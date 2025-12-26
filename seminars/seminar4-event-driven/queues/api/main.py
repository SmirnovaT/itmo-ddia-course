import json
import time
import uuid
from datetime import datetime
from typing import List, Optional
from io import BytesIO

import pika
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from minio import Minio
from minio.error import S3Error

from config import settings

app = FastAPI(title="Image Processing API")

# Job status storage (in production, use Redis or database)
job_storage = {}

# RabbitMQ connection
def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_pass)
    parameters = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    return pika.BlockingConnection(parameters)

# MinIO client
minio_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure
)


@app.on_event("startup")
async def startup_event():
    """Initialize queues and buckets on startup"""
    # Ensure buckets exist
    try:
        if not minio_client.bucket_exists(settings.upload_bucket):
            minio_client.make_bucket(settings.upload_bucket)
        if not minio_client.bucket_exists(settings.processed_bucket):
            minio_client.make_bucket(settings.processed_bucket)
    except S3Error as e:
        print(f"MinIO error: {e}")
    
    # Declare queues
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Declare main queue with DLQ
        channel.queue_declare(queue=settings.dlq_queue, durable=True)
        channel.queue_declare(
            queue=settings.task_queue,
            durable=True,
            arguments={
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': settings.dlq_queue
            }
        )
        channel.queue_declare(queue=settings.notification_queue, durable=True)
        
        connection.close()
    except Exception as e:
        print(f"RabbitMQ error: {e}")


@app.get("/")
async def root():
    return {
        "service": "Image Processing API",
        "version": "1.0",
        "endpoints": {
            "upload": "/upload",
            "status": "/status/{job_id}",
            "metrics": "/metrics",
            "dlq": "/dlq/stats"
        }
    }


@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    operations: str = Form(default="resize")
):
    """
    Upload an image and queue it for processing
    
    operations: comma-separated list (resize, watermark, filter)
    """
    # Validate file
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Parse operations
    ops_list = [op.strip() for op in operations.split(",")]
    valid_ops = ["resize", "watermark", "filter"]
    ops_list = [op for op in ops_list if op in valid_ops]
    
    if not ops_list:
        raise HTTPException(status_code=400, detail=f"Invalid operations. Valid: {valid_ops}")
    
    try:
        # Upload to MinIO
        file_content = await file.read()
        file_name = f"{job_id}_{file.filename}"
        
        minio_client.put_object(
            settings.upload_bucket,
            file_name,
            BytesIO(file_content),
            length=len(file_content),
            content_type=file.content_type
        )
        
        # Create job message
        job_message = {
            "job_id": job_id,
            "file_name": file_name,
            "original_name": file.filename,
            "operations": ops_list,
            "timestamp": timestamp,
            "bucket": settings.upload_bucket
        }
        
        # Publish to RabbitMQ
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        channel.basic_publish(
            exchange='',
            routing_key=settings.task_queue,
            body=json.dumps(job_message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type='application/json'
            )
        )
        
        connection.close()
        
        # Store job status
        job_storage[job_id] = {
            "status": "queued",
            "operations": ops_list,
            "timestamp": timestamp,
            "file_name": file_name
        }
        
        return {
            "job_id": job_id,
            "status": "queued",
            "operations": ops_list,
            "message": "Image uploaded and queued for processing"
        }
        
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a processing job"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_storage[job_id]


@app.get("/metrics")
async def get_metrics():
    """Get queue metrics"""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Get queue stats
        task_queue = channel.queue_declare(queue=settings.task_queue, passive=True)
        notification_queue = channel.queue_declare(queue=settings.notification_queue, passive=True)
        dlq_queue = channel.queue_declare(queue=settings.dlq_queue, passive=True)
        
        connection.close()
        
        # Count jobs by status
        status_counts = {}
        for job in job_storage.values():
            status = job.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "queues": {
                "task_queue": {
                    "name": settings.task_queue,
                    "messages": task_queue.method.message_count
                },
                "notification_queue": {
                    "name": settings.notification_queue,
                    "messages": notification_queue.method.message_count
                },
                "dlq": {
                    "name": settings.dlq_queue,
                    "messages": dlq_queue.method.message_count
                }
            },
            "jobs": {
                "total": len(job_storage),
                "by_status": status_counts
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")


@app.get("/dlq/stats")
async def get_dlq_stats():
    """Get Dead Letter Queue statistics"""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        dlq_queue = channel.queue_declare(queue=settings.dlq_queue, passive=True)
        message_count = dlq_queue.method.message_count
        
        connection.close()
        
        return {
            "dlq": settings.dlq_queue,
            "failed_messages": message_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/jobs/update")
async def update_job_status(job_id: str, status: str, result: Optional[dict] = None):
    """Internal endpoint for workers to update job status"""
    if job_id in job_storage:
        job_storage[job_id]["status"] = status
        job_storage[job_id]["updated_at"] = datetime.now().isoformat()
        
        if result:
            job_storage[job_id]["result"] = result
        
        return {"message": "Status updated"}
    
    raise HTTPException(status_code=404, detail="Job not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
