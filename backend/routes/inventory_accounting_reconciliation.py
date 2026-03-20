"""
OCB TITAN ERP - INVENTORY TO ACCOUNTING RECONCILIATION ENGINE
P0: Ensure Stock Value = Persediaan Account Balance

RULES ENFORCED:
1. Tidak boleh ada stock movement bernilai tanpa journal impact
2. Tidak boleh ada reversal stock tanpa reversal journal  
3. Tidak boleh ada purchase direct stock in tanpa journal persediaan
4. Stock Value (dari movements) = Persediaan Balance (dari journal)

SOURCES OF TRUTH:
- Stock Value: Calculated from stock_movements (qty * cost)
- Persediaan Balance: Sum of journal entries for persediaan accounts
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/inventory-accounting", tags=["Inventory Accounting Reconciliation"])

# Persediaan account codes used in the system
PERSEDIAAN_ACCOUNT_CODES = ["1-1400", "1-3000", "1-1200"]


class InventoryAccountingReconciliation:
    def __init__(self, db):
        self.db = db
        self.timestamp = datetime.now(timezone.utc)
    
    async def get_stock_value_from_movements(self) -> Dict:
        """
        Calculate stock value from stock_movements
        Exclude anomaly data (value > 1 Billion per transaction)
        """
        pipeline = [
            {"$addFields": {
                "unit_cost": {"$ifNull": ["$cost_per_unit", {"$ifNull": ["$cost_price", 0]}]}
            }},
            {"$addFields": {
                "value": {"$multiply": ["$quantity", "$unit_cost"]}
            }},
            # Exclude anomalies
            {"$match": {
                "$expr": {"$lt": [{"$abs": "$value"}, 1000000000]}  # < 1 Billion
            }},
            {"$group": {
                "_id": "$movement_type",
                "total_qty": {"$sum": "$quantity"},
                "total_value": {"$sum": "$value"},
                "count": {"$sum": 1}
            }}
        ]
        
        by_type = await self.db["stock_movements"].aggregate(pipeline).to_list(None)
        
        # Categorize in vs out
        stock_in_types = ['stock_in', 'purchase_in', 'opname_in', 'in', 'initial_stock', 
                         'OPENING_BALANCE', 'adjustment', 'ADJUSTMENT_PLUS', 'receive',
                         'transfer_in', 'quick_purchase', 'purchase', 'sales_return_in']
        stock_out_types = ['stock_out', 'sale', 'sales_out', 'opname_out', 'out', 
                          'reversal', 'adjustment_out', 'ADJUSTMENT_MINUS', 'transfer_out',
                          'stock_reversal', 'purchase_return']
        
        in_value = 0
        out_value = 0
        details = []
        
        for t in by_type:
            mv_type = t['_id'] or 'unknown'
            qty = t['total_qty'] or 0
            val = t['total_value'] or 0
            
            if mv_type in stock_in_types:
                in_value += val
                direction = "IN"
            elif mv_type in stock_out_types:
                out_value += abs(val)
                direction = "OUT"
            else:
                direction = "?"
            
            if abs(val) > 0:
                details.append({
                    "type": mv_type,
                    "direction": direction,
                    "qty": qty,
                    "value": val,
                    "count": t['count']
                })
        
        net_value = in_value - out_value
        
        return {
            "source": "stock_movements",
            "stock_in_value": in_value,
            "stock_out_value": out_value,
            "net_stock_value": net_value,
            "details": sorted(details, key=lambda x: -abs(x['value']))
        }
    
    async def get_persediaan_balance_from_journal(self) -> Dict:
        """
        Get persediaan balance from journal entries
        Prioritize 'entries' field, fallback to 'lines' if entries is empty
        """
        total_debit = 0
        total_credit = 0
        account_details = []
        processed_journal_ids = set()
        
        # Check 'entries' field first (primary)
        pipeline_entries = [
            {"$match": {"entries": {"$exists": True, "$ne": []}}},
            {"$unwind": "$entries"},
            {"$match": {
                "$or": [
                    {"entries.account_code": {"$in": PERSEDIAAN_ACCOUNT_CODES}},
                    {"entries.account_name": {"$regex": "persediaan", "$options": "i"}}
                ]
            }},
            {"$group": {
                "_id": {
                    "code": "$entries.account_code",
                    "name": "$entries.account_name"
                },
                "total_debit": {"$sum": {"$ifNull": ["$entries.debit", 0]}},
                "total_credit": {"$sum": {"$ifNull": ["$entries.credit", 0]}},
                "journal_ids": {"$addToSet": "$id"},
                "count": {"$sum": 1}
            }}
        ]
        
        entries_result = await self.db["journal_entries"].aggregate(pipeline_entries).to_list(None)
        
        for r in entries_result:
            debit = r['total_debit'] or 0
            credit = r['total_credit'] or 0
            total_debit += debit
            total_credit += credit
            for jid in r.get('journal_ids', []):
                processed_journal_ids.add(jid)
            account_details.append({
                "source": "entries",
                "account_code": r['_id']['code'],
                "account_name": r['_id']['name'],
                "debit": debit,
                "credit": credit,
                "balance": debit - credit,
                "count": r['count']
            })
        
        # Check 'lines' field ONLY for journals that don't have entries
        pipeline_lines = [
            {"$match": {
                "$or": [
                    {"entries": {"$exists": False}},
                    {"entries": []},
                    {"entries": None}
                ]
            }},
            {"$unwind": "$lines"},
            {"$match": {
                "$or": [
                    {"lines.account_code": {"$in": PERSEDIAAN_ACCOUNT_CODES}},
                    {"lines.account_name": {"$regex": "persediaan", "$options": "i"}}
                ]
            }},
            {"$group": {
                "_id": {
                    "code": "$lines.account_code",
                    "name": "$lines.account_name"
                },
                "total_debit": {"$sum": {"$ifNull": ["$lines.debit", 0]}},
                "total_credit": {"$sum": {"$ifNull": ["$lines.credit", 0]}},
                "count": {"$sum": 1}
            }}
        ]
        
        lines_result = await self.db["journal_entries"].aggregate(pipeline_lines).to_list(None)
        
        for r in lines_result:
            debit = r['total_debit'] or 0
            credit = r['total_credit'] or 0
            total_debit += debit
            total_credit += credit
            account_details.append({
                "source": "lines",
                "account_code": r['_id']['code'],
                "account_name": r['_id']['name'],
                "debit": debit,
                "credit": credit,
                "balance": debit - credit,
                "count": r['count']
            })
        
        return {
            "source": "journal_entries",
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balance": total_debit - total_credit,
            "account_details": account_details
        }
    
    async def find_movements_without_journal(self) -> List[Dict]:
        """
        Find stock movements that don't have corresponding journal entries
        """
        movements = await self.db["stock_movements"].aggregate([
            {"$addFields": {
                "unit_cost": {"$ifNull": ["$cost_per_unit", {"$ifNull": ["$cost_price", 0]}]}
            }},
            {"$addFields": {
                "value": {"$multiply": [{"$abs": "$quantity"}, "$unit_cost"]}
            }},
            {"$match": {
                "value": {"$gt": 0, "$lt": 1000000000}
            }},
            {"$sort": {"created_at": -1}},
            {"$limit": 200}
        ]).to_list(200)
        
        missing_journals = []
        
        for m in movements:
            ref_id = m.get('reference_id')
            ref_number = m.get('reference_number', m.get('reference_no', ''))
            value = m['value']
            
            # Try to find matching journal with persediaan impact
            journal = None
            if ref_id:
                journal = await self.db["journal_entries"].find_one({
                    "$and": [
                        {"$or": [
                            {"reference_id": ref_id},
                            {"description": {"$regex": ref_number if ref_number else "xxx"}}
                        ]},
                        {"$or": [
                            {"entries.account_code": {"$in": PERSEDIAAN_ACCOUNT_CODES}},
                            {"lines.account_code": {"$in": PERSEDIAAN_ACCOUNT_CODES}}
                        ]}
                    ]
                })
            
            if not journal:
                missing_journals.append({
                    "movement_id": str(m.get('id', ''))[:12],
                    "date": m.get('created_at'),
                    "type": m.get('movement_type'),
                    "reference_type": m.get('reference_type'),
                    "reference_number": ref_number or "N/A",
                    "product": m.get('product_name', '')[:30],
                    "qty": m.get('quantity'),
                    "cost": m['unit_cost'],
                    "value": value
                })
        
        return missing_journals
    
    async def find_journal_mismatch(self) -> List[Dict]:
        """
        Find movements where journal value doesn't match stock value
        """
        mismatches = []
        
        # Get movements with significant value
        movements = await self.db["stock_movements"].aggregate([
            {"$addFields": {
                "unit_cost": {"$ifNull": ["$cost_per_unit", {"$ifNull": ["$cost_price", 0]}]}
            }},
            {"$addFields": {
                "value": {"$multiply": ["$quantity", "$unit_cost"]}
            }},
            {"$match": {
                "value": {"$gt": 100000, "$lt": 1000000000}  # 100K - 1B
            }},
            {"$sort": {"value": -1}},
            {"$limit": 50}
        ]).to_list(50)
        
        for m in movements:
            ref_id = m.get('reference_id')
            ref_number = m.get('reference_number', m.get('reference_no', ''))
            stock_value = m['value']
            
            # Find matching journal
            journal = None
            if ref_id:
                journal = await self.db["journal_entries"].find_one({"reference_id": ref_id})
            if not journal and ref_number:
                journal = await self.db["journal_entries"].find_one({
                    "description": {"$regex": ref_number}
                })
            
            if journal:
                # Find persediaan entry in journal
                journal_value = 0
                for entry in journal.get('entries', []) + journal.get('lines', []):
                    if entry.get('account_code') in PERSEDIAAN_ACCOUNT_CODES or \
                       'persediaan' in entry.get('account_name', '').lower():
                        journal_value = entry.get('debit', 0) - entry.get('credit', 0)
                        break
                
                diff = abs(stock_value) - abs(journal_value)
                if abs(diff) > 1000:  # More than Rp 1,000 difference
                    mismatches.append({
                        "reference_number": ref_number,
                        "stock_value": stock_value,
                        "journal_value": journal_value,
                        "difference": diff,
                        "product": m.get('product_name', '')[:30]
                    })
        
        return sorted(mismatches, key=lambda x: -abs(x['difference']))
    
    async def reconcile(self) -> Dict:
        """
        Full reconciliation between inventory and accounting
        """
        stock = await self.get_stock_value_from_movements()
        journal = await self.get_persediaan_balance_from_journal()
        movements_without_journal = await self.find_movements_without_journal()
        journal_mismatches = await self.find_journal_mismatch()
        
        stock_value = stock['net_stock_value']
        journal_balance = journal['balance']
        gap = stock_value - journal_balance
        
        # Determine status
        if abs(gap) < 1000:
            status = "RECONCILED"
        elif abs(gap) < 100000:  # < 100K
            status = "MINOR_VARIANCE"
        elif abs(gap) < 1000000:  # < 1M
            status = "VARIANCE_WARNING"
        else:
            status = "MAJOR_VARIANCE"
        
        # Calculate missing journal impact
        missing_value = sum(m['value'] for m in movements_without_journal)
        mismatch_value = sum(m['difference'] for m in journal_mismatches)
        
        return {
            "reconciliation_id": f"INVAC-{self.timestamp.strftime('%Y%m%d_%H%M%S')}",
            "timestamp": self.timestamp.isoformat(),
            "tenant": self.db.name,
            "stock_valuation": stock,
            "journal_balance": journal,
            "gap_analysis": {
                "stock_value": stock_value,
                "journal_balance": journal_balance,
                "gap": gap,
                "status": status,
                "gap_explanation": {
                    "movements_without_journal_count": len(movements_without_journal),
                    "movements_without_journal_value": missing_value,
                    "journal_mismatch_count": len(journal_mismatches),
                    "journal_mismatch_value": mismatch_value,
                    "explained_gap": missing_value + mismatch_value,
                    "unexplained_gap": gap - (missing_value + mismatch_value)
                }
            },
            "issues": {
                "movements_without_journal": movements_without_journal[:20],
                "journal_mismatches": journal_mismatches[:20]
            },
            "recommendation": self._get_recommendation(gap, status, len(movements_without_journal))
        }
    
    def _get_recommendation(self, gap: float, status: str, missing_count: int) -> str:
        if status == "RECONCILED":
            return "✅ Tidak ada tindakan diperlukan. Stock dan Persediaan sudah SINKRON."
        
        recs = []
        if gap > 0:
            recs.append(f"Stock lebih besar dari Journal sebesar Rp {abs(gap):,.0f}")
            recs.append("Kemungkinan penyebab:")
            recs.append("- Stock movement tanpa journal entry")
            recs.append("- Quick Purchase tanpa jurnal persediaan")
        else:
            recs.append(f"Journal lebih besar dari Stock sebesar Rp {abs(gap):,.0f}")
            recs.append("Kemungkinan penyebab:")
            recs.append("- Journal persediaan tanpa stock movement")
            recs.append("- Duplikasi jurnal")
        
        if missing_count > 0:
            recs.append(f"\n⚠️ Ditemukan {missing_count} stock movement TANPA journal impact")
            recs.append("Tindakan: Buat jurnal koreksi untuk transaksi tersebut")
        
        return "\n".join(recs)


# ==================== API ENDPOINTS ====================

@router.get("/reconcile")
async def reconcile_inventory_accounting(
    user: dict = Depends(get_current_user)
):
    """
    P0: Full Inventory to Accounting Reconciliation
    
    Returns:
    - Stock value from movements
    - Persediaan balance from journals
    - GAP analysis
    - List of problematic transactions
    """
    db = get_db()
    reconciler = InventoryAccountingReconciliation(db)
    return await reconciler.reconcile()


@router.get("/stock-value")
async def get_stock_value(
    user: dict = Depends(get_current_user)
):
    """Get total stock value from stock_movements"""
    db = get_db()
    reconciler = InventoryAccountingReconciliation(db)
    return await reconciler.get_stock_value_from_movements()


@router.get("/persediaan-balance")
async def get_persediaan_balance(
    user: dict = Depends(get_current_user)
):
    """Get persediaan account balance from journals"""
    db = get_db()
    reconciler = InventoryAccountingReconciliation(db)
    return await reconciler.get_persediaan_balance_from_journal()


@router.get("/movements-without-journal")
async def get_movements_without_journal(
    user: dict = Depends(get_current_user)
):
    """Find stock movements without journal impact"""
    db = get_db()
    reconciler = InventoryAccountingReconciliation(db)
    movements = await reconciler.find_movements_without_journal()
    
    total_value = sum(m['value'] for m in movements)
    
    return {
        "count": len(movements),
        "total_value": total_value,
        "movements": movements
    }


@router.get("/journal-mismatches")
async def get_journal_mismatches(
    user: dict = Depends(get_current_user)
):
    """Find movements where journal value doesn't match stock value"""
    db = get_db()
    reconciler = InventoryAccountingReconciliation(db)
    mismatches = await reconciler.find_journal_mismatch()
    
    total_diff = sum(m['difference'] for m in mismatches)
    
    return {
        "count": len(mismatches),
        "total_difference": total_diff,
        "mismatches": mismatches
    }


@router.post("/create-adjustment-journal")
async def create_adjustment_journal(
    adjustment_value: float,
    description: str = "Jurnal Koreksi Persediaan",
    user: dict = Depends(get_current_user)
):
    """
    Create adjustment journal to fix GAP between inventory and accounting
    
    If adjustment_value > 0: DEBIT Persediaan, CREDIT Selisih Persediaan
    If adjustment_value < 0: DEBIT Selisih Persediaan, CREDIT Persediaan
    """
    if abs(adjustment_value) < 1:
        raise HTTPException(status_code=400, detail="Nilai adjustment terlalu kecil")
    
    db = get_db()
    
    # Get next journal number
    from database import get_next_sequence
    journal_number = await get_next_sequence("journal_adjustment")
    journal_id = str(uuid.uuid4())
    
    # Create journal entries
    if adjustment_value > 0:
        entries = [
            {
                "account_code": "1-1400",
                "account_name": "Persediaan Barang",
                "debit": abs(adjustment_value),
                "credit": 0,
                "description": "Koreksi kenaikan persediaan"
            },
            {
                "account_code": "8-9900",
                "account_name": "Selisih Persediaan",
                "debit": 0,
                "credit": abs(adjustment_value),
                "description": "Koreksi selisih persediaan"
            }
        ]
    else:
        entries = [
            {
                "account_code": "8-9900",
                "account_name": "Selisih Persediaan",
                "debit": abs(adjustment_value),
                "credit": 0,
                "description": "Koreksi selisih persediaan"
            },
            {
                "account_code": "1-1400",
                "account_name": "Persediaan Barang",
                "debit": 0,
                "credit": abs(adjustment_value),
                "description": "Koreksi penurunan persediaan"
            }
        ]
    
    journal = {
        "id": journal_id,
        "journal_number": f"JV-ADJ-{journal_number}",
        "journal_date": datetime.now(timezone.utc).isoformat(),
        "reference_type": "inventory_adjustment",
        "reference_id": None,
        "reference_number": f"ADJ-{datetime.now().strftime('%Y%m%d')}",
        "description": description,
        "entries": entries,
        "total_debit": abs(adjustment_value),
        "total_credit": abs(adjustment_value),
        "is_balanced": True,
        "status": "posted",
        "branch_id": user.get("branch_id"),
        "created_by": user.get("user_id"),
        "created_by_name": user.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db["journal_entries"].insert_one(journal)
    
    return {
        "success": True,
        "message": f"Jurnal koreksi berhasil dibuat: Rp {abs(adjustment_value):,.0f}",
        "journal_id": journal_id,
        "journal_number": journal["journal_number"]
    }
