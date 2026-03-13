"""
OCB TITAN ERP - INVENTORY VS GL RECONCILIATION ENGINE
MASTER BLUEPRINT: Enterprise Hardening Phase

Membandingkan:
- Inventory valuation (dari stock * cost)
- GL Persediaan (akun 1104)

Jika selisih > threshold → ALERT
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, List
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
import uuid
import json
import os

router = APIRouter(prefix="/reconciliation", tags=["Inventory vs GL Reconciliation"])

OUTPUT_DIR = "/app/backend/scripts/audit_output"


class InventoryGLReconciliation:
    def __init__(self, db):
        self.db = db
        self.timestamp = datetime.now(timezone.utc)
    
    async def get_inventory_valuation(self) -> Dict:
        """
        Calculate total inventory value from products
        Value = SUM(stock * cost_price)
        """
        pipeline = [
            {"$match": {"stock": {"$gt": 0}}},
            {"$project": {
                "id": 1,
                "name": 1,
                "sku": 1,
                "stock": 1,
                "cost_price": {"$ifNull": ["$cost_price", 0]},
                "value": {"$multiply": [
                    {"$ifNull": ["$stock", 0]},
                    {"$ifNull": ["$cost_price", 0]}
                ]}
            }},
            {"$group": {
                "_id": None,
                "total_value": {"$sum": "$value"},
                "total_qty": {"$sum": "$stock"},
                "product_count": {"$sum": 1}
            }}
        ]
        
        result = await self.db["products"].aggregate(pipeline).to_list(1)
        
        if result:
            return {
                "source": "inventory",
                "total_value": result[0].get("total_value", 0),
                "total_qty": result[0].get("total_qty", 0),
                "product_count": result[0].get("product_count", 0)
            }
        
        return {"source": "inventory", "total_value": 0, "total_qty": 0, "product_count": 0}
    
    async def get_gl_inventory_balance(self) -> Dict:
        """
        Get inventory balance from GL (account 1104)
        Balance = SUM(debit) - SUM(credit) for account 1104
        """
        pipeline = [
            {"$match": {"status": "posted"}},
            {"$unwind": "$entries"},
            {"$match": {"entries.account_code": "1104"}},
            {"$group": {
                "_id": None,
                "total_debit": {"$sum": "$entries.debit"},
                "total_credit": {"$sum": "$entries.credit"},
                "journal_count": {"$sum": 1}
            }}
        ]
        
        result = await self.db["journal_entries"].aggregate(pipeline).to_list(1)
        
        if result:
            balance = (result[0].get("total_debit", 0) or 0) - (result[0].get("total_credit", 0) or 0)
            return {
                "source": "gl_1104",
                "account_code": "1104",
                "account_name": "Inventory / Persediaan",
                "total_debit": result[0].get("total_debit", 0),
                "total_credit": result[0].get("total_credit", 0),
                "balance": balance,
                "journal_count": result[0].get("journal_count", 0)
            }
        
        return {
            "source": "gl_1104",
            "account_code": "1104",
            "balance": 0,
            "total_debit": 0,
            "total_credit": 0,
            "journal_count": 0
        }
    
    async def reconcile(self) -> Dict:
        """
        Perform reconciliation between inventory and GL
        """
        inventory = await self.get_inventory_valuation()
        gl = await self.get_gl_inventory_balance()
        
        inventory_value = inventory.get("total_value", 0)
        gl_balance = gl.get("balance", 0)
        
        difference = inventory_value - gl_balance
        percentage_diff = (difference / gl_balance * 100) if gl_balance != 0 else 0
        
        # Determine status
        if abs(difference) < 1:
            status = "RECONCILED"
            alert = False
        elif abs(percentage_diff) < 1:  # Less than 1% difference
            status = "MINOR_VARIANCE"
            alert = False
        elif abs(percentage_diff) < 5:  # 1-5% difference
            status = "VARIANCE_WARNING"
            alert = True
        else:
            status = "MAJOR_VARIANCE"
            alert = True
        
        result = {
            "reconciliation_id": f"INVGL-{self.timestamp.strftime('%Y%m%d_%H%M%S')}",
            "timestamp": self.timestamp.isoformat(),
            "inventory": inventory,
            "gl": gl,
            "comparison": {
                "inventory_value": inventory_value,
                "gl_balance": gl_balance,
                "difference": difference,
                "percentage_difference": round(percentage_diff, 2),
                "status": status,
                "alert_required": alert
            },
            "recommendation": self._get_recommendation(difference, status)
        }
        
        return result
    
    def _get_recommendation(self, difference: float, status: str) -> str:
        if status == "RECONCILED":
            return "Tidak ada tindakan diperlukan. Inventory dan GL sudah sesuai."
        elif status == "MINOR_VARIANCE":
            return "Selisih kecil, kemungkinan dari pembulatan. Monitor di periode berikutnya."
        elif difference > 0:
            return f"Inventory lebih besar dari GL sebesar Rp {abs(difference):,.0f}. Periksa: (1) Penerimaan barang tanpa journal, (2) Adjustment stok tanpa journal."
        else:
            return f"GL lebih besar dari Inventory sebesar Rp {abs(difference):,.0f}. Periksa: (1) Journal pembelian tanpa penerimaan, (2) Penjualan dengan stok negatif."


# ==================== API ENDPOINTS ====================

@router.get("/inventory-vs-gl")
async def reconcile_inventory_vs_gl(
    user: dict = Depends(get_current_user)
):
    """
    Perform inventory vs GL reconciliation
    
    Compares:
    - Inventory valuation (stock * cost)
    - GL account 1104 balance
    """
    db = get_db()
    
    reconciler = InventoryGLReconciliation(db)
    result = await reconciler.reconcile()
    
    # Save to file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save JSON
    json_path = f"{OUTPUT_DIR}/inventory_vs_gl_recon.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    
    return result


@router.get("/inventory-vs-gl/detail")
async def get_inventory_detail(
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """Get detailed inventory valuation by product"""
    db = get_db()
    
    pipeline = [
        {"$match": {"stock": {"$ne": 0}}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "name": 1,
            "sku": 1,
            "stock": 1,
            "cost_price": {"$ifNull": ["$cost_price", 0]},
            "value": {"$multiply": [
                {"$ifNull": ["$stock", 0]},
                {"$ifNull": ["$cost_price", 0]}
            ]}
        }},
        {"$sort": {"value": -1}},
        {"$limit": limit}
    ]
    
    products = await db["products"].aggregate(pipeline).to_list(limit)
    
    total_value = sum(p.get("value", 0) for p in products)
    
    return {
        "products": products,
        "total_value": total_value,
        "count": len(products)
    }


@router.get("/gl-inventory-transactions")
async def get_gl_inventory_transactions(
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get recent GL transactions for inventory account (1104)"""
    db = get_db()
    
    pipeline = [
        {"$match": {"status": "posted"}},
        {"$unwind": "$entries"},
        {"$match": {"entries.account_code": "1104"}},
        {"$project": {
            "_id": 0,
            "journal_number": 1,
            "transaction_type": 1,
            "description": 1,
            "posted_at": 1,
            "debit": "$entries.debit",
            "credit": "$entries.credit"
        }},
        {"$sort": {"posted_at": -1}},
        {"$limit": limit}
    ]
    
    transactions = await db["journal_entries"].aggregate(pipeline).to_list(limit)
    
    return {
        "transactions": transactions,
        "count": len(transactions)
    }


@router.post("/inventory-vs-gl/generate-report")
async def generate_reconciliation_report(
    user: dict = Depends(get_current_user)
):
    """Generate full reconciliation report (JSON + MD)"""
    db = get_db()
    
    reconciler = InventoryGLReconciliation(db)
    result = await reconciler.reconcile()
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save JSON
    json_path = f"{OUTPUT_DIR}/inventory_vs_gl_recon.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    
    # Generate MD report
    md_path = f"{OUTPUT_DIR}/inventory_vs_gl_recon_report.md"
    with open(md_path, "w") as f:
        f.write("# OCB TITAN - INVENTORY VS GL RECONCILIATION REPORT\n\n")
        f.write(f"**Reconciliation ID:** {result['reconciliation_id']}\n")
        f.write(f"**Timestamp:** {result['timestamp']}\n\n")
        
        f.write("## Summary\n\n")
        f.write("| Source | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Inventory Valuation | Rp {result['inventory']['total_value']:,.0f} |\n")
        f.write(f"| GL Balance (1104) | Rp {result['gl']['balance']:,.0f} |\n")
        f.write(f"| **Difference** | **Rp {result['comparison']['difference']:,.0f}** |\n")
        f.write(f"| Percentage | {result['comparison']['percentage_difference']}% |\n")
        f.write(f"| **Status** | **{result['comparison']['status']}** |\n\n")
        
        f.write("## Details\n\n")
        f.write("### Inventory\n")
        f.write(f"- Products with stock: {result['inventory']['product_count']}\n")
        f.write(f"- Total quantity: {result['inventory']['total_qty']:,.0f}\n")
        f.write(f"- Total value: Rp {result['inventory']['total_value']:,.0f}\n\n")
        
        f.write("### GL Account 1104\n")
        f.write(f"- Total debit: Rp {result['gl']['total_debit']:,.0f}\n")
        f.write(f"- Total credit: Rp {result['gl']['total_credit']:,.0f}\n")
        f.write(f"- Balance: Rp {result['gl']['balance']:,.0f}\n")
        f.write(f"- Journal entries: {result['gl']['journal_count']}\n\n")
        
        f.write("## Recommendation\n\n")
        f.write(result['recommendation'] + "\n\n")
        
        f.write("---\n")
        f.write(f"*Generated: {result['timestamp']}*\n")
    
    # Create audit log
    await db["audit_logs"].insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": db.name,
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "action": "INVENTORY_GL_RECONCILIATION",
        "module": "reconciliation",
        "entity_type": "report",
        "entity_id": result['reconciliation_id'],
        "before_data": None,
        "after_data": {
            "status": result['comparison']['status'],
            "difference": result['comparison']['difference']
        },
        "description": f"Generated inventory vs GL reconciliation: {result['comparison']['status']}",
        "ip_address": "system",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "reconciliation": result,
        "files_generated": {
            "json": json_path,
            "markdown": md_path
        }
    }
