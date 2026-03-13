#!/usr/bin/env python3
"""
OCB TITAN ERP - STOCK DISCREPANCY FIX ENGINE
MASTER BLUEPRINT: Production Checklist SUPER DEWA

Fix all stock discrepancies via BRE:
1. Read stock_reconciliation_report.json
2. Create inventory adjustments via BRE
3. Create journal entries via BRE
4. Generate evidence files

All adjustments WAJIB lewat BRE.
"""

import asyncio
import os
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Any
import uuid

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
REPORTS_DIR = "/app/reports"
OUTPUT_DIR = "/app/backend/scripts/audit_output"


class StockDiscrepancyFixer:
    def __init__(self, mongo_url: str = MONGO_URL):
        self.mongo_url = mongo_url
        self.client = None
        self.timestamp = datetime.now(timezone.utc)
        self.adjustments = []
        self.journals = []
        self.skipped = []
        
    async def connect(self):
        self.client = AsyncIOMotorClient(self.mongo_url)
        
    async def disconnect(self):
        if self.client:
            self.client.close()
    
    def load_discrepancy_report(self) -> Dict:
        """Load the reconciliation report"""
        report_path = f"{REPORTS_DIR}/stock_reconciliation_report.json"
        if not os.path.exists(report_path):
            raise FileNotFoundError(f"Report not found: {report_path}")
        
        with open(report_path, "r") as f:
            return json.load(f)
    
    async def get_product_info(self, db, product_id: str) -> Dict:
        """Get product details"""
        product = await db["products"].find_one(
            {"id": product_id},
            {"_id": 0, "id": 1, "name": 1, "sku": 1, "cost_price": 1}
        )
        return product or {}
    
    async def get_branch_info(self, db, branch_id: str) -> Dict:
        """Get branch details"""
        if not branch_id:
            return {"name": "Default Warehouse"}
        
        branch = await db["branches"].find_one(
            {"id": branch_id},
            {"_id": 0, "id": 1, "name": 1, "code": 1}
        )
        return branch or {"name": "Unknown Branch"}
    
    async def create_inventory_adjustment_via_bre(
        self,
        db,
        product_id: str,
        product_name: str,
        branch_id: str,
        branch_name: str,
        adjustment_qty: int,
        reason: str
    ) -> Dict:
        """
        Create inventory adjustment through BRE
        This is the ONLY way to modify stock in production
        """
        adjustment_id = str(uuid.uuid4())
        adjustment_number = f"ADJ-FIX-{self.timestamp.strftime('%Y%m%d%H%M%S')}-{len(self.adjustments)+1:03d}"
        
        movement_type = "ADJUSTMENT_PLUS" if adjustment_qty > 0 else "ADJUSTMENT_MINUS"
        
        # 1. Create Stock Movement (SSOT)
        stock_movement = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "product_name": product_name,
            "branch_id": branch_id,
            "branch_name": branch_name,
            "movement_type": movement_type,
            "quantity": adjustment_qty,  # Positive or negative based on direction
            "reference_id": adjustment_id,
            "reference_type": "stock_adjustment",
            "notes": f"Reconciliation fix: {reason}",
            "user_id": "SYSTEM_BRE",
            "created_at": self.timestamp.isoformat()
        }
        
        await db["stock_movements"].insert_one(stock_movement)
        
        # 2. Update product stock cache
        await db["products"].update_one(
            {"id": product_id},
            {"$inc": {"stock": adjustment_qty}}
        )
        
        # 3. Create stock adjustment record
        adjustment = {
            "id": adjustment_id,
            "adjustment_number": adjustment_number,
            "product_id": product_id,
            "product_name": product_name,
            "branch_id": branch_id,
            "branch_name": branch_name,
            "adjustment_type": movement_type,
            "quantity": abs(adjustment_qty),
            "direction": "plus" if adjustment_qty > 0 else "minus",
            "reason": reason,
            "status": "completed",
            "created_by": "SYSTEM_BRE",
            "created_at": self.timestamp.isoformat(),
            "movement_id": stock_movement["id"]
        }
        
        await db["stock_adjustments"].insert_one(adjustment)
        
        self.adjustments.append({
            "adjustment_id": adjustment_id,
            "adjustment_number": adjustment_number,
            "product_id": product_id,
            "product_name": product_name,
            "quantity": adjustment_qty,
            "movement_type": movement_type
        })
        
        return adjustment
    
    async def create_adjustment_journal_via_bre(
        self,
        db,
        adjustment: Dict,
        cost_price: float = 0
    ) -> Dict:
        """
        Create journal entry for inventory adjustment through BRE
        
        If ADJUSTMENT_PLUS (stock increase):
            Debit: Inventory (1104)
            Credit: Inventory Adjustment (5901)
        
        If ADJUSTMENT_MINUS (stock decrease):
            Debit: Inventory Adjustment Expense (5901)
            Credit: Inventory (1104)
        """
        journal_id = str(uuid.uuid4())
        journal_number = f"JV-ADJ-{self.timestamp.strftime('%Y%m%d%H%M%S')}-{len(self.journals)+1:03d}"
        
        qty = adjustment.get("quantity", 0)
        cost = cost_price if cost_price > 0 else 10000  # Default cost if unknown
        amount = abs(qty) * cost
        
        direction = adjustment.get("direction", "plus")
        
        if direction == "plus":
            entries = [
                {
                    "account_code": "1104",
                    "account_name": "Inventory",
                    "debit": amount,
                    "credit": 0,
                    "description": f"Stock adjustment IN: {adjustment.get('product_name', '')}"
                },
                {
                    "account_code": "5901",
                    "account_name": "Inventory Adjustment",
                    "debit": 0,
                    "credit": amount,
                    "description": f"Stock adjustment IN: {adjustment.get('product_name', '')}"
                }
            ]
        else:
            entries = [
                {
                    "account_code": "5901",
                    "account_name": "Inventory Adjustment Expense",
                    "debit": amount,
                    "credit": 0,
                    "description": f"Stock adjustment OUT: {adjustment.get('product_name', '')}"
                },
                {
                    "account_code": "1104",
                    "account_name": "Inventory",
                    "debit": 0,
                    "credit": amount,
                    "description": f"Stock adjustment OUT: {adjustment.get('product_name', '')}"
                }
            ]
        
        journal = {
            "id": journal_id,
            "journal_number": journal_number,
            "transaction_type": "inventory_adjustment",
            "reference_id": adjustment.get("id"),
            "reference_type": "stock_adjustment",
            "description": f"Reconciliation adjustment: {adjustment.get('adjustment_number')}",
            "entries": entries,
            "status": "posted",
            "total_debit": amount,
            "total_credit": amount,
            "created_by": "SYSTEM_BRE",
            "created_at": self.timestamp.isoformat(),
            "posted_at": self.timestamp.isoformat()
        }
        
        await db["journal_entries"].insert_one(journal)
        
        self.journals.append({
            "journal_id": journal_id,
            "journal_number": journal_number,
            "adjustment_id": adjustment.get("id"),
            "amount": amount,
            "type": direction
        })
        
        return journal
    
    async def create_audit_log(self, db, action: str, details: Dict):
        """Create audit log for adjustment"""
        log = {
            "id": str(uuid.uuid4()),
            "tenant_id": db.name,
            "user_id": "SYSTEM_BRE",
            "user_name": "BRE Reconciliation Engine",
            "action": action,
            "module": "stock_reconciliation_fix",
            "entity_type": "inventory_adjustment",
            "entity_id": details.get("adjustment_id", ""),
            "before_data": None,
            "after_data": details,
            "description": f"Stock discrepancy fix: {action}",
            "ip_address": "localhost",
            "created_at": self.timestamp.isoformat()
        }
        
        await db["audit_logs"].insert_one(log)
    
    async def fix_discrepancies(self, db_name: str, auto_fix_threshold: int = 100) -> Dict:
        """
        Fix all discrepancies from reconciliation report
        
        Args:
            db_name: Database name
            auto_fix_threshold: Auto-fix if difference <= threshold, else flag for manual review
        """
        await self.connect()
        db = self.client[db_name]
        
        print("="*70)
        print("OCB TITAN - STOCK DISCREPANCY FIX ENGINE")
        print(f"Database: {db_name}")
        print(f"Timestamp: {self.timestamp.isoformat()}")
        print(f"Auto-fix threshold: {auto_fix_threshold} units")
        print("="*70)
        
        # Load report
        report = self.load_discrepancy_report()
        
        tenant_result = None
        for tr in report.get("tenant_results", []):
            if tr.get("tenant") == db_name:
                tenant_result = tr
                break
        
        if not tenant_result:
            print(f"❌ No results found for tenant: {db_name}")
            return {"error": f"Tenant not found: {db_name}"}
        
        discrepancies = tenant_result.get("discrepancies", [])
        print(f"\n📋 Found {len(discrepancies)} discrepancies to process\n")
        
        fixed_count = 0
        skipped_count = 0
        flagged_count = 0
        
        for i, disc in enumerate(discrepancies):
            product_id = disc.get("product_id", "")
            branch_id = disc.get("branch_id")
            difference = disc.get("difference", 0)
            
            print(f"\n[{i+1}/{len(discrepancies)}] Processing: {product_id[:20]}...")
            
            # Skip invalid products
            if not product_id or product_id == "None":
                print(f"  ⏭️ SKIPPED: Invalid product_id")
                self.skipped.append({
                    "product_id": product_id,
                    "reason": "Invalid product_id",
                    "difference": difference
                })
                skipped_count += 1
                continue
            
            # Get product info
            product = await self.get_product_info(db, product_id)
            if not product:
                print(f"  ⏭️ SKIPPED: Product not found in database")
                self.skipped.append({
                    "product_id": product_id,
                    "reason": "Product not found",
                    "difference": difference
                })
                skipped_count += 1
                continue
            
            product_name = product.get("name", product_id)
            cost_price = product.get("cost_price", 0) or 0
            
            # Get branch info
            branch = await self.get_branch_info(db, branch_id)
            branch_name = branch.get("name", "Default")
            
            # Check threshold
            if abs(difference) > auto_fix_threshold:
                print(f"  🚩 FLAGGED: Difference ({difference}) exceeds threshold ({auto_fix_threshold})")
                self.skipped.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "reason": f"Exceeds auto-fix threshold ({auto_fix_threshold})",
                    "difference": difference,
                    "status": "FLAGGED_MANUAL_REVIEW"
                })
                flagged_count += 1
                continue
            
            # Calculate adjustment needed
            # If movement_qty > cached_qty, cache is behind, need to increase cache
            # If movement_qty < cached_qty, cache is ahead, need to decrease cache
            # But we sync to SSOT, so we adjust the difference
            adjustment_qty = difference  # Positive = add, Negative = subtract
            
            # Create adjustment via BRE
            try:
                adjustment = await self.create_inventory_adjustment_via_bre(
                    db=db,
                    product_id=product_id,
                    product_name=product_name,
                    branch_id=branch_id,
                    branch_name=branch_name,
                    adjustment_qty=-adjustment_qty,  # Negate because we want to match SSOT
                    reason=f"Reconciliation fix: SSOT={disc.get('movement_qty')}, Cache={disc.get('cached_qty')}"
                )
                
                # Create journal via BRE
                await self.create_adjustment_journal_via_bre(
                    db=db,
                    adjustment=adjustment,
                    cost_price=cost_price
                )
                
                # Create audit log
                await self.create_audit_log(db, "STOCK_DISCREPANCY_FIXED", {
                    "adjustment_id": adjustment.get("id"),
                    "product_id": product_id,
                    "difference_fixed": difference,
                    "movement_type": adjustment.get("adjustment_type")
                })
                
                print(f"  ✅ FIXED: {product_name[:30]} | Adjustment: {-adjustment_qty}")
                fixed_count += 1
                
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                self.skipped.append({
                    "product_id": product_id,
                    "reason": f"Error: {str(e)}",
                    "difference": difference
                })
                skipped_count += 1
        
        await self.disconnect()
        
        # Generate reports
        result = {
            "fix_id": f"FIX-{self.timestamp.strftime('%Y%m%d_%H%M%S')}",
            "timestamp": self.timestamp.isoformat(),
            "database": db_name,
            "total_discrepancies": len(discrepancies),
            "fixed": fixed_count,
            "skipped": skipped_count,
            "flagged_manual": flagged_count,
            "adjustments": self.adjustments,
            "journals": self.journals,
            "skipped_items": self.skipped
        }
        
        # Save reports
        self.save_reports(result)
        
        # Print summary
        print("\n" + "="*70)
        print("STOCK DISCREPANCY FIX SUMMARY")
        print("="*70)
        print(f"Total Discrepancies: {len(discrepancies)}")
        print(f"Fixed: {fixed_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Flagged for Manual: {flagged_count}")
        print(f"Adjustments Created: {len(self.adjustments)}")
        print(f"Journals Created: {len(self.journals)}")
        print("="*70)
        
        return result
    
    def save_reports(self, result: Dict):
        """Save all evidence reports"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 1. stock_adjustment_fix_report.md
        md_path = f"{OUTPUT_DIR}/stock_adjustment_fix_report.md"
        with open(md_path, "w") as f:
            f.write("# OCB TITAN - STOCK ADJUSTMENT FIX REPORT\n\n")
            f.write(f"**Fix ID:** {result.get('fix_id', '')}\n")
            f.write(f"**Timestamp:** {result.get('timestamp', '')}\n")
            f.write(f"**Database:** {result.get('database', '')}\n\n")
            f.write("## Summary\n\n")
            f.write(f"- **Total Discrepancies:** {result.get('total_discrepancies', 0)}\n")
            f.write(f"- **Fixed:** {result.get('fixed', 0)}\n")
            f.write(f"- **Skipped:** {result.get('skipped', 0)}\n")
            f.write(f"- **Flagged for Manual Review:** {result.get('flagged_manual', 0)}\n\n")
            f.write("## Adjustments Created\n\n")
            f.write("| # | Adjustment Number | Product | Qty | Type |\n")
            f.write("|---|-------------------|---------|-----|------|\n")
            for i, adj in enumerate(result.get("adjustments", [])):
                f.write(f"| {i+1} | {adj.get('adjustment_number', '')} | {adj.get('product_name', '')[:30]} | {adj.get('quantity', 0)} | {adj.get('movement_type', '')} |\n")
            f.write("\n## Journals Created\n\n")
            f.write("| # | Journal Number | Amount | Type |\n")
            f.write("|---|----------------|--------|------|\n")
            for i, jnl in enumerate(result.get("journals", [])):
                f.write(f"| {i+1} | {jnl.get('journal_number', '')} | Rp {jnl.get('amount', 0):,.0f} | {jnl.get('type', '')} |\n")
            if result.get("skipped_items"):
                f.write("\n## Skipped/Flagged Items\n\n")
                for item in result.get("skipped_items", []):
                    f.write(f"- **{item.get('product_id', '')[:20]}**: {item.get('reason', '')}\n")
        
        print(f"\n📄 Report saved: {md_path}")
        
        # 2. stock_movement_adjustments.json
        json_path = f"{OUTPUT_DIR}/stock_movement_adjustments.json"
        with open(json_path, "w") as f:
            json.dump({
                "fix_id": result.get("fix_id"),
                "timestamp": result.get("timestamp"),
                "adjustments": result.get("adjustments", []),
                "journals": result.get("journals", [])
            }, f, indent=2, default=str)
        print(f"📄 Adjustments saved: {json_path}")
        
        # 3. inventory_vs_gl_recon.json
        recon_path = f"{OUTPUT_DIR}/inventory_vs_gl_recon.json"
        total_adjustment_value = sum(j.get("amount", 0) for j in result.get("journals", []))
        with open(recon_path, "w") as f:
            json.dump({
                "reconciliation_id": result.get("fix_id"),
                "timestamp": result.get("timestamp"),
                "summary": {
                    "total_adjustments": len(result.get("adjustments", [])),
                    "total_journals": len(result.get("journals", [])),
                    "total_adjustment_value": total_adjustment_value,
                    "inventory_account": "1104",
                    "adjustment_account": "5901"
                },
                "journal_summary": result.get("journals", [])
            }, f, indent=2, default=str)
        print(f"📄 Inventory vs GL reconciliation saved: {recon_path}")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OCB TITAN Stock Discrepancy Fix Engine")
    parser.add_argument("--tenant", type=str, default="ocb_titan", help="Tenant database")
    parser.add_argument("--threshold", type=int, default=100, help="Auto-fix threshold")
    
    args = parser.parse_args()
    
    fixer = StockDiscrepancyFixer()
    return await fixer.fix_discrepancies(args.tenant, args.threshold)


if __name__ == "__main__":
    asyncio.run(main())
