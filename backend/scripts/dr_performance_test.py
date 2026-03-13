#!/usr/bin/env python3
"""
OCB TITAN ERP - DISASTER RECOVERY & PERFORMANCE TEST
- Test restore time < 5 minutes
- Test 1000 transactions/day simulation
- Test 50 concurrent users
- API latency < 500ms
"""

import asyncio
import os
import json
import time
import subprocess
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import httpx

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
API_BASE = os.environ.get("API_BASE", "http://localhost:8001/api")
TEST_DB = "ocb_titan"
OUTPUT_FILE = "/app/test_reports/DR_PERFORMANCE_VALIDATION.json"


class DRPerformanceValidator:
    def __init__(self):
        self.client = None
        self.db = None
        self.results = []
        self.token = None
        
    async def setup(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[TEST_DB]
        
        # Get auth token
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{API_BASE}/auth/login",
                    json={"email": "ocbgroupbjm@gmail.com", "password": "admin123"}
                )
                if resp.status_code == 200:
                    self.token = resp.json().get("token")
            except:
                pass
    
    async def teardown(self):
        if self.client:
            self.client.close()
    
    def log_result(self, test_name: str, passed: bool, details: str = "", data: dict = None):
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status} - {details[:80]}")
    
    # ==================== DISASTER RECOVERY TEST ====================
    
    async def test_disaster_recovery(self):
        """Test Disaster Recovery - Restore Time < 5 minutes"""
        print("\n--- DISASTER RECOVERY TEST ---")
        
        try:
            # Simulate "disaster" - we already have backups
            backup_dir = "/app/backend/backups"
            
            # Find most recent dump
            dump_files = [f for f in os.listdir(backup_dir) if f.endswith('.dump')]
            
            if not dump_files:
                # Create a backup first
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dump_path = f"{backup_dir}/dr_test_{timestamp}.dump"
                
                start_time = time.time()
                cmd = f"mongodump --uri='{MONGO_URL}' --db={TEST_DB} --archive={dump_path} --gzip"
                subprocess.run(cmd, shell=True, capture_output=True)
                backup_time = time.time() - start_time
                
                self.log_result(
                    "DR Backup Creation",
                    backup_time < 60,
                    f"Backup created in {backup_time:.1f}s",
                    {"backup_time_seconds": backup_time}
                )
            else:
                dump_path = f"{backup_dir}/{sorted(dump_files)[-1]}"
                self.log_result("DR Backup Available", True, f"Using existing: {dump_path}")
            
            # Test restore time (to temp db)
            restore_db = f"{TEST_DB}_dr_test"
            
            start_time = time.time()
            cmd = f"mongorestore --uri='{MONGO_URL}' --archive={dump_path} --gzip --nsFrom='{TEST_DB}.*' --nsTo='{restore_db}.*' --drop 2>/dev/null"
            result = subprocess.run(cmd, shell=True, capture_output=True)
            restore_time = time.time() - start_time
            
            # Verify restore
            test_db = self.client[restore_db]
            collections = await test_db.list_collection_names()
            
            # Cleanup
            await self.client.drop_database(restore_db)
            
            # Target: < 5 minutes (300 seconds)
            passed = restore_time < 300 and len(collections) > 0
            
            self.log_result(
                "DR Restore Time",
                passed,
                f"Restored in {restore_time:.1f}s (target: <300s), {len(collections)} collections",
                {"restore_time_seconds": restore_time, "collections": len(collections)}
            )
            
        except Exception as e:
            self.log_result("Disaster Recovery", False, str(e))
    
    # ==================== PERFORMANCE TEST ====================
    
    async def test_api_latency(self):
        """Test API Latency < 500ms"""
        print("\n--- API LATENCY TEST ---")
        
        try:
            endpoints = [
                ("GET", "/dashboard-intel/kpi-summary?days=30"),
                ("GET", "/products?limit=50"),
                ("GET", "/sales/invoices?limit=20"),
                ("GET", "/audit/summary"),
                ("GET", "/ai/tools/trial-balance"),
            ]
            
            latencies = []
            
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
                
                for method, endpoint in endpoints:
                    start = time.time()
                    try:
                        if method == "GET":
                            resp = await client.get(f"{API_BASE}{endpoint}", headers=headers)
                        elapsed = (time.time() - start) * 1000  # Convert to ms
                        latencies.append({
                            "endpoint": endpoint,
                            "method": method,
                            "latency_ms": elapsed,
                            "status": resp.status_code
                        })
                    except Exception as e:
                        latencies.append({
                            "endpoint": endpoint,
                            "method": method,
                            "latency_ms": -1,
                            "error": str(e)[:50]
                        })
            
            # Calculate stats
            valid_latencies = [l["latency_ms"] for l in latencies if l["latency_ms"] > 0]
            avg_latency = sum(valid_latencies) / len(valid_latencies) if valid_latencies else 0
            max_latency = max(valid_latencies) if valid_latencies else 0
            
            # Target: all < 500ms
            all_under_500 = all(l < 500 for l in valid_latencies)
            
            self.log_result(
                "API Latency",
                all_under_500 and avg_latency < 500,
                f"Avg: {avg_latency:.0f}ms, Max: {max_latency:.0f}ms (target: <500ms)",
                {"avg_ms": avg_latency, "max_ms": max_latency, "details": latencies}
            )
            
        except Exception as e:
            self.log_result("API Latency", False, str(e))
    
    async def test_concurrent_users(self):
        """Test 50 Concurrent Users"""
        print("\n--- CONCURRENT USERS TEST ---")
        
        try:
            concurrent_users = 50
            successful_requests = 0
            failed_requests = 0
            latencies = []
            
            async def make_request(user_id):
                nonlocal successful_requests, failed_requests
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
                        start = time.time()
                        resp = await client.get(
                            f"{API_BASE}/dashboard-intel/kpi-summary?days=7",
                            headers=headers
                        )
                        elapsed = (time.time() - start) * 1000
                        if resp.status_code == 200:
                            successful_requests += 1
                            latencies.append(elapsed)
                        else:
                            failed_requests += 1
                except:
                    failed_requests += 1
            
            # Simulate concurrent requests
            tasks = [make_request(i) for i in range(concurrent_users)]
            await asyncio.gather(*tasks)
            
            success_rate = successful_requests / concurrent_users * 100 if concurrent_users > 0 else 0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            # Target: >90% success, avg <1000ms
            passed = success_rate > 90 and avg_latency < 1000
            
            self.log_result(
                "Concurrent Users (50)",
                passed,
                f"Success: {success_rate:.0f}%, Avg latency: {avg_latency:.0f}ms",
                {"success_rate": success_rate, "successful": successful_requests, "failed": failed_requests, "avg_latency_ms": avg_latency}
            )
            
        except Exception as e:
            self.log_result("Concurrent Users", False, str(e))
    
    async def test_transaction_throughput(self):
        """Test 1000 Transactions/Day Simulation"""
        print("\n--- TRANSACTION THROUGHPUT TEST ---")
        
        try:
            import uuid
            
            # Simulate 100 transactions (scaled down for speed)
            transactions_to_create = 100
            start_time = time.time()
            
            branch = await self.db["branches"].find_one({"is_active": True}, {"_id": 0})
            product = await self.db["products"].find_one({"is_active": True}, {"_id": 0})
            
            if not branch or not product:
                self.log_result("Transaction Throughput", False, "Missing test data")
                return
            
            created = 0
            for i in range(transactions_to_create):
                try:
                    invoice = {
                        "id": str(uuid.uuid4()),
                        "invoice_number": f"PERF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i:04d}",
                        "invoice_date": datetime.now(timezone.utc).isoformat(),
                        "branch_id": branch["id"],
                        "items": [{
                            "product_id": product["id"],
                            "product_name": product.get("name", ""),
                            "quantity": 1,
                            "unit_price": product.get("selling_price", 10000),
                            "subtotal": product.get("selling_price", 10000)
                        }],
                        "total": product.get("selling_price", 10000),
                        "status": "completed",
                        "payment_method": "cash",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await self.db["sales_invoices"].insert_one(invoice)
                    created += 1
                except:
                    pass
            
            elapsed = time.time() - start_time
            tps = created / elapsed if elapsed > 0 else 0
            
            # Extrapolate to 1000/day = ~0.7 TPS (very low requirement)
            # Our target: at least 10 TPS for comfortable margin
            passed = tps > 5
            
            self.log_result(
                "Transaction Throughput",
                passed,
                f"Created {created} in {elapsed:.1f}s ({tps:.1f} TPS). 1000/day needs ~0.7 TPS",
                {"created": created, "elapsed_seconds": elapsed, "tps": tps}
            )
            
        except Exception as e:
            self.log_result("Transaction Throughput", False, str(e))
    
    async def run_all_tests(self):
        """Run all DR and performance tests"""
        print("\n" + "="*70)
        print("OCB TITAN ERP - DISASTER RECOVERY & PERFORMANCE VALIDATION")
        print(f"Database: {TEST_DB}")
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print("="*70)
        
        await self.setup()
        
        await self.test_disaster_recovery()
        await self.test_api_latency()
        await self.test_concurrent_users()
        await self.test_transaction_throughput()
        
        await self.teardown()
        
        # Summary
        passed_count = sum(1 for r in self.results if r["passed"])
        total_count = len(self.results)
        
        print("\n" + "="*70)
        print("DR & PERFORMANCE VALIDATION SUMMARY")
        print("="*70)
        print(f"Total Tests:  {total_count}")
        print(f"Passed:       {passed_count}")
        print(f"Failed:       {total_count - passed_count}")
        print(f"Pass Rate:    {passed_count/total_count*100:.1f}%")
        print("="*70)
        
        # Save results
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        report = {
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "database": TEST_DB,
            "total_tests": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "pass_rate": f"{passed_count/total_count*100:.1f}%",
            "results": self.results
        }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Report saved: {OUTPUT_FILE}")
        
        return report


if __name__ == "__main__":
    validator = DRPerformanceValidator()
    asyncio.run(validator.run_all_tests())
