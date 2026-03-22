# PT OCB GROUP AI - CASHFLOW & PAYMENT ENGINE
# P1: Enterprise Cash/Bank Full Integration
# RULE: No payment without cash/bank movement, no cash/bank movement without journal

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from database import db
from utils.auth import get_current_user
from routes.rbac_system import check_permission, log_activity
import uuid

router = APIRouter(prefix="/api/cashflow", tags=["Cashflow & Payment Engine"])

# ==================== COLLECTIONS ====================
cash_bank_ledger = db["cash_bank_ledger"]  # Single Source of Truth for Cash/Bank
ap_collection = db["accounts_payable"]
ar_collection = db["accounts_receivable"]
ap_payments = db["ap_payments"]
ar_payments = db["ar_payments"]
ap_allocations = db["ap_payment_allocations"]
ar_allocations = db["ar_payment_allocations"]
journal_entries = db["journal_entries"]
suppliers = db["suppliers"]
customers = db["customers"]
coa_collection = db["chart_of_accounts"]

# ==================== CONSTANTS ====================
TRANSACTION_TYPES = {
    "cash_in": {"name": "Kas Masuk", "direction": "in", "color": "green"},
    "cash_out": {"name": "Kas Keluar", "direction": "out", "color": "red"},
    "ap_payment": {"name": "Pembayaran Hutang", "direction": "out", "color": "orange"},
    "ar_receipt": {"name": "Penerimaan Piutang", "direction": "in", "color": "blue"},
    "bank_transfer": {"name": "Transfer Bank", "direction": "transfer", "color": "purple"},
    "bank_deposit": {"name": "Setor Bank", "direction": "out", "color": "indigo"},
    "bank_withdraw": {"name": "Tarik Bank", "direction": "in", "color": "cyan"},
    "expense": {"name": "Biaya Operasional", "direction": "out", "color": "pink"},
    "revenue": {"name": "Pendapatan Lain", "direction": "in", "color": "teal"},
    "adjustment": {"name": "Penyesuaian", "direction": "adjust", "color": "gray"},
    "opening_balance": {"name": "Saldo Awal", "direction": "in", "color": "amber"},
}

DEFAULT_ACCOUNTS = {
    "cash_account": {"code": "1-1100", "name": "Kas"},
    "bank_account": {"code": "1-1200", "name": "Bank"},
    "ap_account": {"code": "2-1100", "name": "Hutang Dagang"},
    "ar_account": {"code": "1-1300", "name": "Piutang Usaha"},
    "expense_account": {"code": "6-1000", "name": "Biaya Umum"},
    "revenue_account": {"code": "4-1000", "name": "Pendapatan Lain"},
    "discount_purchase": {"code": "4-3000", "name": "Potongan Pembelian"},
    "discount_sales": {"code": "5-3000", "name": "Potongan Penjualan"},
}

# ==================== PYDANTIC MODELS ====================

class CashBankLedgerEntry(BaseModel):
    """Single entry in cash/bank ledger"""
    transaction_date: str
    account_code: str  # Cash or Bank account code
    amount: float = Field(gt=0)
    transaction_type: str  # From TRANSACTION_TYPES
    direction: str = "in"  # in, out, transfer
    reference_type: str = ""  # ap_payment, ar_receipt, expense, etc
    reference_id: str = ""
    reference_no: str = ""
    description: str = ""
    counterparty_type: str = ""  # supplier, customer, employee, other
    counterparty_id: str = ""
    counterparty_name: str = ""
    branch_id: str = ""
    notes: str = ""

class APPaymentAllocation(BaseModel):
    """Allocation for multi-invoice AP payment"""
    invoice_id: str
    invoice_no: str
    allocated_amount: float = Field(gt=0)
    discount_amount: float = 0.0
    notes: str = ""

class APPaymentCreate(BaseModel):
    """Create AP Payment request"""
    supplier_id: str
    payment_date: str
    payment_method: str = "transfer"  # cash, transfer, giro
    account_code: str  # Cash or Bank account code to debit
    reference_no: str = ""
    notes: str = ""
    allocations: List[APPaymentAllocation]
    branch_id: str = ""

class ARReceiptAllocation(BaseModel):
    """Allocation for multi-invoice AR receipt"""
    invoice_id: str
    invoice_no: str
    allocated_amount: float = Field(gt=0)
    discount_amount: float = 0.0
    notes: str = ""

class ARReceiptCreate(BaseModel):
    """Create AR Receipt request"""
    customer_id: str
    receipt_date: str
    payment_method: str = "transfer"
    account_code: str  # Cash or Bank account to credit
    reference_no: str = ""
    notes: str = ""
    allocations: List[ARReceiptAllocation]
    branch_id: str = ""

class CashInCreate(BaseModel):
    """Generic cash/bank in transaction"""
    transaction_date: str
    account_code: str
    amount: float = Field(gt=0)
    description: str
    category: str = "revenue"  # revenue, other_income, refund, etc
    reference_no: str = ""
    counterparty_name: str = ""
    branch_id: str = ""
    notes: str = ""

class CashOutCreate(BaseModel):
    """Generic cash/bank out transaction"""
    transaction_date: str
    account_code: str
    amount: float = Field(gt=0)
    description: str
    category: str = "expense"  # expense, operational, utility, etc
    expense_account_code: str = ""  # For journal debit
    reference_no: str = ""
    counterparty_name: str = ""
    branch_id: str = ""
    notes: str = ""

class BankTransferCreate(BaseModel):
    """Inter-account transfer"""
    transfer_date: str
    from_account_code: str
    to_account_code: str
    amount: float = Field(gt=0)
    description: str = "Transfer antar rekening"
    reference_no: str = ""
    branch_id: str = ""
    notes: str = ""


# ==================== HELPER FUNCTIONS ====================

async def generate_transaction_number(prefix: str) -> str:
    """Generate unique transaction number"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    # Count existing transactions today
    count = await cash_bank_ledger.count_documents({
        "transaction_no": {"$regex": f"^{prefix}-{today}"}
    })
    
    return f"{prefix}-{today}-{str(count + 1).zfill(4)}"


async def get_account_info(account_code: str) -> Dict[str, Any]:
    """Get account info from COA"""
    account = await coa_collection.find_one(
        {"account_code": account_code}, 
        {"_id": 0}
    )
    if account:
        return {
            "code": account.get("account_code"),
            "name": account.get("account_name"),
            "type": account.get("account_type"),
            "category": account.get("category")
        }
    
    # Fallback to defaults
    for key, val in DEFAULT_ACCOUNTS.items():
        if val["code"] == account_code:
            return {"code": val["code"], "name": val["name"], "type": "asset", "category": "kas_bank"}
    
    return {"code": account_code, "name": f"Account {account_code}", "type": "unknown", "category": "unknown"}


async def create_journal_entry_auto(
    reference_type: str,
    reference_id: str,
    reference_no: str,
    description: str,
    entries: List[Dict],
    branch_id: str,
    user_id: str,
    user_name: str,
    transaction_date: str = None
) -> str:
    """Create balanced journal entry automatically"""
    today = datetime.now(timezone.utc)
    
    # Generate journal number
    jv_count = await journal_entries.count_documents({
        "journal_no": {"$regex": f"^JV-{today.strftime('%Y%m%d')}"}
    })
    journal_no = f"JV-{today.strftime('%Y%m%d')}-{str(jv_count + 1).zfill(4)}"
    
    total_debit = sum(e.get("debit", 0) for e in entries)
    total_credit = sum(e.get("credit", 0) for e in entries)
    
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(
            status_code=400, 
            detail=f"Journal tidak balanced: Debit={total_debit:,.0f}, Credit={total_credit:,.0f}"
        )
    
    journal = {
        "id": str(uuid.uuid4()),
        "journal_no": journal_no,
        "journal_number": journal_no,
        "journal_date": transaction_date or today.strftime("%Y-%m-%d"),
        "posted_at": today.isoformat(),
        "reference_type": reference_type,
        "reference_id": reference_id,
        "reference_no": reference_no,
        "memo": description,
        "description": description,
        "branch_id": branch_id,
        "entries": entries,
        "lines": entries,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": True,
        "status": "posted",
        "source": "cashflow_engine",
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": today.isoformat()
    }
    
    await journal_entries.insert_one(journal)
    return journal_no


async def record_cash_bank_ledger(
    transaction_no: str,
    transaction_date: str,
    account_code: str,
    amount: float,
    transaction_type: str,
    direction: str,
    reference_type: str,
    reference_id: str,
    reference_no: str,
    description: str,
    counterparty_type: str,
    counterparty_id: str,
    counterparty_name: str,
    branch_id: str,
    journal_no: str,
    user_id: str,
    user_name: str,
    notes: str = ""
) -> str:
    """
    Record entry in Cash/Bank Ledger
    This is the SINGLE SOURCE OF TRUTH for all cash/bank movements
    """
    account_info = await get_account_info(account_code)
    
    entry_id = str(uuid.uuid4())
    entry = {
        "id": entry_id,
        "transaction_no": transaction_no,
        "transaction_date": transaction_date,
        "account_code": account_code,
        "account_name": account_info.get("name", ""),
        "amount": amount,
        "transaction_type": transaction_type,
        "transaction_type_name": TRANSACTION_TYPES.get(transaction_type, {}).get("name", transaction_type),
        "direction": direction,  # in, out, transfer
        "debit": amount if direction == "in" else 0,
        "credit": amount if direction == "out" else 0,
        "reference_type": reference_type,
        "reference_id": reference_id,
        "reference_no": reference_no,
        "description": description,
        "counterparty_type": counterparty_type,
        "counterparty_id": counterparty_id,
        "counterparty_name": counterparty_name,
        "branch_id": branch_id,
        "journal_no": journal_no,
        "notes": notes,
        "is_voided": False,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await cash_bank_ledger.insert_one(entry)
    return entry_id


async def get_account_balance(account_code: str, as_of_date: str = None) -> Dict[str, float]:
    """Calculate account balance from ledger"""
    match_filter = {
        "account_code": account_code,
        "is_voided": {"$ne": True}
    }
    
    if as_of_date:
        match_filter["transaction_date"] = {"$lte": as_of_date}
    
    pipeline = [
        {"$match": match_filter},
        {"$group": {
            "_id": "$account_code",
            "total_debit": {"$sum": "$debit"},
            "total_credit": {"$sum": "$credit"},
            "transaction_count": {"$sum": 1}
        }}
    ]
    
    result = await cash_bank_ledger.aggregate(pipeline).to_list(1)
    
    if result:
        total_debit = result[0].get("total_debit", 0)
        total_credit = result[0].get("total_credit", 0)
        return {
            "account_code": account_code,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balance": total_debit - total_credit,  # Asset account: Debit - Credit
            "transaction_count": result[0].get("transaction_count", 0)
        }
    
    return {
        "account_code": account_code,
        "total_debit": 0,
        "total_credit": 0,
        "balance": 0,
        "transaction_count": 0
    }


# ==================== AP PAYMENT ENDPOINTS ====================

@router.post("/ap-payment/create")
async def create_ap_payment(
    data: APPaymentCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Create AP Payment with Cash/Bank Ledger integration
    
    ENTERPRISE RULE:
    1. Validate all invoice allocations
    2. Create Cash/Bank Ledger entry (CREDIT)
    3. Create Journal: Dr. Hutang Dagang, Cr. Kas/Bank
    4. Update invoice outstanding
    5. Full audit trail
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", user.get("full_name", ""))
    
    if not data.allocations:
        raise HTTPException(status_code=400, detail="Minimal 1 invoice harus dipilih untuk pembayaran")
    
    total_payment = sum(a.allocated_amount for a in data.allocations)
    total_discount = sum(a.discount_amount for a in data.allocations)
    
    if total_payment <= 0:
        raise HTTPException(status_code=400, detail="Total pembayaran harus lebih dari 0")
    
    # Validate supplier
    supplier = await suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    supplier_name = supplier.get("name", "Unknown")
    
    # Validate each invoice allocation
    for alloc in data.allocations:
        invoice = await ap_collection.find_one({"id": alloc.invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail=f"Invoice {alloc.invoice_no} tidak ditemukan")
        
        outstanding = invoice.get("outstanding_amount", invoice.get("amount", 0))
        if alloc.allocated_amount > outstanding + 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Alokasi {alloc.invoice_no} (Rp {alloc.allocated_amount:,.0f}) melebihi sisa hutang (Rp {outstanding:,.0f})"
            )
        
        if invoice.get("supplier_id") != data.supplier_id:
            raise HTTPException(status_code=400, detail=f"Invoice {alloc.invoice_no} bukan milik supplier yang dipilih")
    
    # Generate payment number
    payment_no = await generate_transaction_number("PAY-AP")
    payment_id = str(uuid.uuid4())
    branch_id = data.branch_id or user.get("branch_id", "")
    
    # Get account info
    payment_account = await get_account_info(data.account_code)
    ap_account = await get_account_info(DEFAULT_ACCOUNTS["ap_account"]["code"])
    
    # Step 1: Create Journal Entry
    journal_entries_list = [
        {
            "account_code": ap_account["code"],
            "account_name": ap_account["name"],
            "debit": total_payment + total_discount,
            "credit": 0,
            "description": f"Pembayaran Hutang - {supplier_name}"
        },
        {
            "account_code": payment_account["code"],
            "account_name": payment_account["name"],
            "debit": 0,
            "credit": total_payment,
            "description": f"Pembayaran Hutang - {supplier_name}"
        }
    ]
    
    if total_discount > 0:
        discount_account = await get_account_info(DEFAULT_ACCOUNTS["discount_purchase"]["code"])
        journal_entries_list.append({
            "account_code": discount_account["code"],
            "account_name": discount_account["name"],
            "debit": 0,
            "credit": total_discount,
            "description": f"Potongan Pembelian - {supplier_name}"
        })
    
    journal_no = await create_journal_entry_auto(
        reference_type="ap_payment",
        reference_id=payment_id,
        reference_no=payment_no,
        description=f"Pembayaran Hutang {payment_no} - {supplier_name}",
        entries=journal_entries_list,
        branch_id=branch_id,
        user_id=user_id,
        user_name=user_name,
        transaction_date=data.payment_date
    )
    
    # Step 2: Record Cash/Bank Ledger Entry
    ledger_id = await record_cash_bank_ledger(
        transaction_no=payment_no,
        transaction_date=data.payment_date,
        account_code=data.account_code,
        amount=total_payment,
        transaction_type="ap_payment",
        direction="out",
        reference_type="ap_payment",
        reference_id=payment_id,
        reference_no=payment_no,
        description=f"Pembayaran Hutang - {supplier_name}",
        counterparty_type="supplier",
        counterparty_id=data.supplier_id,
        counterparty_name=supplier_name,
        branch_id=branch_id,
        journal_no=journal_no,
        user_id=user_id,
        user_name=user_name,
        notes=data.notes
    )
    
    # Step 3: Create Payment Header
    payment_header = {
        "id": payment_id,
        "payment_no": payment_no,
        "payment_date": data.payment_date,
        "supplier_id": data.supplier_id,
        "supplier_name": supplier_name,
        "total_amount": total_payment,
        "discount_amount": total_discount,
        "net_amount": total_payment,
        "payment_method": data.payment_method,
        "account_code": data.account_code,
        "account_name": payment_account["name"],
        "reference_no": data.reference_no,
        "notes": data.notes,
        "branch_id": branch_id,
        "allocation_count": len(data.allocations),
        "status": "posted",
        "journal_no": journal_no,
        "ledger_id": ledger_id,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ap_payments.insert_one(payment_header)
    
    # Step 4: Create allocations and update invoices
    allocation_records = []
    for alloc in data.allocations:
        invoice = await ap_collection.find_one({"id": alloc.invoice_id}, {"_id": 0})
        
        allocation_record = {
            "id": str(uuid.uuid4()),
            "payment_header_id": payment_id,
            "payment_no": payment_no,
            "invoice_id": alloc.invoice_id,
            "invoice_no": alloc.invoice_no,
            "original_amount": invoice.get("original_amount", invoice.get("amount", 0)),
            "outstanding_before": invoice.get("outstanding_amount", invoice.get("amount", 0)),
            "allocated_amount": alloc.allocated_amount,
            "discount_amount": alloc.discount_amount,
            "outstanding_after": max(0, invoice.get("outstanding_amount", invoice.get("amount", 0)) - alloc.allocated_amount),
            "notes": alloc.notes,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        allocation_records.append(allocation_record)
        
        # Update invoice
        current_paid = invoice.get("paid_amount", 0)
        current_outstanding = invoice.get("outstanding_amount", invoice.get("amount", 0))
        new_paid = current_paid + alloc.allocated_amount
        new_outstanding = max(0, current_outstanding - alloc.allocated_amount)
        
        # Determine new status
        original_amount = invoice.get("original_amount", invoice.get("amount", 0))
        if new_outstanding <= 0:
            new_status = "paid"
        elif new_paid > 0:
            new_status = "partial"
        else:
            due_date = invoice.get("due_date", "")
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            new_status = "overdue" if due_date and due_date < today else "open"
        
        await ap_collection.update_one(
            {"id": alloc.invoice_id},
            {"$set": {
                "paid_amount": new_paid,
                "outstanding_amount": new_outstanding,
                "status": new_status,
                "last_payment_date": data.payment_date,
                "last_payment_no": payment_no,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    if allocation_records:
        await ap_allocations.insert_many(allocation_records)
    
    # Audit log
    await log_activity(
        db, user_id, user_name,
        "create", "ap_payment",
        f"Pembayaran Hutang {payment_no} ke {supplier_name}, Rp {total_payment:,.0f}, {len(data.allocations)} invoice",
        request.client.host if request.client else "",
        branch_id
    )
    
    return {
        "status": "success",
        "message": "Pembayaran hutang berhasil dibuat",
        "payment_no": payment_no,
        "payment_id": payment_id,
        "journal_no": journal_no,
        "total_amount": total_payment,
        "discount_amount": total_discount,
        "allocation_count": len(data.allocations),
        "allocations": [
            {
                "invoice_no": a.invoice_no, 
                "amount": a.allocated_amount,
                "discount": a.discount_amount
            }
            for a in data.allocations
        ]
    }


# ==================== AR RECEIPT ENDPOINTS ====================

@router.post("/ar-receipt/create")
async def create_ar_receipt(
    data: ARReceiptCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Create AR Receipt with Cash/Bank Ledger integration
    
    ENTERPRISE RULE:
    1. Validate all invoice allocations
    2. Create Cash/Bank Ledger entry (DEBIT)
    3. Create Journal: Dr. Kas/Bank, Cr. Piutang Usaha
    4. Update invoice outstanding
    5. Full audit trail
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", user.get("full_name", ""))
    
    if not data.allocations:
        raise HTTPException(status_code=400, detail="Minimal 1 invoice harus dipilih untuk penerimaan")
    
    total_receipt = sum(a.allocated_amount for a in data.allocations)
    total_discount = sum(a.discount_amount for a in data.allocations)
    
    if total_receipt <= 0:
        raise HTTPException(status_code=400, detail="Total penerimaan harus lebih dari 0")
    
    # Validate customer
    customer = await customers.find_one({"id": data.customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    customer_name = customer.get("name", "Unknown")
    
    # Validate each invoice allocation
    for alloc in data.allocations:
        invoice = await ar_collection.find_one({"id": alloc.invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail=f"Invoice {alloc.invoice_no} tidak ditemukan")
        
        outstanding = invoice.get("outstanding_amount", invoice.get("amount", 0))
        if alloc.allocated_amount > outstanding + 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Alokasi {alloc.invoice_no} (Rp {alloc.allocated_amount:,.0f}) melebihi sisa piutang (Rp {outstanding:,.0f})"
            )
    
    # Generate receipt number
    receipt_no = await generate_transaction_number("RCV-AR")
    receipt_id = str(uuid.uuid4())
    branch_id = data.branch_id or user.get("branch_id", "")
    
    # Get account info
    receipt_account = await get_account_info(data.account_code)
    ar_account = await get_account_info(DEFAULT_ACCOUNTS["ar_account"]["code"])
    
    # Step 1: Create Journal Entry
    journal_entries_list = [
        {
            "account_code": receipt_account["code"],
            "account_name": receipt_account["name"],
            "debit": total_receipt,
            "credit": 0,
            "description": f"Penerimaan Piutang - {customer_name}"
        },
        {
            "account_code": ar_account["code"],
            "account_name": ar_account["name"],
            "debit": 0,
            "credit": total_receipt + total_discount,
            "description": f"Penerimaan Piutang - {customer_name}"
        }
    ]
    
    if total_discount > 0:
        discount_account = await get_account_info(DEFAULT_ACCOUNTS["discount_sales"]["code"])
        journal_entries_list.append({
            "account_code": discount_account["code"],
            "account_name": discount_account["name"],
            "debit": total_discount,
            "credit": 0,
            "description": f"Potongan Penjualan - {customer_name}"
        })
    
    journal_no = await create_journal_entry_auto(
        reference_type="ar_receipt",
        reference_id=receipt_id,
        reference_no=receipt_no,
        description=f"Penerimaan Piutang {receipt_no} - {customer_name}",
        entries=journal_entries_list,
        branch_id=branch_id,
        user_id=user_id,
        user_name=user_name,
        transaction_date=data.receipt_date
    )
    
    # Step 2: Record Cash/Bank Ledger Entry
    ledger_id = await record_cash_bank_ledger(
        transaction_no=receipt_no,
        transaction_date=data.receipt_date,
        account_code=data.account_code,
        amount=total_receipt,
        transaction_type="ar_receipt",
        direction="in",
        reference_type="ar_receipt",
        reference_id=receipt_id,
        reference_no=receipt_no,
        description=f"Penerimaan Piutang - {customer_name}",
        counterparty_type="customer",
        counterparty_id=data.customer_id,
        counterparty_name=customer_name,
        branch_id=branch_id,
        journal_no=journal_no,
        user_id=user_id,
        user_name=user_name,
        notes=data.notes
    )
    
    # Step 3: Create Receipt Header
    receipt_header = {
        "id": receipt_id,
        "receipt_no": receipt_no,
        "receipt_date": data.receipt_date,
        "customer_id": data.customer_id,
        "customer_name": customer_name,
        "total_amount": total_receipt,
        "discount_amount": total_discount,
        "net_amount": total_receipt,
        "payment_method": data.payment_method,
        "account_code": data.account_code,
        "account_name": receipt_account["name"],
        "reference_no": data.reference_no,
        "notes": data.notes,
        "branch_id": branch_id,
        "allocation_count": len(data.allocations),
        "status": "posted",
        "journal_no": journal_no,
        "ledger_id": ledger_id,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ar_payments.insert_one(receipt_header)
    
    # Step 4: Create allocations and update invoices
    allocation_records = []
    for alloc in data.allocations:
        invoice = await ar_collection.find_one({"id": alloc.invoice_id}, {"_id": 0})
        
        allocation_record = {
            "id": str(uuid.uuid4()),
            "payment_header_id": receipt_id,
            "receipt_no": receipt_no,
            "invoice_id": alloc.invoice_id,
            "invoice_no": alloc.invoice_no,
            "original_amount": invoice.get("original_amount", invoice.get("amount", 0)),
            "outstanding_before": invoice.get("outstanding_amount", invoice.get("amount", 0)),
            "allocated_amount": alloc.allocated_amount,
            "discount_amount": alloc.discount_amount,
            "outstanding_after": max(0, invoice.get("outstanding_amount", invoice.get("amount", 0)) - alloc.allocated_amount),
            "notes": alloc.notes,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        allocation_records.append(allocation_record)
        
        # Update invoice
        current_paid = invoice.get("paid_amount", 0)
        current_outstanding = invoice.get("outstanding_amount", invoice.get("amount", 0))
        new_paid = current_paid + alloc.allocated_amount
        new_outstanding = max(0, current_outstanding - alloc.allocated_amount)
        
        # Determine new status
        if new_outstanding <= 0:
            new_status = "paid"
        elif new_paid > 0:
            new_status = "partial"
        else:
            due_date = invoice.get("due_date", "")
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            new_status = "overdue" if due_date and due_date < today else "open"
        
        await ar_collection.update_one(
            {"id": alloc.invoice_id},
            {"$set": {
                "paid_amount": new_paid,
                "outstanding_amount": new_outstanding,
                "status": new_status,
                "last_payment_date": data.receipt_date,
                "last_receipt_no": receipt_no,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    if allocation_records:
        await ar_allocations.insert_many(allocation_records)
    
    # Audit log
    await log_activity(
        db, user_id, user_name,
        "create", "ar_receipt",
        f"Penerimaan Piutang {receipt_no} dari {customer_name}, Rp {total_receipt:,.0f}, {len(data.allocations)} invoice",
        request.client.host if request.client else "",
        branch_id
    )
    
    return {
        "status": "success",
        "message": "Penerimaan piutang berhasil dibuat",
        "receipt_no": receipt_no,
        "receipt_id": receipt_id,
        "journal_no": journal_no,
        "total_amount": total_receipt,
        "discount_amount": total_discount,
        "allocation_count": len(data.allocations)
    }


# ==================== CASH IN/OUT ENDPOINTS ====================

@router.post("/cash-in/create")
async def create_cash_in(
    data: CashInCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create generic cash/bank in transaction with journal"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", user.get("full_name", ""))
    branch_id = data.branch_id or user.get("branch_id", "")
    
    # Generate transaction number
    transaction_no = await generate_transaction_number("KM")  # Kas Masuk
    transaction_id = str(uuid.uuid4())
    
    # Get account info
    cash_account = await get_account_info(data.account_code)
    revenue_account = await get_account_info(DEFAULT_ACCOUNTS["revenue_account"]["code"])
    
    # Create Journal: Dr. Kas/Bank, Cr. Pendapatan
    journal_entries_list = [
        {
            "account_code": cash_account["code"],
            "account_name": cash_account["name"],
            "debit": data.amount,
            "credit": 0,
            "description": data.description
        },
        {
            "account_code": revenue_account["code"],
            "account_name": revenue_account["name"],
            "debit": 0,
            "credit": data.amount,
            "description": data.description
        }
    ]
    
    journal_no = await create_journal_entry_auto(
        reference_type="cash_in",
        reference_id=transaction_id,
        reference_no=transaction_no,
        description=f"Kas Masuk {transaction_no} - {data.description}",
        entries=journal_entries_list,
        branch_id=branch_id,
        user_id=user_id,
        user_name=user_name,
        transaction_date=data.transaction_date
    )
    
    # Record to ledger
    ledger_id = await record_cash_bank_ledger(
        transaction_no=transaction_no,
        transaction_date=data.transaction_date,
        account_code=data.account_code,
        amount=data.amount,
        transaction_type="cash_in",
        direction="in",
        reference_type="cash_in",
        reference_id=transaction_id,
        reference_no=transaction_no,
        description=data.description,
        counterparty_type="other",
        counterparty_id="",
        counterparty_name=data.counterparty_name,
        branch_id=branch_id,
        journal_no=journal_no,
        user_id=user_id,
        user_name=user_name,
        notes=data.notes
    )
    
    return {
        "status": "success",
        "message": "Kas masuk berhasil dicatat",
        "transaction_no": transaction_no,
        "journal_no": journal_no,
        "amount": data.amount
    }


@router.post("/cash-out/create")
async def create_cash_out(
    data: CashOutCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create generic cash/bank out transaction with journal"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", user.get("full_name", ""))
    branch_id = data.branch_id or user.get("branch_id", "")
    
    # Generate transaction number
    transaction_no = await generate_transaction_number("KK")  # Kas Keluar
    transaction_id = str(uuid.uuid4())
    
    # Get account info
    cash_account = await get_account_info(data.account_code)
    expense_code = data.expense_account_code or DEFAULT_ACCOUNTS["expense_account"]["code"]
    expense_account = await get_account_info(expense_code)
    
    # Create Journal: Dr. Biaya, Cr. Kas/Bank
    journal_entries_list = [
        {
            "account_code": expense_account["code"],
            "account_name": expense_account["name"],
            "debit": data.amount,
            "credit": 0,
            "description": data.description
        },
        {
            "account_code": cash_account["code"],
            "account_name": cash_account["name"],
            "debit": 0,
            "credit": data.amount,
            "description": data.description
        }
    ]
    
    journal_no = await create_journal_entry_auto(
        reference_type="cash_out",
        reference_id=transaction_id,
        reference_no=transaction_no,
        description=f"Kas Keluar {transaction_no} - {data.description}",
        entries=journal_entries_list,
        branch_id=branch_id,
        user_id=user_id,
        user_name=user_name,
        transaction_date=data.transaction_date
    )
    
    # Record to ledger
    ledger_id = await record_cash_bank_ledger(
        transaction_no=transaction_no,
        transaction_date=data.transaction_date,
        account_code=data.account_code,
        amount=data.amount,
        transaction_type="cash_out",
        direction="out",
        reference_type="cash_out",
        reference_id=transaction_id,
        reference_no=transaction_no,
        description=data.description,
        counterparty_type="other",
        counterparty_id="",
        counterparty_name=data.counterparty_name,
        branch_id=branch_id,
        journal_no=journal_no,
        user_id=user_id,
        user_name=user_name,
        notes=data.notes
    )
    
    return {
        "status": "success",
        "message": "Kas keluar berhasil dicatat",
        "transaction_no": transaction_no,
        "journal_no": journal_no,
        "amount": data.amount
    }


@router.post("/bank-transfer/create")
async def create_bank_transfer(
    data: BankTransferCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create inter-account transfer with journal"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", user.get("full_name", ""))
    branch_id = data.branch_id or user.get("branch_id", "")
    
    if data.from_account_code == data.to_account_code:
        raise HTTPException(status_code=400, detail="Akun asal dan tujuan tidak boleh sama")
    
    # Generate transaction number
    transaction_no = await generate_transaction_number("TRF")
    transaction_id = str(uuid.uuid4())
    
    # Get account info
    from_account = await get_account_info(data.from_account_code)
    to_account = await get_account_info(data.to_account_code)
    
    # Create Journal: Dr. To Account, Cr. From Account
    journal_entries_list = [
        {
            "account_code": to_account["code"],
            "account_name": to_account["name"],
            "debit": data.amount,
            "credit": 0,
            "description": data.description
        },
        {
            "account_code": from_account["code"],
            "account_name": from_account["name"],
            "debit": 0,
            "credit": data.amount,
            "description": data.description
        }
    ]
    
    journal_no = await create_journal_entry_auto(
        reference_type="bank_transfer",
        reference_id=transaction_id,
        reference_no=transaction_no,
        description=f"Transfer {transaction_no} - {from_account['name']} ke {to_account['name']}",
        entries=journal_entries_list,
        branch_id=branch_id,
        user_id=user_id,
        user_name=user_name,
        transaction_date=data.transfer_date
    )
    
    # Record OUT from source account
    await record_cash_bank_ledger(
        transaction_no=transaction_no,
        transaction_date=data.transfer_date,
        account_code=data.from_account_code,
        amount=data.amount,
        transaction_type="bank_transfer",
        direction="out",
        reference_type="bank_transfer",
        reference_id=transaction_id,
        reference_no=transaction_no,
        description=f"Transfer ke {to_account['name']}",
        counterparty_type="internal",
        counterparty_id=data.to_account_code,
        counterparty_name=to_account["name"],
        branch_id=branch_id,
        journal_no=journal_no,
        user_id=user_id,
        user_name=user_name,
        notes=data.notes
    )
    
    # Record IN to destination account
    await record_cash_bank_ledger(
        transaction_no=transaction_no,
        transaction_date=data.transfer_date,
        account_code=data.to_account_code,
        amount=data.amount,
        transaction_type="bank_transfer",
        direction="in",
        reference_type="bank_transfer",
        reference_id=transaction_id,
        reference_no=transaction_no,
        description=f"Transfer dari {from_account['name']}",
        counterparty_type="internal",
        counterparty_id=data.from_account_code,
        counterparty_name=from_account["name"],
        branch_id=branch_id,
        journal_no=journal_no,
        user_id=user_id,
        user_name=user_name,
        notes=data.notes
    )
    
    return {
        "status": "success",
        "message": "Transfer berhasil dicatat",
        "transaction_no": transaction_no,
        "journal_no": journal_no,
        "amount": data.amount,
        "from_account": from_account["name"],
        "to_account": to_account["name"]
    }


# ==================== QUERY ENDPOINTS ====================

@router.get("/ledger")
async def get_cash_bank_ledger(
    account_code: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    transaction_type: str = Query(None),
    branch_id: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    user: dict = Depends(get_current_user)
):
    """Get cash/bank ledger entries with filters"""
    query = {"is_voided": {"$ne": True}}
    
    if account_code:
        query["account_code"] = account_code
    if transaction_type:
        query["transaction_type"] = transaction_type
    if branch_id:
        query["branch_id"] = branch_id
    if start_date:
        query["transaction_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("transaction_date", {})["$lte"] = end_date
    
    skip = (page - 1) * limit
    
    entries = await cash_bank_ledger.find(
        query, {"_id": 0}
    ).sort("transaction_date", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await cash_bank_ledger.count_documents(query)
    
    # Calculate running balance
    running_balance = 0
    for entry in reversed(entries):
        if entry.get("direction") == "in":
            running_balance += entry.get("amount", 0)
        else:
            running_balance -= entry.get("amount", 0)
        entry["running_balance"] = running_balance
    
    return {
        "items": entries,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/accounts")
async def get_cash_bank_accounts(user: dict = Depends(get_current_user)):
    """Get list of cash/bank accounts with balances"""
    # Get kas/bank accounts from COA - support multiple field patterns
    accounts = await coa_collection.find(
        {
            "$and": [
                {"is_active": {"$ne": False}},
                {"$or": [
                    {"category": "kas_bank"},
                    {"category": "current_asset", "sub_type": {"$in": ["cash", "bank"]}},
                    {"code": {"$regex": "^110[1-9]"}},  # 110x codes (detail accounts)
                    {"code": {"$regex": "^1-100[1-9]"}},  # 1-100x codes
                    {"sub_type": {"$in": ["cash", "bank"]}},
                    {"type": "asset", "sub_type": {"$in": ["cash", "bank"]}}
                ]},
                # Exclude header accounts (type H)
                {"$or": [
                    {"type": {"$ne": "H"}},
                    {"type": {"$exists": False}}
                ]}
            ]
        },
        {"_id": 0}
    ).to_list(20)
    
    # Calculate balance for each account
    result = []
    seen_codes = set()
    for acc in accounts:
        # Support both account_code and code fields
        acc_code = acc.get("account_code") or acc.get("code")
        acc_name = acc.get("account_name") or acc.get("name")
        
        # Skip duplicates and header accounts
        if not acc_code or acc_code in seen_codes:
            continue
        seen_codes.add(acc_code)
        
        balance_info = await get_account_balance(acc_code)
        result.append({
            "account_code": acc_code,
            "account_name": acc_name,
            "account_type": acc.get("sub_type") or acc.get("account_type") or acc.get("type", "kas"),
            "balance": balance_info.get("balance", 0),
            "total_debit": balance_info.get("total_debit", 0),
            "total_credit": balance_info.get("total_credit", 0),
            "transaction_count": balance_info.get("transaction_count", 0)
        })
    
    return {
        "accounts": result,
        "total_balance": sum(a.get("balance", 0) for a in result)
    }


@router.get("/balance/{account_code}")
async def get_account_balance_api(
    account_code: str,
    as_of_date: str = Query(None),
    user: dict = Depends(get_current_user)
):
    """Get balance for specific cash/bank account"""
    balance = await get_account_balance(account_code, as_of_date)
    account_info = await get_account_info(account_code)
    
    return {
        **balance,
        "account_name": account_info.get("name", "")
    }


# ==================== RECONCILIATION ENDPOINTS ====================

@router.get("/reconciliation")
async def get_cashflow_reconciliation(
    account_code: str = Query(None),
    as_of_date: str = Query(None),
    user: dict = Depends(get_current_user)
):
    """
    Reconciliation check between:
    1. Cash/Bank Ledger
    2. Journal Balance
    3. AP/AR Outstanding
    """
    as_of = as_of_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get ledger balance
    ledger_balance = await get_account_balance(account_code, as_of) if account_code else {}
    
    # Get journal balance for the account
    journal_pipeline = [
        {"$unwind": "$entries"},
        {"$match": {
            "journal_date": {"$lte": as_of},
            "status": "posted"
        }}
    ]
    
    if account_code:
        journal_pipeline[1]["$match"]["entries.account_code"] = account_code
    
    journal_pipeline.extend([
        {"$group": {
            "_id": "$entries.account_code",
            "total_debit": {"$sum": "$entries.debit"},
            "total_credit": {"$sum": "$entries.credit"}
        }}
    ])
    
    journal_result = await journal_entries.aggregate(journal_pipeline).to_list(100)
    
    # Get total AP outstanding
    ap_outstanding = await ap_collection.aggregate([
        {"$match": {"status": {"$in": ["open", "partial", "overdue"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$outstanding_amount"}}}
    ]).to_list(1)
    
    # Get total AR outstanding
    ar_outstanding = await ar_collection.aggregate([
        {"$match": {"status": {"$in": ["open", "partial", "overdue"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$outstanding_amount"}}}
    ]).to_list(1)
    
    return {
        "as_of_date": as_of,
        "cash_bank_ledger": {
            "account_code": account_code,
            "balance": ledger_balance.get("balance", 0),
            "total_debit": ledger_balance.get("total_debit", 0),
            "total_credit": ledger_balance.get("total_credit", 0)
        },
        "journal_balance": {
            "accounts": [
                {
                    "account_code": r["_id"],
                    "balance": r["total_debit"] - r["total_credit"]
                }
                for r in journal_result
            ]
        },
        "ap_outstanding": ap_outstanding[0]["total"] if ap_outstanding else 0,
        "ar_outstanding": ar_outstanding[0]["total"] if ar_outstanding else 0,
        "reconciliation_status": "OK" if abs(ledger_balance.get("balance", 0) - sum(
            r["total_debit"] - r["total_credit"] for r in journal_result if account_code and r["_id"] == account_code
        )) < 1 else "MISMATCH"
    }


@router.get("/summary")
async def get_cashflow_summary(
    start_date: str = Query(None),
    end_date: str = Query(None),
    branch_id: str = Query(None),
    user: dict = Depends(get_current_user)
):
    """Get cashflow summary by transaction type"""
    today = datetime.now(timezone.utc)
    start = start_date or today.replace(day=1).strftime("%Y-%m-%d")
    end = end_date or today.strftime("%Y-%m-%d")
    
    match_filter = {
        "transaction_date": {"$gte": start, "$lte": end},
        "is_voided": {"$ne": True}
    }
    
    if branch_id:
        match_filter["branch_id"] = branch_id
    
    pipeline = [
        {"$match": match_filter},
        {"$group": {
            "_id": {
                "type": "$transaction_type",
                "direction": "$direction"
            },
            "total_amount": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.direction": 1}}
    ]
    
    results = await cash_bank_ledger.aggregate(pipeline).to_list(50)
    
    total_in = 0
    total_out = 0
    by_type = {}
    
    for r in results:
        type_key = r["_id"]["type"]
        direction = r["_id"]["direction"]
        amount = r["total_amount"]
        
        if direction == "in":
            total_in += amount
        elif direction == "out":
            total_out += amount
        
        if type_key not in by_type:
            by_type[type_key] = {
                "name": TRANSACTION_TYPES.get(type_key, {}).get("name", type_key),
                "in": 0,
                "out": 0,
                "count": 0
            }
        
        if direction == "in":
            by_type[type_key]["in"] += amount
        else:
            by_type[type_key]["out"] += amount
        by_type[type_key]["count"] += r["count"]
    
    return {
        "period": {"start": start, "end": end},
        "total_cash_in": total_in,
        "total_cash_out": total_out,
        "net_cashflow": total_in - total_out,
        "by_transaction_type": list(by_type.values())
    }
