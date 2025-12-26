#!/usr/bin/env python3
"""
Analyze results from load tests
"""
import argparse
import json
import glob
from pathlib import Path
import statistics


def load_results(pattern):
    """Load all result files matching pattern"""
    files = glob.glob(pattern)
    
    if not files:
        print(f"No files found matching: {pattern}")
        return []
    
    results = []
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                results.append({
                    "file": file_path,
                    "data": data
                })
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return results


def analyze_bulk_uploads(results):
    """Analyze bulk upload results"""
    print("\n" + "="*80)
    print("Bulk Upload Analysis")
    print("="*80)
    
    for result in results:
        file_name = result["file"]
        data = result["data"]
        config = data["config"]
        summary = data["summary"]
        
        print(f"\nFile: {file_name}")
        print(f"Configuration:")
        print(f"  Images: {config['count']}")
        print(f"  Operations: {config['operations']}")
        print(f"  Concurrency: {config['concurrency']}")
        
        print(f"\nResults:")
        print(f"  Total time: {summary['total_time']:.2f}s")
        print(f"  Successful: {summary['successful']}/{config['count']}")
        print(f"  Throughput: {summary['throughput']:.2f} uploads/s")
        
        latency = summary['latency']
        print(f"\nLatency:")
        print(f"  Mean: {latency['mean']:.3f}s")
        print(f"  Median: {latency['median']:.3f}s")
        print(f"  Min: {latency['min']:.3f}s")
        print(f"  Max: {latency['max']:.3f}s")
        print(f"  StdDev: {latency['stdev']:.3f}s")


def analyze_burst_tests(results):
    """Analyze burst test results"""
    print("\n" + "="*80)
    print("Burst Test Analysis")
    print("="*80)
    
    for result in results:
        file_name = result["file"]
        data = result["data"]
        config = data["config"]
        summary = data["summary"]
        
        print(f"\nFile: {file_name}")
        print(f"Configuration:")
        print(f"  Burst size: {config['burst_size']}")
        print(f"  Burst count: {config['burst_count']}")
        print(f"  Interval: {config['interval']}s")
        
        print(f"\nResults:")
        print(f"  Total images: {summary['total_images']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Failed: {summary['failed']}")
        
        burst_timings = summary['burst_timings']
        print(f"\nBurst Timing:")
        print(f"  Mean: {statistics.mean(burst_timings):.2f}s")
        print(f"  Min: {min(burst_timings):.2f}s")
        print(f"  Max: {max(burst_timings):.2f}s")
        
        latency = summary['latency']
        print(f"\nLatency:")
        print(f"  Mean: {latency['mean']:.3f}s")
        print(f"  Median: {latency['median']:.3f}s")
        print(f"  Min: {latency['min']:.3f}s")
        print(f"  Max: {latency['max']:.3f}s")


def compare_results(results):
    """Compare multiple test results"""
    if len(results) < 2:
        print("\nNeed at least 2 results to compare")
        return
    
    print("\n" + "="*80)
    print("Comparison")
    print("="*80)
    
    throughputs = []
    mean_latencies = []
    
    for result in results:
        data = result["data"]
        summary = data["summary"]
        
        if "throughput" in summary:
            throughputs.append({
                "file": result["file"],
                "throughput": summary["throughput"],
                "config": data["config"]
            })
        
        mean_latencies.append({
            "file": result["file"],
            "latency": summary["latency"]["mean"],
            "config": data["config"]
        })
    
    if throughputs:
        print("\nThroughput comparison:")
        sorted_throughputs = sorted(throughputs, key=lambda x: x["throughput"], reverse=True)
        for i, item in enumerate(sorted_throughputs, 1):
            print(f"  {i}. {item['throughput']:.2f} uploads/s - {Path(item['file']).name}")
            if "concurrency" in item["config"]:
                print(f"     Concurrency: {item['config']['concurrency']}")
    
    print("\nMean latency comparison:")
    sorted_latencies = sorted(mean_latencies, key=lambda x: x["latency"])
    for i, item in enumerate(sorted_latencies, 1):
        print(f"  {i}. {item['latency']:.3f}s - {Path(item['file']).name}")


def main():
    parser = argparse.ArgumentParser(description="Analyze load test results")
    parser.add_argument("--pattern", default="*_results_*.json", help="File pattern to match")
    parser.add_argument("--type", choices=["bulk", "burst", "all"], default="all", 
                       help="Type of tests to analyze")
    
    args = parser.parse_args()
    
    results = load_results(args.pattern)
    
    if not results:
        return
    
    print(f"\nFound {len(results)} result file(s)")
    
    if args.type in ["bulk", "all"]:
        bulk_results = [r for r in results if "bulk_upload" in r["file"]]
        if bulk_results:
            analyze_bulk_uploads(bulk_results)
    
    if args.type in ["burst", "all"]:
        burst_results = [r for r in results if "burst_test" in r["file"]]
        if burst_results:
            analyze_burst_tests(burst_results)
    
    # Compare if multiple results
    if len(results) > 1:
        compare_results(results)
    
    print("\n")


if __name__ == "__main__":
    main()
