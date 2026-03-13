"""
OCB TITAN AI - Journal Correction Script
=========================================
Buat reversal dan correcting journal untuk jurnal yang tidak balance

Sesuai MASTER BLUEPRINT:
- JANGAN EDIT POSTED JOURNAL LANGSUNG
- Perbaikan lewat reversal journal dan correcting journal
"""

import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

async def create_correction_journals():
    """Create reversal and correcting journals for imbalanced sales journals"""
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client["ocb_titan"]
    
    # The problematic journals and their missing entries
    # Based on analysis: Missing Debit Kas/Piutang entry
    problematic_journals = [
        {
            "journal_number": "JV-20260312-0006",
            "reference": "INV-20260312-0006",
            "missing_debit_amount": 4440000,  # 4,000,000 + 440,000 (Penjualan + PPN)
            "description": "Penjualan INV-20260312-0006"
        },
        {
            "journal_number": "JV-20260312-0007",
            "reference": "INV-20260312-0007",
            "missing_debit_amount": 4440000,
            "description": "Penjualan INV-20260312-0007"
        },
        {
            "journal_number": "JV-20260312-0008",
            "reference": "INV-20260312-0008",
            "missing_debit_amount": 2220000,  # 2,000,000 + 220,000
            "description": "Penjualan INV-20260312-0008"
        }
    ]
    
    now = datetime.now(timezone.utc).isoformat()
    corrections_created = []
    
    for prob in problematic_journals:
        # Get original journal
        original = await db.journal_entries.find_one(
            {"journal_number": prob["journal_number"]},
            {"_id": 0}
        )
        
        if not original:
            print(f"WARNING: Journal {prob['journal_number']} not found")
            continue
        
        print(f"\n{'='*60}")
        print(f"Processing: {prob['journal_number']}")
        
        # Create CORRECTING JOURNAL (add the missing debit entry)
        # This is better than reversal because the original journal
        # has valid entries, just incomplete
        
        correction_id = str(uuid.uuid4())
        correction_number = f"COR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        
        # The missing entry is Debit to Piutang Usaha (since these are sales)
        correction_entry = {
            "account_code": "1-1300",
            "account_name": "Piutang Usaha",
            "debit": prob["missing_debit_amount"],
            "credit": 0,
            "description": f"Koreksi entry yg hilang dari {prob['journal_number']}"
        }
        
        correction_journal = {
            "id": correction_id,
            "journal_number": correction_number,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "reference": f"CORRECTION-{prob['reference']}",
            "reference_type": "correction",
            "reference_id": original.get("id", prob["journal_number"]),
            "description": f"Koreksi jurnal tidak lengkap: {prob['description']} - Entry Piutang yg hilang",
            "lines": [correction_entry],
            "entries": [correction_entry],
            "total_debit": prob["missing_debit_amount"],
            "total_credit": 0,
            "status": "posted",  # Auto-post correction
            
            # Audit correction fields
            "correction_of_journal_id": original.get("id"),
            "correction_of_journal_number": prob["journal_number"],
            "correction_reason": f"Jurnal penjualan tidak memiliki entry Debit Piutang/Kas. Total Debit yg hilang: Rp {prob['missing_debit_amount']:,.0f}",
            "correction_method": "correcting_entry",
            "corrected_by": "system_audit",
            "corrected_at": now,
            
            "created_at": now,
            "created_by": "system_audit"
        }
        
        # Insert correction journal
        await db.journal_entries.insert_one(correction_journal)
        
        # Mark original journal as corrected (without editing it)
        await db.journal_entries.update_one(
            {"journal_number": prob["journal_number"]},
            {"$set": {
                "has_correction": True,
                "correction_journal_id": correction_id,
                "correction_journal_number": correction_number,
                "correction_note": "Entry Debit Piutang yg hilang ditambahkan via correcting journal"
            }}
        )
        
        corrections_created.append({
            "original": prob["journal_number"],
            "correction": correction_number,
            "amount": prob["missing_debit_amount"]
        })
        
        print(f"Created correction: {correction_number}")
        print(f"  Added: Debit Piutang Usaha Rp {prob['missing_debit_amount']:,.0f}")
    
    print(f"\n{'='*60}")
    print("CORRECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total corrections created: {len(corrections_created)}")
    
    for c in corrections_created:
        print(f"  {c['original']} -> {c['correction']} (Rp {c['amount']:,.0f})")
    
    # Verify balance after corrections
    print(f"\n{'='*60}")
    print("VERIFICATION AFTER CORRECTIONS")
    print(f"{'='*60}")
    
    # Recalculate trial balance
    pipeline = [
        {"$match": {"status": {"$in": ["posted", "POSTED"]}}},
        {"$unwind": {"path": "$lines", "preserveNullAndEmptyArrays": False}},
        {"$group": {
            "_id": None,
            "total_debit": {"$sum": {"$ifNull": ["$lines.debit", 0]}},
            "total_credit": {"$sum": {"$ifNull": ["$lines.credit", 0]}}
        }}
    ]
    
    result = await db.journal_entries.aggregate(pipeline).to_list(1)
    if result:
        r = result[0]
        print(f"Total Debit: Rp {r['total_debit']:,.0f}")
        print(f"Total Credit: Rp {r['total_credit']:,.0f}")
        print(f"Difference: Rp {r['total_debit'] - r['total_credit']:,.0f}")
        print(f"BALANCED: {abs(r['total_debit'] - r['total_credit']) < 1}")
    
    return corrections_created


async def verify_all_journals_balance():
    """Verify all journals are now balanced"""
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client["ocb_titan"]
    
    journals = await db.journal_entries.find({}, {"_id": 0}).to_list(10000)
    
    imbalanced = []
    for j in journals:
        lines = j.get("lines", []) or j.get("entries", [])
        total_d = sum(float(l.get("debit", 0) or 0) for l in lines)
        total_c = sum(float(l.get("credit", 0) or 0) for l in lines)
        diff = abs(total_d - total_c)
        
        if diff > 1:  # More than Rp 1 tolerance
            imbalanced.append({
                "journal_number": j.get("journal_number"),
                "difference": total_d - total_c
            })
    
    print(f"\n{'='*60}")
    print("JOURNAL BALANCE CHECK")
    print(f"{'='*60}")
    print(f"Total Journals: {len(journals)}")
    print(f"Imbalanced: {len(imbalanced)}")
    
    if imbalanced:
        print("\nStill imbalanced:")
        for i in imbalanced[:10]:
            print(f"  {i['journal_number']}: Diff={i['difference']:,.0f}")
    else:
        print("\n✓ ALL JOURNALS ARE NOW BALANCED!")
    
    return imbalanced


if __name__ == "__main__":
    print("="*60)
    print("OCB TITAN AI - JOURNAL CORRECTION")
    print("="*60)
    
    asyncio.run(create_correction_journals())
    asyncio.run(verify_all_journals_balance())
