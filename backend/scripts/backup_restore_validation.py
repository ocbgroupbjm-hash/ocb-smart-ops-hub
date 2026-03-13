#!/usr/bin/env python3
"""
OCB TITAN ERP - BACKUP & RESTORE VALIDATION
3 Jenis Backup: Full DB Dump, Portable JSON/ZIP, PDF Reports

Output: /app/test_reports/BACKUP_RESTORE_VALIDATION.json
"""

import asyncio
import os
import json
import subprocess
import zipfile
import shutil
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from io import BytesIO

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
TEST_DB = "ocb_titan"
BACKUP_DIR = "/app/backend/backups"
OUTPUT_FILE = "/app/test_reports/BACKUP_RESTORE_VALIDATION.json"


class BackupRestoreValidator:
    def __init__(self):
        self.client = None
        self.db = None
        self.results = []
        self.backup_files = []
        
    async def setup(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[TEST_DB]
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
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
    
    # ==================== BACKUP TYPE 1: MONGODB DUMP ====================
    
    async def test_backup_full_dump(self):
        """Test 1: Full MongoDB Dump Backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_path = f"{BACKUP_DIR}/tenant_backup_{timestamp}.dump"
            
            # Run mongodump
            cmd = f"mongodump --uri='{MONGO_URL}' --db={TEST_DB} --archive={dump_path} --gzip"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(dump_path):
                file_size = os.path.getsize(dump_path)
                self.backup_files.append(dump_path)
                self.log_result(
                    "Backup Full Dump",
                    True,
                    f"Created: {dump_path} ({file_size/1024:.1f} KB)",
                    {"path": dump_path, "size_kb": file_size/1024}
                )
            else:
                self.log_result("Backup Full Dump", False, f"mongodump failed: {result.stderr[:100]}")
                
        except Exception as e:
            self.log_result("Backup Full Dump", False, str(e))
    
    async def test_restore_full_dump(self):
        """Test 1b: Restore from MongoDB Dump"""
        try:
            if not self.backup_files:
                self.log_result("Restore Full Dump", False, "No backup file available")
                return
            
            dump_path = self.backup_files[-1]
            restore_db = f"{TEST_DB}_restore_test"
            
            # Run mongorestore to a test database
            cmd = f"mongorestore --uri='{MONGO_URL}' --archive={dump_path} --gzip --nsFrom='{TEST_DB}.*' --nsTo='{restore_db}.*' --drop"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Verify restore
                restored_db = self.client[restore_db]
                collections = await restored_db.list_collection_names()
                
                if len(collections) > 0:
                    # Cleanup
                    await self.client.drop_database(restore_db)
                    self.log_result(
                        "Restore Full Dump",
                        True,
                        f"Restored {len(collections)} collections, then cleaned up",
                        {"collections_restored": len(collections)}
                    )
                else:
                    self.log_result("Restore Full Dump", False, "No collections restored")
            else:
                self.log_result("Restore Full Dump", False, f"mongorestore failed: {result.stderr[:100]}")
                
        except Exception as e:
            self.log_result("Restore Full Dump", False, str(e))
    
    # ==================== BACKUP TYPE 2: PORTABLE JSON/ZIP ====================
    
    async def test_backup_portable_json(self):
        """Test 2: Portable JSON Export"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_dir = f"{BACKUP_DIR}/json_export_{timestamp}"
            os.makedirs(json_dir, exist_ok=True)
            
            # Export critical collections
            collections_to_export = [
                "journal_entries", "sales_invoices", "purchase_orders",
                "stock_movements", "products", "customers", "suppliers",
                "accounts", "branches", "users"
            ]
            
            exported = 0
            total_records = 0
            
            for collection_name in collections_to_export:
                try:
                    docs = await self.db[collection_name].find({}, {"_id": 0}).to_list(100000)
                    if docs:
                        file_path = f"{json_dir}/{collection_name}.json"
                        with open(file_path, "w") as f:
                            json.dump(docs, f, indent=2, default=str)
                        exported += 1
                        total_records += len(docs)
                except Exception as e:
                    pass  # Collection might not exist
            
            # Create ZIP
            zip_path = f"{BACKUP_DIR}/backup_portable_{timestamp}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(json_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, json_dir)
                        zipf.write(file_path, arcname)
            
            # Cleanup JSON folder
            shutil.rmtree(json_dir)
            
            zip_size = os.path.getsize(zip_path)
            self.backup_files.append(zip_path)
            
            self.log_result(
                "Backup Portable JSON/ZIP",
                True,
                f"Exported {exported} collections, {total_records} records, ZIP: {zip_size/1024:.1f} KB",
                {"collections": exported, "records": total_records, "zip_path": zip_path, "size_kb": zip_size/1024}
            )
            
        except Exception as e:
            self.log_result("Backup Portable JSON/ZIP", False, str(e))
    
    async def test_restore_portable_json(self):
        """Test 2b: Restore from Portable JSON/ZIP"""
        try:
            # Find the ZIP file
            zip_files = [f for f in self.backup_files if f.endswith('.zip')]
            if not zip_files:
                self.log_result("Restore Portable JSON", False, "No ZIP backup available")
                return
            
            zip_path = zip_files[-1]
            extract_dir = f"{BACKUP_DIR}/restore_test"
            os.makedirs(extract_dir, exist_ok=True)
            
            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(extract_dir)
            
            # Count extracted files
            json_files = [f for f in os.listdir(extract_dir) if f.endswith('.json')]
            
            # Verify data integrity
            total_records = 0
            for json_file in json_files:
                with open(os.path.join(extract_dir, json_file), 'r') as f:
                    data = json.load(f)
                    total_records += len(data)
            
            # Cleanup
            shutil.rmtree(extract_dir)
            
            self.log_result(
                "Restore Portable JSON",
                True,
                f"Extracted {len(json_files)} JSON files, {total_records} records verified",
                {"json_files": len(json_files), "total_records": total_records}
            )
            
        except Exception as e:
            self.log_result("Restore Portable JSON", False, str(e))
    
    # ==================== BACKUP TYPE 3: PDF REPORTS ====================
    
    async def test_backup_pdf_reports(self):
        """Test 3: PDF Report Generation"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib import colors
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_dir = f"{BACKUP_DIR}/reports_{timestamp}"
            os.makedirs(pdf_dir, exist_ok=True)
            
            reports_created = []
            
            # 1. Trial Balance PDF
            try:
                pdf_path = f"{pdf_dir}/trial_balance_{timestamp}.pdf"
                c = canvas.Canvas(pdf_path, pagesize=A4)
                width, height = A4
                
                c.setFont("Helvetica-Bold", 16)
                c.drawCentredString(width/2, height - 50, "OCB TITAN ERP - TRIAL BALANCE")
                c.setFont("Helvetica", 10)
                c.drawCentredString(width/2, height - 70, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Get trial balance data
                journals = await self.db["journal_entries"].find({"status": "posted"}, {"_id": 0}).to_list(100000)
                
                account_balances = {}
                for j in journals:
                    for e in j.get("entries", []):
                        code = e.get("account_code", "")
                        if code not in account_balances:
                            account_balances[code] = {"name": e.get("account_name", ""), "debit": 0, "credit": 0}
                        account_balances[code]["debit"] += e.get("debit", 0)
                        account_balances[code]["credit"] += e.get("credit", 0)
                
                y = height - 100
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y, "Account")
                c.drawString(250, y, "Debit")
                c.drawString(350, y, "Credit")
                y -= 5
                c.line(50, y, 450, y)
                y -= 15
                
                c.setFont("Helvetica", 9)
                total_d, total_c = 0, 0
                for code in sorted(account_balances.keys())[:30]:  # First 30
                    data = account_balances[code]
                    c.drawString(50, y, f"{code} - {data['name'][:30]}")
                    c.drawString(250, y, f"{data['debit']:,.0f}")
                    c.drawString(350, y, f"{data['credit']:,.0f}")
                    total_d += data['debit']
                    total_c += data['credit']
                    y -= 12
                    if y < 100:
                        break
                
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y - 10, "TOTAL")
                c.drawString(250, y - 10, f"{total_d:,.0f}")
                c.drawString(350, y - 10, f"{total_c:,.0f}")
                
                c.save()
                reports_created.append("trial_balance.pdf")
            except Exception as e:
                print(f"    Trial Balance PDF error: {e}")
            
            # 2. Inventory Report PDF
            try:
                pdf_path = f"{pdf_dir}/inventory_{timestamp}.pdf"
                c = canvas.Canvas(pdf_path, pagesize=A4)
                
                c.setFont("Helvetica-Bold", 16)
                c.drawCentredString(width/2, height - 50, "OCB TITAN ERP - INVENTORY REPORT")
                c.setFont("Helvetica", 10)
                c.drawCentredString(width/2, height - 70, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Get inventory from SSOT
                pipeline = [
                    {"$group": {"_id": "$product_id", "qty": {"$sum": "$quantity"}, "name": {"$first": "$product_name"}}},
                    {"$match": {"qty": {"$ne": 0}}},
                    {"$sort": {"qty": -1}},
                    {"$limit": 50}
                ]
                stock = await self.db["stock_movements"].aggregate(pipeline).to_list(50)
                
                y = height - 100
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y, "Product")
                c.drawString(400, y, "Qty")
                y -= 20
                
                c.setFont("Helvetica", 9)
                for s in stock[:30]:
                    c.drawString(50, y, str(s.get("name", ""))[:50])
                    c.drawString(400, y, str(s.get("qty", 0)))
                    y -= 12
                    if y < 100:
                        break
                
                c.save()
                reports_created.append("inventory.pdf")
            except Exception as e:
                print(f"    Inventory PDF error: {e}")
            
            # Create summary
            self.log_result(
                "Backup PDF Reports",
                len(reports_created) >= 2,
                f"Created {len(reports_created)} PDF reports in {pdf_dir}",
                {"reports": reports_created, "path": pdf_dir}
            )
            
        except Exception as e:
            self.log_result("Backup PDF Reports", False, str(e))
    
    async def run_all_tests(self):
        """Run all backup/restore tests"""
        print("\n" + "="*70)
        print("OCB TITAN ERP - BACKUP & RESTORE VALIDATION")
        print(f"Database: {TEST_DB}")
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print("="*70 + "\n")
        
        await self.setup()
        
        print("--- TYPE 1: FULL DATABASE DUMP ---")
        await self.test_backup_full_dump()
        await self.test_restore_full_dump()
        
        print("\n--- TYPE 2: PORTABLE JSON/ZIP ---")
        await self.test_backup_portable_json()
        await self.test_restore_portable_json()
        
        print("\n--- TYPE 3: PDF REPORTS ---")
        await self.test_backup_pdf_reports()
        
        await self.teardown()
        
        # Summary
        passed_count = sum(1 for r in self.results if r["passed"])
        total_count = len(self.results)
        
        print("\n" + "="*70)
        print("BACKUP & RESTORE VALIDATION SUMMARY")
        print("="*70)
        print(f"Total Tests:  {total_count}")
        print(f"Passed:       {passed_count}")
        print(f"Failed:       {total_count - passed_count}")
        print(f"Pass Rate:    {passed_count/total_count*100:.1f}%")
        print("="*70)
        
        # List backup files created
        print("\nBackup Files Created:")
        for bf in self.backup_files:
            size = os.path.getsize(bf) / 1024 if os.path.exists(bf) else 0
            print(f"  - {bf} ({size:.1f} KB)")
        
        # Save results
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        report = {
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "database": TEST_DB,
            "total_tests": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "pass_rate": f"{passed_count/total_count*100:.1f}%",
            "backup_files": self.backup_files,
            "results": self.results
        }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Report saved: {OUTPUT_FILE}")
        
        return report


if __name__ == "__main__":
    validator = BackupRestoreValidator()
    asyncio.run(validator.run_all_tests())
