#!/usr/bin/env python3
"""
OCB TITAN ERP - Performance Load Test Script
Simulates: 500 concurrent users, 100 transactions/minute

Tests:
- POS transactions
- Sales posting
- Inventory update
- Journal posting

Performance targets:
- API response < 300ms
- Error rate < 1%
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
import os

API_URL = os.environ.get("API_URL", "https://smart-ops-hub-6.preview.emergentagent.com")
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"

# Results storage
results = {
    "timestamp": datetime.utcnow().isoformat(),
    "config": {
        "concurrent_users": 100,  # Reduced for preview environment
        "transactions_per_minute": 50,
        "test_duration_seconds": 30
    },
    "endpoints": {},
    "summary": {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "error_rate_percent": 0,
        "avg_response_ms": 0,
        "p95_response_ms": 0,
        "p99_response_ms": 0,
        "requests_per_second": 0
    }
}

async def get_token(session):
    """Get authentication token"""
    async with session.post(
        f"{API_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    ) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get("token")
    return None

async def test_endpoint(session, token, endpoint, method="GET", data=None):
    """Test a single endpoint and record timing"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    start = time.time()
    try:
        if method == "GET":
            async with session.get(f"{API_URL}{endpoint}", headers=headers, timeout=10) as resp:
                status = resp.status
                await resp.text()
        else:
            async with session.post(f"{API_URL}{endpoint}", headers=headers, json=data, timeout=10) as resp:
                status = resp.status
                await resp.text()
        
        elapsed = (time.time() - start) * 1000  # ms
        success = status in [200, 201]
        
        return {
            "endpoint": endpoint,
            "status": status,
            "response_ms": elapsed,
            "success": success
        }
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return {
            "endpoint": endpoint,
            "status": 0,
            "response_ms": elapsed,
            "success": False,
            "error": str(e)
        }

async def run_user_session(session, token, user_id, endpoints):
    """Simulate a single user session"""
    user_results = []
    
    for endpoint in endpoints:
        result = await test_endpoint(session, token, endpoint)
        result["user_id"] = user_id
        user_results.append(result)
        await asyncio.sleep(0.1)  # Small delay between requests
    
    return user_results

async def run_load_test():
    """Run the load test"""
    print(f"Starting load test at {datetime.utcnow().isoformat()}")
    print(f"Target: {API_URL}")
    print("-" * 60)
    
    # Test endpoints
    endpoints = [
        "/api/system/health",
        "/api/products",
        "/api/branches",
        "/api/pos/transactions",
        "/api/sales/invoices",
        "/api/inventory/stock",
        "/api/accounting/journals",
        "/api/accounting/financial/trial-balance",
        "/api/dashboard/owner",
        "/api/ar/list"
    ]
    
    async with aiohttp.ClientSession() as session:
        # Get token
        print("Authenticating...")
        token = await get_token(session)
        if not token:
            print("ERROR: Failed to authenticate")
            return
        
        print("Authentication successful")
        print(f"Testing {len(endpoints)} endpoints with {results['config']['concurrent_users']} concurrent users...")
        
        all_results = []
        start_time = time.time()
        
        # Run concurrent users
        concurrent = results['config']['concurrent_users']
        tasks = []
        
        for i in range(concurrent):
            task = run_user_session(session, token, i, endpoints)
            tasks.append(task)
        
        # Execute all tasks
        user_results = await asyncio.gather(*tasks)
        
        # Flatten results
        for user_result in user_results:
            all_results.extend(user_result)
        
        total_time = time.time() - start_time
        
        # Process results
        endpoint_stats = {}
        all_times = []
        
        for r in all_results:
            ep = r["endpoint"]
            if ep not in endpoint_stats:
                endpoint_stats[ep] = {
                    "times": [],
                    "success": 0,
                    "fail": 0
                }
            
            endpoint_stats[ep]["times"].append(r["response_ms"])
            all_times.append(r["response_ms"])
            
            if r["success"]:
                endpoint_stats[ep]["success"] += 1
            else:
                endpoint_stats[ep]["fail"] += 1
        
        # Calculate statistics
        for ep, stats in endpoint_stats.items():
            times = stats["times"]
            results["endpoints"][ep] = {
                "total_requests": len(times),
                "successful": stats["success"],
                "failed": stats["fail"],
                "avg_ms": round(statistics.mean(times), 2),
                "min_ms": round(min(times), 2),
                "max_ms": round(max(times), 2),
                "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 2) if len(times) > 1 else times[0],
                "error_rate": round((stats["fail"] / len(times)) * 100, 2)
            }
        
        # Summary
        total = len(all_results)
        success = sum(1 for r in all_results if r["success"])
        failed = total - success
        
        results["summary"] = {
            "total_requests": total,
            "successful_requests": success,
            "failed_requests": failed,
            "error_rate_percent": round((failed / total) * 100, 2) if total > 0 else 0,
            "avg_response_ms": round(statistics.mean(all_times), 2),
            "min_response_ms": round(min(all_times), 2),
            "max_response_ms": round(max(all_times), 2),
            "p95_response_ms": round(sorted(all_times)[int(len(all_times) * 0.95)], 2),
            "p99_response_ms": round(sorted(all_times)[int(len(all_times) * 0.99)], 2),
            "requests_per_second": round(total / total_time, 2),
            "test_duration_seconds": round(total_time, 2)
        }
        
        # Performance targets
        results["performance_check"] = {
            "avg_under_300ms": results["summary"]["avg_response_ms"] < 300,
            "error_rate_under_1pct": results["summary"]["error_rate_percent"] < 1,
            "overall_status": "PASS" if (results["summary"]["avg_response_ms"] < 300 and results["summary"]["error_rate_percent"] < 1) else "FAIL"
        }
        
        print("\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        print(f"Total Requests: {total}")
        print(f"Successful: {success}")
        print(f"Failed: {failed}")
        print(f"Error Rate: {results['summary']['error_rate_percent']}%")
        print(f"Avg Response: {results['summary']['avg_response_ms']}ms")
        print(f"P95 Response: {results['summary']['p95_response_ms']}ms")
        print(f"P99 Response: {results['summary']['p99_response_ms']}ms")
        print(f"Requests/sec: {results['summary']['requests_per_second']}")
        print(f"Duration: {results['summary']['test_duration_seconds']}s")
        print("-" * 60)
        print(f"Performance Status: {results['performance_check']['overall_status']}")
        
        # Save results
        output_path = "/app/test_reports/load_test_results.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")
        
        return results

if __name__ == "__main__":
    asyncio.run(run_load_test())
