#!/usr/bin/env python3
"""
Burst Test - Create burst loads to test system resilience
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
    
    # Add some patterns
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    for i in range(0, width, 100):
        draw.line([(i, 0), (i, height)], fill=(255, 255, 255), width=2)
    for i in range(0, height, 100):
        draw.line([(0, i), (width, i)], fill=(255, 255, 255), width=2)
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=85)
    img_bytes.seek(0)
    return img_bytes.getvalue()


async def upload_image(session, api_url, image_data, burst_id, image_id):
    """Upload a single image"""
    start_time = time.time()
    
    try:
        data = aiohttp.FormData()
        data.add_field('file',
                      image_data,
                      filename=f'burst{burst_id}_image_{image_id}.jpg',
                      content_type='image/jpeg')
        data.add_field('operations', 'resize,watermark')
        
        async with session.post(f"{api_url}/upload", data=data) as response:
            if response.status == 200:
                result = await response.json()
                elapsed = time.time() - start_time
                return {
                    "success": True,
                    "job_id": result.get("job_id"),
                    "elapsed": elapsed,
                    "burst_id": burst_id,
                    "image_id": image_id
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status}",
                    "elapsed": time.time() - start_time,
                    "burst_id": burst_id,
                    "image_id": image_id
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "elapsed": time.time() - start_time,
            "burst_id": burst_id,
            "image_id": image_id
        }


async def send_burst(session, api_url, image_data, burst_id, burst_size):
    """Send a burst of uploads"""
    print(f"\n[Burst {burst_id}] Sending {burst_size} images...")
    start_time = time.time()
    
    tasks = [upload_image(session, api_url, image_data, burst_id, i) for i in range(burst_size)]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    successful = sum(1 for r in results if r["success"])
    
    print(f"[Burst {burst_id}] Completed in {elapsed:.2f}s - {successful}/{burst_size} successful")
    
    return results


async def burst_test(api_url, burst_size, burst_count, interval):
    """Run burst test"""
    print(f"\nBurst Load Test")
    print(f"=" * 60)
    print(f"API URL: {api_url}")
    print(f"Burst size: {burst_size} images")
    print(f"Number of bursts: {burst_count}")
    print(f"Interval between bursts: {interval}s")
    print(f"=" * 60)
    
    # Create test image
    print("\nCreating test image...")
    image_data = await create_test_image()
    print(f"Test image size: {len(image_data) / 1024:.2f} KB")
    
    all_results = []
    burst_timings = []
    
    async with aiohttp.ClientSession() as session:
        for burst_id in range(burst_count):
            burst_start = time.time()
            
            # Send burst
            results = await send_burst(session, api_url, image_data, burst_id, burst_size)
            all_results.extend(results)
            
            burst_time = time.time() - burst_start
            burst_timings.append(burst_time)
            
            # Wait before next burst (except for last one)
            if burst_id < burst_count - 1:
                print(f"Waiting {interval}s before next burst...")
                await asyncio.sleep(interval)
    
    # Analyze results
    successful = [r for r in all_results if r["success"]]
    failed = [r for r in all_results if not r["success"]]
    
    upload_times = [r["elapsed"] for r in all_results]
    
    print(f"\n{'=' * 60}")
    print("Overall Results:")
    print(f"{'=' * 60}")
    print(f"Total bursts: {burst_count}")
    print(f"Total images: {len(all_results)}")
    print(f"Successful uploads: {len(successful)}")
    print(f"Failed uploads: {len(failed)}")
    print(f"\nBurst Timing:")
    print(f"  Mean burst time: {statistics.mean(burst_timings):.2f}s")
    print(f"  Min burst time: {min(burst_timings):.2f}s")
    print(f"  Max burst time: {max(burst_timings):.2f}s")
    print(f"\nUpload Latency:")
    print(f"  Mean: {statistics.mean(upload_times):.3f}s")
    print(f"  Median: {statistics.median(upload_times):.3f}s")
    print(f"  Min: {min(upload_times):.3f}s")
    print(f"  Max: {max(upload_times):.3f}s")
    
    if len(upload_times) > 1:
        print(f"  StdDev: {statistics.stdev(upload_times):.3f}s")
    
    # Save results
    results_file = f"burst_test_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "config": {
                "api_url": api_url,
                "burst_size": burst_size,
                "burst_count": burst_count,
                "interval": interval
            },
            "summary": {
                "total_images": len(all_results),
                "successful": len(successful),
                "failed": len(failed),
                "burst_timings": burst_timings,
                "latency": {
                    "mean": statistics.mean(upload_times),
                    "median": statistics.median(upload_times),
                    "min": min(upload_times),
                    "max": max(upload_times),
                    "stdev": statistics.stdev(upload_times) if len(upload_times) > 1 else 0
                }
            },
            "results": all_results
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(description="Burst load test")
    parser.add_argument("--burst-size", type=int, default=50, help="Images per burst")
    parser.add_argument("--burst-count", type=int, default=3, help="Number of bursts")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between bursts")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    
    args = parser.parse_args()
    
    asyncio.run(burst_test(args.api_url, args.burst_size, args.burst_count, args.interval))


if __name__ == "__main__":
    main()
