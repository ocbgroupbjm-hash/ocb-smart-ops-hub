"""
OCB TITAN AI - Journal Balance Audit & Correction Script
=========================================================
PERINTAH 1: BERESKAN HISTORICAL JOURNAL IMBALANCE

Sesuai MASTER BLUEPRINT SUPER DEWA:
- Scan seluruh jurnal historis semua tenant aktif
- Klasifikasi: BALANCED, UNBALANCED_MINOR, UNBALANCED_CRITICAL, MISSING_LINES, INVALID_REFERENCE
- JANGAN EDIT POSTED JOURNAL LANGSUNG
- Perbaikan lewat: reversal journal, correcting journal, suspense clearing

Author: E1 Agent
Date: 2026-03-13
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from decimal import Decimal, ROUND_HALF_UP
import uuid

# Active tenants from blueprint
ACTIVE_TENANTS = [
    "ocb_titan",     # Pilot tenant - process first
    "ocb_baju",
    "ocb_counter", 
    "ocb_unit_4",
    "ocb_unt_1"
]

# Classification thresholds
TOLERANCE_MINOR = 1.0      # Rp 1 tolerance for rounding
TOLERANCE_CRITICAL = 100.0  # Above this is critical

# Suspense account for clearing
SUSPENSE_ACCOUNT = {
    "code": "2-9999",
    "name": "Suspense - Clearing Account"
}

class JournalAuditEngine:
    """Engine untuk audit dan koreksi journal balance"""
    
    def __init__(self, mongo_url: str):
        self.client = AsyncIOMotorClient(mongo_url)
        self.audit_results = {}
        self.corrections = []
        
    async def audit_tenant(self, db_name: str) -> Dict[str, Any]:
        """Audit semua journal di satu tenant"""
        db = self.client[db_name]
        
        results = {
            "tenant_id": db_name,
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_journals": 0,
            "balanced": 0,
            "unbalanced_minor": 0,
            "unbalanced_critical": 0,
            "missing_lines": 0,
            "invalid_reference": 0,
            "total_imbalance_amount": 0,
            "journals": []
        }
        
        # Get all journal entries
        journals = await db.journal_entries.find({}, {"_id": 0}).to_list(10000)
        results["total_journals"] = len(journals)
        
        for journal in journals:
            journal_audit = await self._audit_single_journal(db, journal)
            results["journals"].append(journal_audit)
            
            # Update counters
            classification = journal_audit["classification"]
            if classification == "BALANCED":
                results["balanced"] += 1
            elif classification == "UNBALANCED_MINOR":
                results["unbalanced_minor"] += 1
                results["total_imbalance_amount"] += abs(journal_audit["difference"])
            elif classification == "UNBALANCED_CRITICAL":
                results["unbalanced_critical"] += 1
                results["total_imbalance_amount"] += abs(journal_audit["difference"])
            elif classification == "MISSING_LINES":
                results["missing_lines"] += 1
            elif classification == "INVALID_REFERENCE":
                results["invalid_reference"] += 1
        
        return results
    
    async def _audit_single_journal(self, db, journal: Dict) -> Dict[str, Any]:
        """Audit single journal entry"""
        journal_id = journal.get("id", journal.get("journal_number", "unknown"))
        
        # Get lines from 'lines' or 'entries' field
        lines = journal.get("lines", []) or journal.get("entries", [])
        
        audit = {
            "journal_id": journal_id,
            "journal_number": journal.get("journal_number", ""),
            "ref_type": journal.get("reference_type", journal.get("ref_type", "")),
            "ref_id": journal.get("reference_id", journal.get("ref_id", "")),
            "reference": journal.get("reference", ""),
            "description": journal.get("description", ""),
            "total_debit": 0,
            "total_credit": 0,
            "difference": 0,
            "line_count": len(lines),
            "created_at": journal.get("created_at", ""),
            "posted_at": journal.get("posted_at", journal.get("date", "")),
            "status": journal.get("status", "unknown"),
            "classification": "BALANCED",
            "issues": []
        }
        
        # Check for missing lines
        if not lines:
            audit["classification"] = "MISSING_LINES"
            audit["issues"].append("No journal lines found")
            return audit
        
        # Calculate totals
        for line in lines:
            debit = float(line.get("debit", 0) or 0)
            credit = float(line.get("credit", 0) or 0)
            audit["total_debit"] += debit
            audit["total_credit"] += credit
            
            # Validate line has account
            if not line.get("account_code") and not line.get("account_id"):
                audit["issues"].append(f"Line missing account code/id")
        
        # Calculate difference
        audit["difference"] = round(audit["total_debit"] - audit["total_credit"], 2)
        
        # Classify
        abs_diff = abs(audit["difference"])
        if abs_diff < 0.01:  # Essentially zero
            audit["classification"] = "BALANCED"
        elif abs_diff <= TOLERANCE_MINOR:
            audit["classification"] = "UNBALANCED_MINOR"
            audit["issues"].append(f"Minor imbalance: Rp {audit['difference']:,.2f}")
        elif abs_diff <= TOLERANCE_CRITICAL:
            audit["classification"] = "UNBALANCED_MINOR"
            audit["issues"].append(f"Minor imbalance: Rp {audit['difference']:,.2f}")
        else:
            audit["classification"] = "UNBALANCED_CRITICAL"
            audit["issues"].append(f"CRITICAL imbalance: Rp {audit['difference']:,.2f}")
        
        # Validate reference if exists
        if audit["ref_type"] and audit["ref_id"]:
            ref_valid = await self._validate_reference(db, audit["ref_type"], audit["ref_id"])
            if not ref_valid:
                if audit["classification"] == "BALANCED":
                    audit["classification"] = "INVALID_REFERENCE"
                audit["issues"].append(f"Reference not found: {audit['ref_type']}/{audit['ref_id']}")
        
        return audit
    
    async def _validate_reference(self, db, ref_type: str, ref_id: str) -> bool:
        """Validate that referenced document exists"""
        collection_map = {
            "sales": "sales_invoices",
            "sales_invoice": "sales_invoices",
            "purchase": "purchase_invoices",
            "purchase_invoice": "purchase_invoices",
            "pos": "transactions",
            "pos_transaction": "transactions",
            "cash_transaction": "cash_transactions",
            "deposit": "deposits",
            "payroll": "payroll_runs",
            "stock_adjustment": "stock_adjustments",
            "transfer": "stock_transfers",
            "return": "sales_returns",
            "sales_return": "sales_returns",
            "expense": "cash_expenses"
        }
        
        collection_name = collection_map.get(ref_type.lower())
        if not collection_name:
            return True  # Unknown ref type, assume valid
        
        doc = await db[collection_name].find_one(
            {"$or": [{"id": ref_id}, {"_id": ref_id}]},
            {"_id": 1}
        )
        return doc is not None
    
    async def generate_corrections(self, audit_results: Dict) -> List[Dict]:
        """Generate correction journals for imbalanced entries"""
        corrections = []
        
        for journal_audit in audit_results.get("journals", []):
            if journal_audit["classification"] in ["UNBALANCED_MINOR", "UNBALANCED_CRITICAL"]:
                correction = self._create_correction_journal(
                    audit_results["tenant_id"],
                    journal_audit
                )
                corrections.append(correction)
        
        return corrections
    
    def _create_correction_journal(self, tenant_id: str, journal_audit: Dict) -> Dict:
        """Create a correcting journal entry for imbalanced journal"""
        diff = journal_audit["difference"]
        now = datetime.now(timezone.utc).isoformat()
        
        correction = {
            "id": str(uuid.uuid4()),
            "journal_number": f"COR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "reference": f"CORRECTION-{journal_audit['journal_number']}",
            "reference_type": "correction",
            "reference_id": journal_audit["journal_id"],
            "description": f"Koreksi selisih jurnal {journal_audit['journal_number']}: Rp {abs(diff):,.2f}",
            "lines": [],
            "entries": [],
            "total_debit": 0,
            "total_credit": 0,
            "status": "draft",  # Must be reviewed before posting
            
            # Audit correction fields
            "correction_of_journal_id": journal_audit["journal_id"],
            "correction_of_journal_number": journal_audit["journal_number"],
            "correction_reason": f"Selisih {journal_audit['classification']}: D={journal_audit['total_debit']:,.2f} C={journal_audit['total_credit']:,.2f} Diff={diff:,.2f}",
            "correction_method": "suspense_clearing",
            "corrected_by": "system_audit",
            "corrected_at": now,
            
            "created_at": now,
            "created_by": "system_audit",
            "tenant_id": tenant_id
        }
        
        # Create balancing entry using suspense account
        if diff > 0:
            # Debit > Credit, need more credit
            entry = {
                "account_code": SUSPENSE_ACCOUNT["code"],
                "account_name": SUSPENSE_ACCOUNT["name"],
                "debit": 0,
                "credit": abs(diff),
                "description": f"Clearing selisih jurnal {journal_audit['journal_number']}"
            }
            correction["total_credit"] = abs(diff)
        else:
            # Credit > Debit, need more debit
            entry = {
                "account_code": SUSPENSE_ACCOUNT["code"],
                "account_name": SUSPENSE_ACCOUNT["name"],
                "debit": abs(diff),
                "credit": 0,
                "description": f"Clearing selisih jurnal {journal_audit['journal_number']}"
            }
            correction["total_debit"] = abs(diff)
        
        correction["lines"].append(entry)
        correction["entries"].append(entry)
        
        return correction
    
    async def apply_corrections(self, db_name: str, corrections: List[Dict], dry_run: bool = True) -> Dict:
        """Apply correction journals to database"""
        db = self.client[db_name]
        
        result = {
            "tenant_id": db_name,
            "total_corrections": len(corrections),
            "applied": 0,
            "skipped": 0,
            "errors": [],
            "dry_run": dry_run
        }
        
        for correction in corrections:
            try:
                if not dry_run:
                    # Insert correction journal
                    await db.journal_entries.insert_one(correction)
                    result["applied"] += 1
                else:
                    result["skipped"] += 1
            except Exception as e:
                result["errors"].append({
                    "journal_id": correction["correction_of_journal_id"],
                    "error": str(e)
                })
        
        return result
    
    async def recalculate_trial_balance(self, db_name: str) -> Dict:
        """Recalculate trial balance from journal entries"""
        db = self.client[db_name]
        
        # Check if journal_entries exists and has documents
        count = await db.journal_entries.count_documents({})
        if count == 0:
            return {
                "tenant_id": db_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "accounts": [],
                "total_debit": 0,
                "total_credit": 0,
                "difference": 0,
                "is_balanced": True,
                "note": "No journal entries found"
            }
        
        # Try aggregation with 'lines' field first
        try:
            pipeline = [
                {"$match": {"status": {"$in": ["posted", "POSTED"]}}},
                {"$unwind": {"path": "$lines", "preserveNullAndEmptyArrays": False}},
                {"$group": {
                    "_id": "$lines.account_code",
                    "account_name": {"$first": "$lines.account_name"},
                    "total_debit": {"$sum": {"$ifNull": ["$lines.debit", 0]}},
                    "total_credit": {"$sum": {"$ifNull": ["$lines.credit", 0]}}
                }},
                {"$match": {"_id": {"$ne": None}}},
                {"$sort": {"_id": 1}}
            ]
            results = await db.journal_entries.aggregate(pipeline).to_list(1000)
        except Exception:
            results = []
        
        # If no results, try with 'entries' field
        if not results:
            try:
                pipeline = [
                    {"$match": {"status": {"$in": ["posted", "POSTED"]}}},
                    {"$unwind": {"path": "$entries", "preserveNullAndEmptyArrays": False}},
                    {"$group": {
                        "_id": "$entries.account_code",
                        "account_name": {"$first": "$entries.account_name"},
                        "total_debit": {"$sum": {"$ifNull": ["$entries.debit", 0]}},
                        "total_credit": {"$sum": {"$ifNull": ["$entries.credit", 0]}}
                    }},
                    {"$match": {"_id": {"$ne": None}}},
                    {"$sort": {"_id": 1}}
                ]
                results = await db.journal_entries.aggregate(pipeline).to_list(1000)
            except Exception:
                results = []
        
        total_debit = sum(r.get("total_debit", 0) or 0 for r in results)
        total_credit = sum(r.get("total_credit", 0) or 0 for r in results)
        
        return {
            "tenant_id": db_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "accounts": results,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "difference": total_debit - total_credit,
            "is_balanced": abs(total_debit - total_credit) < 1
        }
    
    async def recalculate_balance_sheet(self, db_name: str) -> Dict:
        """Recalculate balance sheet from journal entries"""
        tb = await self.recalculate_trial_balance(db_name)
        
        assets = 0
        liabilities = 0
        equity = 0
        revenue = 0
        expenses = 0
        
        for acc in tb.get("accounts", []):
            code = acc.get("_id", "") or ""
            debit = acc.get("total_debit", 0) or 0
            credit = acc.get("total_credit", 0) or 0
            
            if not code:
                continue
            
            if code.startswith("1"):  # Assets
                assets += debit - credit
            elif code.startswith("2"):  # Liabilities
                liabilities += credit - debit
            elif code.startswith("3"):  # Equity
                equity += credit - debit
            elif code.startswith("4"):  # Revenue
                revenue += credit - debit
            elif code.startswith("5"):  # Expenses
                expenses += debit - credit
        
        net_income = revenue - expenses
        total_equity = equity + net_income
        
        return {
            "tenant_id": db_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "revenue": revenue,
            "expenses": expenses,
            "net_income": net_income,
            "total_equity": total_equity,
            "is_balanced": abs(assets - (liabilities + total_equity)) < 1,
            "equation": {
                "left": assets,
                "right": liabilities + total_equity,
                "difference": assets - (liabilities + total_equity)
            }
        }


async def run_full_audit():
    """Run full audit on all active tenants"""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    engine = JournalAuditEngine(mongo_url)
    
    print("=" * 60)
    print("OCB TITAN AI - JOURNAL BALANCE AUDIT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Active Tenants: {', '.join(ACTIVE_TENANTS)}")
    print()
    
    all_results = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "tenants": {}
    }
    
    all_corrections = []
    
    for tenant in ACTIVE_TENANTS:
        print(f"\n{'='*40}")
        print(f"Auditing: {tenant}")
        print(f"{'='*40}")
        
        # Run audit
        audit_result = await engine.audit_tenant(tenant)
        all_results["tenants"][tenant] = audit_result
        
        # Print summary
        print(f"Total Journals: {audit_result['total_journals']}")
        print(f"  BALANCED: {audit_result['balanced']}")
        print(f"  UNBALANCED_MINOR: {audit_result['unbalanced_minor']}")
        print(f"  UNBALANCED_CRITICAL: {audit_result['unbalanced_critical']}")
        print(f"  MISSING_LINES: {audit_result['missing_lines']}")
        print(f"  INVALID_REFERENCE: {audit_result['invalid_reference']}")
        print(f"Total Imbalance: Rp {audit_result['total_imbalance_amount']:,.2f}")
        
        # Generate corrections
        if audit_result['unbalanced_minor'] > 0 or audit_result['unbalanced_critical'] > 0:
            corrections = await engine.generate_corrections(audit_result)
            all_corrections.extend(corrections)
            print(f"Corrections Generated: {len(corrections)}")
        
        # Get TB before
        tb_before = await engine.recalculate_trial_balance(tenant)
        print(f"\nTrial Balance Status:")
        print(f"  Total Debit: Rp {tb_before['total_debit']:,.2f}")
        print(f"  Total Credit: Rp {tb_before['total_credit']:,.2f}")
        print(f"  Balanced: {tb_before['is_balanced']}")
        
        # Get Balance Sheet
        bs = await engine.recalculate_balance_sheet(tenant)
        print(f"\nBalance Sheet Status:")
        print(f"  Assets: Rp {bs['assets']:,.2f}")
        print(f"  Liabilities + Equity: Rp {bs['liabilities'] + bs['total_equity']:,.2f}")
        print(f"  Balanced: {bs['is_balanced']}")
    
    # Save results
    output_dir = "/app/backend/scripts/audit_output"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    # Save audit report
    with open(f"{output_dir}/audit_report_before_{timestamp}.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    # Save corrections
    with open(f"{output_dir}/corrections_{timestamp}.json", "w") as f:
        json.dump(all_corrections, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print("AUDIT COMPLETE")
    print(f"{'='*60}")
    print(f"Reports saved to: {output_dir}")
    print(f"  - audit_report_before_{timestamp}.json")
    print(f"  - corrections_{timestamp}.json")
    
    return all_results, all_corrections


async def apply_corrections_with_review():
    """Apply corrections after review (dry_run=False)"""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    engine = JournalAuditEngine(mongo_url)
    
    # Load latest corrections
    output_dir = "/app/backend/scripts/audit_output"
    correction_files = [f for f in os.listdir(output_dir) if f.startswith("corrections_")]
    
    if not correction_files:
        print("No correction files found. Run audit first.")
        return
    
    latest_file = sorted(correction_files)[-1]
    
    with open(f"{output_dir}/{latest_file}", "r") as f:
        corrections = json.load(f)
    
    print(f"Loaded {len(corrections)} corrections from {latest_file}")
    
    # Group by tenant
    by_tenant = {}
    for corr in corrections:
        tenant = corr.get("tenant_id", "unknown")
        if tenant not in by_tenant:
            by_tenant[tenant] = []
        by_tenant[tenant].append(corr)
    
    # Apply with dry_run=True first
    for tenant, corrs in by_tenant.items():
        result = await engine.apply_corrections(tenant, corrs, dry_run=True)
        print(f"\n{tenant}: Would apply {result['total_corrections']} corrections")
    
    # Confirm before actual apply
    print("\n" + "="*60)
    print("DRY RUN COMPLETE. To apply corrections, set dry_run=False")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_full_audit())
