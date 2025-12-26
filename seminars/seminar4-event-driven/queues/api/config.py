import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # RabbitMQ
    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user: str = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_pass: str = os.getenv("RABBITMQ_PASS", "guest")
    
    # MinIO
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    # Queues
    task_queue: str = "image_processing"
    notification_queue: str = "notifications"
    dlq_queue: str = "dead_letter_queue"
    
    # Buckets
    upload_bucket: str = "images"
    processed_bucket: str = "processed"


settings = Settings()
