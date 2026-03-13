#!/usr/bin/env python3
"""
OCB TITAN ERP - POST-RESTORE VALIDATION
MASTER BLUEPRINT: validate_restore.py

Setelah restore selesai, sistem WAJIB menjalankan validation script.

Validasi:
1. tenant_registry valid
2. users valid
3. journal_entries valid
4. stock_movements valid
5. Trial Balance balance

Check utama:
SUM(debit) == SUM(credit)

Jika tidak balance:
RESTORE FAIL
"""

import asyncio
import os
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
BACKUP_DIR = "/app/backend/backups"
OUTPUT_DIR = "/app/backend/scripts/audit_output"


class RestoreValidator:
    def __init__(self, mongo_url: str = MONGO_URL):
        self.mongo_url = mongo_url
        self.client = None
        self.results = []
        
    async def connect(self):
        self.client = AsyncIOMotorClient(self.mongo_url)
        
    async def disconnect(self):
        if self.client:
            self.client.close()
    
    def log_result(self, test_name: str, passed: bool, details: str = "", data: dict = None):
        """Log validation result"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if details:
            print(f"    → {details[:100]}")
    
    async def validate_tenant_registry(self, db_name: str) -> bool:
        """1. Validate tenant registry"""
        db = self.client[db_name]
        
        # Check company_profile exists
        profile = await db["company_profile"].find_one({}, {"_id": 0})
        if not profile:
            self.log_result(
                "Tenant Registry - company_profile",
                False,
                "company_profile collection is empty"
            )
            return False
        
        # Check required settings
        settings = await db["system_settings"].find({}).to_list(100)
        
        self.log_result(
            "Tenant Registry",
            True,
            f"company_profile exists, {len(settings)} settings found",
            {"profile_name": profile.get("company_name", ""), "settings_count": len(settings)}
        )
        return True
    
    async def validate_users(self, db_name: str) -> bool:
        """2. Validate users collection"""
        db = self.client[db_name]
        
        # Count users
        total_users = await db["users"].count_documents({})
        if total_users == 0:
            self.log_result("Users", False, "No users found in database")
            return False
        
        # Check users have required fields
        users_without_role = await db["users"].count_documents({
            "$or": [
                {"role_id": {"$exists": False}},
                {"role_id": None}
            ]
        })
        
        # Check active users
        active_users = await db["users"].count_documents({"is_active": {"$ne": False}})
        
        valid = users_without_role == 0 or users_without_role < total_users * 0.1  # Allow 10% without role
        
        self.log_result(
            "Users",
            valid,
            f"Total: {total_users}, Active: {active_users}, Without role_id: {users_without_role}",
            {
                "total_users": total_users,
                "active_users": active_users,
                "users_without_role_id": users_without_role
            }
        )
        return valid
    
    async def validate_journal_entries(self, db_name: str) -> bool:
        """3. Validate journal entries are balanced"""
        db = self.client[db_name]
        
        # Count journals
        total_journals = await db["journal_entries"].count_documents({})
        if total_journals == 0:
            self.log_result(
                "Journal Entries",
                True,
                "No journal entries (may be fresh database)",
                {"total": 0}
            )
            return True
        
        # Check each journal is internally balanced
        unbalanced_journals = []
        
        async for journal in db["journal_entries"].find({"status": "posted"}, {"_id": 0, "journal_number": 1, "entries": 1, "lines": 1}):
            entries = journal.get("entries") or journal.get("lines") or []
            if not entries:
                continue
            
            total_debit = sum(e.get("debit", 0) for e in entries)
            total_credit = sum(e.get("credit", 0) for e in entries)
            
            if abs(total_debit - total_credit) > 0.01:  # Allow 1 cent tolerance
                unbalanced_journals.append({
                    "journal_number": journal.get("journal_number", ""),
                    "debit": total_debit,
                    "credit": total_credit,
                    "diff": total_debit - total_credit
                })
        
        valid = len(unbalanced_journals) == 0
        
        self.log_result(
            "Journal Entries",
            valid,
            f"Total: {total_journals}, Unbalanced: {len(unbalanced_journals)}",
            {
                "total_journals": total_journals,
                "unbalanced_count": len(unbalanced_journals),
                "unbalanced_samples": unbalanced_journals[:5]
            }
        )
        return valid
    
    async def validate_stock_movements(self, db_name: str) -> bool:
        """4. Validate stock movements (SSOT)"""
        db = self.client[db_name]
        
        # Count stock movements
        total_movements = await db["stock_movements"].count_documents({})
        
        # Get unique products in movements
        products_in_movements = await db["stock_movements"].distinct("product_id")
        
        # Check for movements with missing required fields
        invalid_movements = await db["stock_movements"].count_documents({
            "$or": [
                {"product_id": {"$exists": False}},
                {"quantity": {"$exists": False}},
                {"movement_type": {"$exists": False}}
            ]
        })
        
        valid = invalid_movements == 0 or invalid_movements < total_movements * 0.01
        
        self.log_result(
            "Stock Movements (SSOT)",
            valid,
            f"Total: {total_movements}, Products: {len(products_in_movements)}, Invalid: {invalid_movements}",
            {
                "total_movements": total_movements,
                "unique_products": len(products_in_movements),
                "invalid_movements": invalid_movements
            }
        )
        return valid
    
    async def validate_trial_balance(self, db_name: str) -> Dict:
        """5. Validate Trial Balance - SUM(debit) == SUM(credit)
        
        This is the CRITICAL CHECK
        If not balanced: RESTORE FAIL
        """
        db = self.client[db_name]
        
        # Aggregate all debit and credit from journal entries
        pipeline = [
            {"$match": {"status": "posted"}},
            {"$unwind": {"path": "$entries", "preserveNullAndEmptyArrays": True}},
            {"$group": {
                "_id": None,
                "total_debit": {"$sum": "$entries.debit"},
                "total_credit": {"$sum": "$entries.credit"}
            }}
        ]
        
        result = await db["journal_entries"].aggregate(pipeline).to_list(1)
        
        if not result:
            # Try with 'lines' field
            pipeline[1] = {"$unwind": {"path": "$lines", "preserveNullAndEmptyArrays": True}}
            pipeline[2] = {"$group": {
                "_id": None,
                "total_debit": {"$sum": "$lines.debit"},
                "total_credit": {"$sum": "$lines.credit"}
            }}
            result = await db["journal_entries"].aggregate(pipeline).to_list(1)
        
        if not result:
            self.log_result(
                "Trial Balance (CRITICAL)",
                True,
                "No journal entries to validate",
                {"total_debit": 0, "total_credit": 0, "difference": 0}
            )
            return {"balanced": True, "debit": 0, "credit": 0}
        
        totals = result[0]
        total_debit = totals.get("total_debit", 0) or 0
        total_credit = totals.get("total_credit", 0) or 0
        difference = abs(total_debit - total_credit)
        
        # Allow tolerance of 1 rupiah
        balanced = difference < 1
        
        self.log_result(
            "Trial Balance (CRITICAL)",
            balanced,
            f"Debit: Rp {total_debit:,.0f} | Credit: Rp {total_credit:,.0f} | Diff: Rp {difference:,.0f}",
            {
                "total_debit": total_debit,
                "total_credit": total_credit,
                "difference": difference,
                "balanced": balanced
            }
        )
        
        return {
            "balanced": balanced,
            "debit": total_debit,
            "credit": total_credit,
            "difference": difference
        }
    
    async def validate_database(self, db_name: str) -> Dict:
        """Run all validations on a database"""
        print(f"\n{'='*70}")
        print(f"POST-RESTORE VALIDATION: {db_name}")
        print(f"{'='*70}\n")
        
        await self.connect()
        self.results = []
        
        # Run all validations
        v1 = await self.validate_tenant_registry(db_name)
        v2 = await self.validate_users(db_name)
        v3 = await self.validate_journal_entries(db_name)
        v4 = await self.validate_stock_movements(db_name)
        trial_balance = await self.validate_trial_balance(db_name)
        
        await self.disconnect()
        
        # Calculate final result
        all_passed = v1 and v2 and v3 and v4 and trial_balance.get("balanced", False)
        critical_passed = trial_balance.get("balanced", False)
        
        validation_result = {
            "database": db_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "all_tests_passed": all_passed,
            "critical_passed": critical_passed,
            "status": "VALID" if all_passed else ("CRITICAL_FAIL" if not critical_passed else "PARTIAL_FAIL"),
            "trial_balance": trial_balance,
            "tests": self.results,
            "summary": {
                "passed": sum(1 for r in self.results if r["passed"]),
                "failed": sum(1 for r in self.results if not r["passed"]),
                "total": len(self.results)
            }
        }
        
        # Print summary
        print(f"\n{'='*70}")
        print("VALIDATION SUMMARY")
        print(f"{'='*70}")
        print(f"Database: {db_name}")
        print(f"Tests Passed: {validation_result['summary']['passed']}/{validation_result['summary']['total']}")
        print(f"Trial Balance: {'✅ BALANCED' if critical_passed else '❌ NOT BALANCED'}")
        print(f"Final Status: {validation_result['status']}")
        print(f"{'='*70}")
        
        if not critical_passed:
            print("\n🚨 RESTORE FAIL: Trial Balance tidak balance!")
            print("   SUM(debit) != SUM(credit)")
            print("   Database tidak dalam kondisi valid untuk digunakan.")
        
        return validation_result
    
    async def validate_all_tenants(self) -> Dict:
        """Validate all active tenants"""
        # Load tenant list
        businesses_file = "/app/backend/data/businesses.json"
        if not os.path.exists(businesses_file):
            return {"error": "businesses.json not found"}
        
        with open(businesses_file, "r") as f:
            businesses = json.load(f)
        
        results = {}
        all_valid = True
        
        for b in businesses:
            if b.get("is_active") and not b.get("is_test"):
                db_name = b.get("db_name")
                result = await self.validate_database(db_name)
                results[db_name] = result
                if result.get("status") != "VALID":
                    all_valid = False
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "all_tenants_valid": all_valid,
            "tenants": results
        }


# ==================== CLI ====================

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OCB TITAN Post-Restore Validation")
    parser.add_argument("--db", type=str, help="Specific database to validate")
    parser.add_argument("--all", action="store_true", help="Validate all tenants")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    validator = RestoreValidator()
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if args.all:
        result = await validator.validate_all_tenants()
        output_file = args.output or f"{OUTPUT_DIR}/restore_validation_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    elif args.db:
        result = await validator.validate_database(args.db)
        output_file = args.output or f"{OUTPUT_DIR}/restore_validation_{args.db}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    else:
        # Default: validate ocb_titan
        result = await validator.validate_database("ocb_titan")
        output_file = args.output or f"{OUTPUT_DIR}/restore_validation_ocb_titan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Save result
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n📄 Validation report saved: {output_file}")
    
    # Return exit code based on validation
    if args.all:
        exit_code = 0 if result.get("all_tenants_valid") else 1
    else:
        exit_code = 0 if result.get("status") == "VALID" else 1
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
