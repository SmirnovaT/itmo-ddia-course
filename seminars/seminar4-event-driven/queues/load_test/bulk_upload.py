#!/usr/bin/env python3
"""
Bulk Upload Test - Upload multiple images concurrently
"""
import argparse
import asyncio
import time
from pathlib import Path
import statistics
import json

import aiohttp
from PIL import Image
import io


async def create_test_image(width=1920, height=1080):
    """Create a test image"""
    img = Image.new('RGB', (width, height), color=(73, 109, 137))
    
    # Add some content to make it more realistic
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    for i in range(0, width, 100):
        draw.line([(i, 0), (i, height)], fill=(255, 255, 255), width=2)
    for i in range(0, height, 100):
        draw.line([(0, i), (width, i)], fill=(255, 255, 255), width=2)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=85)
    img_bytes.seek(0)
    return img_bytes.getvalue()


async def upload_image(session, api_url, image_data, image_id, operations="resize,watermark"):
    """Upload a single image"""
    start_time = time.time()
    
    try:
        data = aiohttp.FormData()
        data.add_field('file',
                      image_data,
                      filename=f'test_image_{image_id}.jpg',
                      content_type='image/jpeg')
        data.add_field('operations', operations)
        
        async with session.post(f"{api_url}/upload", data=data) as response:
            if response.status == 200:
                result = await response.json()
                elapsed = time.time() - start_time
                return {
                    "success": True,
                    "job_id": result.get("job_id"),
                    "elapsed": elapsed,
                    "image_id": image_id
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status}",
                    "elapsed": time.time() - start_time,
                    "image_id": image_id
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "elapsed": time.time() - start_time,
            "image_id": image_id
        }


async def bulk_upload(api_url, count, operations="resize,watermark", concurrency=10):
    """Upload multiple images concurrently"""
    print(f"\nBulk Upload Test")
    print(f"=" * 60)
    print(f"API URL: {api_url}")
    print(f"Images to upload: {count}")
    print(f"Operations: {operations}")
    print(f"Concurrency: {concurrency}")
    print(f"=" * 60)
    
    # Create test image
    print("\nCreating test image...")
    image_data = await create_test_image()
    print(f"Test image size: {len(image_data) / 1024:.2f} KB")
    
    # Upload images
    print(f"\nUploading {count} images...")
    start_time = time.time()
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def upload_with_semaphore(image_id):
            async with semaphore:
                return await upload_image(session, api_url, image_data, image_id, operations)
        
        # Upload all images
        tasks = [upload_with_semaphore(i) for i in range(count)]
        results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    upload_times = [r["elapsed"] for r in results]
    
    print(f"\n{'=' * 60}")
    print("Results:")
    print(f"{'=' * 60}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Successful uploads: {len(successful)}/{count}")
    print(f"Failed uploads: {len(failed)}")
    print(f"\nThroughput: {count / total_time:.2f} uploads/second")
    print(f"\nUpload Latency:")
    print(f"  Mean: {statistics.mean(upload_times):.3f}s")
    print(f"  Median: {statistics.median(upload_times):.3f}s")
    print(f"  Min: {min(upload_times):.3f}s")
    print(f"  Max: {max(upload_times):.3f}s")
    
    if len(upload_times) > 1:
        print(f"  StdDev: {statistics.stdev(upload_times):.3f}s")
    
    if failed:
        print(f"\nFailed uploads:")
        for f in failed[:10]:  # Show first 10 failures
            print(f"  Image {f['image_id']}: {f['error']}")
    
    # Save results to file
    results_file = f"bulk_upload_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "config": {
                "api_url": api_url,
                "count": count,
                "operations": operations,
                "concurrency": concurrency
            },
            "summary": {
                "total_time": total_time,
                "successful": len(successful),
                "failed": len(failed),
                "throughput": count / total_time,
                "latency": {
                    "mean": statistics.mean(upload_times),
                    "median": statistics.median(upload_times),
                    "min": min(upload_times),
                    "max": max(upload_times),
                    "stdev": statistics.stdev(upload_times) if len(upload_times) > 1 else 0
                }
            },
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(description="Bulk image upload test")
    parser.add_argument("--count", type=int, default=100, help="Number of images to upload")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    parser.add_argument("--operations", default="resize,watermark", help="Operations to perform")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent uploads")
    
    args = parser.parse_args()
    
    asyncio.run(bulk_upload(args.api_url, args.count, args.operations, args.concurrency))


if __name__ == "__main__":
    main()
