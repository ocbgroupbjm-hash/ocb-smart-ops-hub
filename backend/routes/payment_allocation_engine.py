# OCB TITAN ERP - AP/AR PAYMENT ALLOCATION ENGINE
# Enterprise Payment Structure: payment_header + payment_allocation
# Supports multi-invoice payment dengan proper allocation tracking

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import db
from utils.auth import get_current_user
from routes.rbac_system import check_permission, log_activity
import uuid

router = APIRouter(prefix="/api/payment-allocation", tags=["Payment Allocation Engine"])

# Collections
ap_collection = db["accounts_payable"]
ar_collection = db["accounts_receivable"]
ap_payments = db["ap_payments"]
ar_payments = db["ar_payments"]
ap_allocations = db["ap_payment_allocations"]
ar_allocations = db["ar_payment_allocations"]
journal_entries = db["journal_entries"]
suppliers = db["suppliers"]
customers = db["customers"]

# ==================== PYDANTIC MODELS ====================

class AllocationItem(BaseModel):
    invoice_id: str
    invoice_no: str
    allocated_amount: float
    discount_amount: float = 0.0
    notes: Optional[str] = None

class APPaymentRequest(BaseModel):
    """Multi-invoice AP Payment request"""
    supplier_id: str
    payment_date: str
    payment_method: str = "transfer"  # cash, transfer, giro
    bank_account_id: Optional[str] = None
    bank_account_code: Optional[str] = None
    reference_no: Optional[str] = None
    notes: Optional[str] = None
    allocations: List[AllocationItem]  # Multi-invoice allocations
    branch_id: Optional[str] = None

class ARPaymentRequest(BaseModel):
    """Multi-invoice AR Payment request"""
    customer_id: str
    payment_date: str
    payment_method: str = "transfer"
    bank_account_id: Optional[str] = None
    bank_account_code: Optional[str] = None
    reference_no: Optional[str] = None
    notes: Optional[str] = None
    allocations: List[AllocationItem]
    branch_id: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

async def generate_payment_number(prefix: str) -> str:
    """Generate unique payment number"""
    from utils.number_generator import generate_transaction_number
    return await generate_transaction_number(db, prefix)


async def derive_account(account_key: str, branch_id: str = None, payment_method: str = None) -> Dict[str, str]:
    """Get account from settings or defaults"""
    # Check account settings first
    setting = await db.account_settings.find_one({"account_key": account_key}, {"_id": 0})
    if setting:
        return {"code": setting["account_code"], "name": setting["account_name"]}
    
    # Default accounts
    defaults = {
        "ap_account": {"code": "2-1100", "name": "Hutang Dagang"},
        "ar_account": {"code": "1-1300", "name": "Piutang Usaha"},
        "cash_account": {"code": "1-1100", "name": "Kas"},
        "bank_account": {"code": "1-1200", "name": "Bank"},
        "discount_purchase": {"code": "4-3000", "name": "Potongan Pembelian"},
        "discount_sales": {"code": "6-3000", "name": "Potongan Penjualan"},
        "salary_expense": {"code": "6-1100", "name": "Beban Gaji"},
    }
    return defaults.get(account_key, {"code": "9-9999", "name": "Unknown"})


async def create_journal_entry(
    reference_type: str,
    reference_id: str,
    reference_no: str,
    description: str,
    entries: List[Dict],
    branch_id: str,
    user_id: str,
    user_name: str
) -> str:
    """Create balanced journal entry"""
    from utils.number_generator import generate_transaction_number
    journal_number = await generate_transaction_number(db, "JV")
    
    total_debit = sum(e.get("debit", 0) for e in entries)
    total_credit = sum(e.get("credit", 0) for e in entries)
    
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(status_code=400, detail=f"Journal tidak balanced: Debit={total_debit}, Credit={total_credit}")
    
    journal = {
        "id": str(uuid.uuid4()),
        "journal_number": journal_number,
        "journal_no": journal_number,
        "journal_date": datetime.now(timezone.utc).isoformat(),
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "reference_type": reference_type,
        "reference_id": reference_id,
        "reference_no": reference_no,
        "memo": description,
        "description": description,
        "branch_id": branch_id,
        "entries": entries,
        "lines": entries,  # Compatibility
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": True,
        "status": "posted",
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await journal_entries.insert_one(journal)
    return journal_number


async def update_invoice_status(collection, invoice_id: str, invoice_type: str = "ap"):
    """Update invoice status based on outstanding amount"""
    invoice = await collection.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        return
    
    outstanding = invoice.get("outstanding_amount", 0)
    original = invoice.get("original_amount", invoice.get("amount", 0))
    due_date = invoice.get("due_date", "")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if outstanding <= 0:
        new_status = "paid"
    elif outstanding < original:
        new_status = "partial"
    elif due_date and due_date < today:
        new_status = "overdue"
    else:
        new_status = "open"
    
    await collection.update_one(
        {"id": invoice_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )


# ==================== AP PAYMENT ENDPOINTS ====================

@router.post("/ap/create")
async def create_ap_payment_with_allocation(
    data: APPaymentRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Create AP Payment with multi-invoice allocation
    
    BUSINESS RULE ENGINE:
    - SUM(allocation.allocated_amount) = payment.total_amount
    - Each allocation must reference valid AP invoice
    - Invoice outstanding >= allocated_amount
    - Auto-create journal: Dr. Hutang Dagang, Cr. Kas/Bank
    - Auto-update invoice status
    - Audit trail mandatory
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    # Validate allocations
    if not data.allocations:
        raise HTTPException(status_code=400, detail="Minimal 1 invoice harus dipilih untuk pembayaran")
    
    total_payment = sum(a.allocated_amount for a in data.allocations)
    total_discount = sum(a.discount_amount for a in data.allocations)
    
    if total_payment <= 0:
        raise HTTPException(status_code=400, detail="Total pembayaran harus lebih dari 0")
    
    # Validate each invoice
    for alloc in data.allocations:
        invoice = await ap_collection.find_one({"id": alloc.invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail=f"Invoice {alloc.invoice_no} tidak ditemukan")
        
        outstanding = invoice.get("outstanding_amount", invoice.get("amount", 0))
        if alloc.allocated_amount > outstanding + 0.01:  # Small tolerance
            raise HTTPException(
                status_code=400, 
                detail=f"Alokasi {alloc.invoice_no} (Rp {alloc.allocated_amount:,.0f}) melebihi sisa hutang (Rp {outstanding:,.0f})"
            )
        
        # Validate tenant isolation
        if invoice.get("supplier_id") != data.supplier_id:
            raise HTTPException(status_code=400, detail=f"Invoice {alloc.invoice_no} bukan milik supplier yang dipilih")
    
    # Get supplier info
    supplier = await suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
    supplier_name = supplier.get("name", "Unknown") if supplier else "Unknown"
    
    # Generate payment number
    payment_no = await generate_payment_number("PAY-AP")
    payment_id = str(uuid.uuid4())
    branch_id = data.branch_id or user.get("branch_id", "")
    
    # Create Payment Header
    payment_header = {
        "id": payment_id,
        "payment_no": payment_no,
        "payment_date": data.payment_date,
        "supplier_id": data.supplier_id,
        "supplier_name": supplier_name,
        "total_amount": total_payment,
        "discount_amount": total_discount,
        "net_amount": total_payment - total_discount,
        "payment_method": data.payment_method,
        "bank_account_id": data.bank_account_id,
        "bank_account_code": data.bank_account_code,
        "reference_no": data.reference_no,
        "notes": data.notes,
        "branch_id": branch_id,
        "allocation_count": len(data.allocations),
        "status": "posted",
        "journal_id": None,  # Will be updated
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ap_payments.insert_one(payment_header)
    
    # Create Payment Allocations
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
            "allocated_amount": alloc.allocated_amount,
            "discount_amount": alloc.discount_amount,
            "net_allocated": alloc.allocated_amount - alloc.discount_amount,
            "notes": alloc.notes,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        allocation_records.append(allocation_record)
        
        # Update invoice paid_amount and outstanding_amount
        current_paid = invoice.get("paid_amount", 0)
        current_outstanding = invoice.get("outstanding_amount", invoice.get("amount", 0))
        
        new_paid = current_paid + alloc.allocated_amount
        new_outstanding = current_outstanding - alloc.allocated_amount
        
        await ap_collection.update_one(
            {"id": alloc.invoice_id},
            {"$set": {
                "paid_amount": new_paid,
                "outstanding_amount": max(0, new_outstanding),
                "last_payment_date": data.payment_date,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update invoice status
        await update_invoice_status(ap_collection, alloc.invoice_id, "ap")
    
    # Bulk insert allocations
    if allocation_records:
        await ap_allocations.insert_many(allocation_records)
    
    # Create Journal Entry
    # Get accounts
    ap_account = await derive_account("ap_account", branch_id)
    
    if data.payment_method in ["bank", "transfer"]:
        credit_account = await derive_account("bank_account", branch_id)
        if data.bank_account_code:
            credit_account = {"code": data.bank_account_code, "name": "Bank"}
    else:
        credit_account = await derive_account("cash_account", branch_id)
    
    journal_entries_list = [
        {
            "account_code": ap_account["code"],
            "account_name": ap_account["name"],
            "debit": total_payment,
            "credit": 0,
            "description": f"Pembayaran Hutang - {supplier_name}"
        },
        {
            "account_code": credit_account["code"],
            "account_name": credit_account["name"],
            "debit": 0,
            "credit": total_payment,
            "description": f"Pembayaran Hutang - {supplier_name}"
        }
    ]
    
    # Add discount entry if any
    if total_discount > 0:
        discount_account = await derive_account("discount_purchase", branch_id)
        journal_entries_list.append({
            "account_code": discount_account["code"],
            "account_name": discount_account["name"],
            "debit": 0,
            "credit": total_discount,
            "description": f"Potongan Pembelian - {supplier_name}"
        })
        # Adjust debit
        journal_entries_list[0]["debit"] = total_payment + total_discount
    
    journal_no = await create_journal_entry(
        reference_type="ap_payment",
        reference_id=payment_id,
        reference_no=payment_no,
        description=f"Pembayaran Hutang {payment_no} - {supplier_name}",
        entries=journal_entries_list,
        branch_id=branch_id,
        user_id=user_id,
        user_name=user_name
    )
    
    # Update payment with journal_id
    await ap_payments.update_one(
        {"id": payment_id},
        {"$set": {"journal_id": journal_no}}
    )
    
    # Audit log
    await log_activity(
        db, user_id, user_name,
        "create", "ap_payment_allocation",
        f"Pembayaran AP {payment_no} ke {supplier_name}, {len(data.allocations)} invoice, Rp {total_payment:,.0f}",
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
        "allocation_count": len(data.allocations),
        "allocations": [
            {"invoice_no": a.invoice_no, "amount": a.allocated_amount}
            for a in data.allocations
        ]
    }


@router.get("/ap/{payment_id}")
async def get_ap_payment_with_allocations(
    payment_id: str,
    user: dict = Depends(get_current_user)
):
    """Get AP payment detail with all allocations"""
    payment = await ap_payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Pembayaran tidak ditemukan")
    
    # Get allocations
    allocations = await ap_allocations.find(
        {"payment_header_id": payment_id}, 
        {"_id": 0}
    ).to_list(100)
    
    payment["allocations"] = allocations
    
    # Verify allocation integrity
    total_allocated = sum(a.get("allocated_amount", 0) for a in allocations)
    payment["allocation_integrity"] = {
        "total_allocated": total_allocated,
        "header_amount": payment.get("total_amount", 0),
        "is_valid": abs(total_allocated - payment.get("total_amount", 0)) < 0.01
    }
    
    return payment


@router.get("/ap/supplier/{supplier_id}/unpaid")
async def get_unpaid_ap_invoices(
    supplier_id: str,
    user: dict = Depends(get_current_user)
):
    """Get list of unpaid/partial AP invoices for a supplier"""
    invoices = await ap_collection.find(
        {
            "supplier_id": supplier_id,
            "status": {"$in": ["open", "partial", "overdue"]},
            "$or": [
                {"is_deleted": {"$exists": False}},
                {"is_deleted": False}
            ]
        },
        {"_id": 0}
    ).sort("ap_date", 1).to_list(100)
    
    # Calculate outstanding for each
    for inv in invoices:
        if "outstanding_amount" not in inv:
            inv["outstanding_amount"] = inv.get("amount", 0) - inv.get("paid_amount", 0)
    
    return {
        "supplier_id": supplier_id,
        "invoices": invoices,
        "total_outstanding": sum(i.get("outstanding_amount", 0) for i in invoices)
    }


# ==================== AR PAYMENT ENDPOINTS ====================

@router.post("/ar/create")
async def create_ar_payment_with_allocation(
    data: ARPaymentRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Create AR Payment with multi-invoice allocation
    
    BUSINESS RULE ENGINE:
    - Same rules as AP but for receivables
    - Auto-create journal: Dr. Kas/Bank, Cr. Piutang Usaha
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    if not data.allocations:
        raise HTTPException(status_code=400, detail="Minimal 1 invoice harus dipilih untuk pembayaran")
    
    total_payment = sum(a.allocated_amount for a in data.allocations)
    total_discount = sum(a.discount_amount for a in data.allocations)
    
    if total_payment <= 0:
        raise HTTPException(status_code=400, detail="Total pembayaran harus lebih dari 0")
    
    # Validate each invoice
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
    
    # Get customer info
    customer = await customers.find_one({"id": data.customer_id}, {"_id": 0})
    customer_name = customer.get("name", "Unknown") if customer else "Unknown"
    
    payment_no = await generate_payment_number("PAY-AR")
    payment_id = str(uuid.uuid4())
    branch_id = data.branch_id or user.get("branch_id", "")
    
    # Create Payment Header
    payment_header = {
        "id": payment_id,
        "payment_no": payment_no,
        "payment_date": data.payment_date,
        "customer_id": data.customer_id,
        "customer_name": customer_name,
        "total_amount": total_payment,
        "discount_amount": total_discount,
        "net_amount": total_payment - total_discount,
        "payment_method": data.payment_method,
        "bank_account_id": data.bank_account_id,
        "bank_account_code": data.bank_account_code,
        "reference_no": data.reference_no,
        "notes": data.notes,
        "branch_id": branch_id,
        "allocation_count": len(data.allocations),
        "status": "posted",
        "journal_id": None,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ar_payments.insert_one(payment_header)
    
    # Create Payment Allocations
    allocation_records = []
    for alloc in data.allocations:
        invoice = await ar_collection.find_one({"id": alloc.invoice_id}, {"_id": 0})
        
        allocation_record = {
            "id": str(uuid.uuid4()),
            "payment_header_id": payment_id,
            "payment_no": payment_no,
            "invoice_id": alloc.invoice_id,
            "invoice_no": alloc.invoice_no,
            "original_amount": invoice.get("original_amount", invoice.get("amount", 0)),
            "allocated_amount": alloc.allocated_amount,
            "discount_amount": alloc.discount_amount,
            "net_allocated": alloc.allocated_amount - alloc.discount_amount,
            "notes": alloc.notes,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        allocation_records.append(allocation_record)
        
        # Update invoice
        current_paid = invoice.get("paid_amount", 0)
        current_outstanding = invoice.get("outstanding_amount", invoice.get("amount", 0))
        
        new_paid = current_paid + alloc.allocated_amount
        new_outstanding = current_outstanding - alloc.allocated_amount
        
        await ar_collection.update_one(
            {"id": alloc.invoice_id},
            {"$set": {
                "paid_amount": new_paid,
                "outstanding_amount": max(0, new_outstanding),
                "last_payment_date": data.payment_date,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        await update_invoice_status(ar_collection, alloc.invoice_id, "ar")
    
    if allocation_records:
        await ar_allocations.insert_many(allocation_records)
    
    # Create Journal Entry - AR: Dr. Cash/Bank, Cr. AR
    ar_account = await derive_account("ar_account", branch_id)
    
    if data.payment_method in ["bank", "transfer"]:
        debit_account = await derive_account("bank_account", branch_id)
        if data.bank_account_code:
            debit_account = {"code": data.bank_account_code, "name": "Bank"}
    else:
        debit_account = await derive_account("cash_account", branch_id)
    
    journal_entries_list = [
        {
            "account_code": debit_account["code"],
            "account_name": debit_account["name"],
            "debit": total_payment,
            "credit": 0,
            "description": f"Penerimaan Piutang - {customer_name}"
        },
        {
            "account_code": ar_account["code"],
            "account_name": ar_account["name"],
            "debit": 0,
            "credit": total_payment,
            "description": f"Penerimaan Piutang - {customer_name}"
        }
    ]
    
    if total_discount > 0:
        discount_account = await derive_account("discount_sales", branch_id)
        journal_entries_list.append({
            "account_code": discount_account["code"],
            "account_name": discount_account["name"],
            "debit": total_discount,
            "credit": 0,
            "description": f"Potongan Penjualan - {customer_name}"
        })
        journal_entries_list[1]["credit"] = total_payment + total_discount
    
    journal_no = await create_journal_entry(
        reference_type="ar_payment",
        reference_id=payment_id,
        reference_no=payment_no,
        description=f"Penerimaan Piutang {payment_no} - {customer_name}",
        entries=journal_entries_list,
        branch_id=branch_id,
        user_id=user_id,
        user_name=user_name
    )
    
    await ar_payments.update_one(
        {"id": payment_id},
        {"$set": {"journal_id": journal_no}}
    )
    
    await log_activity(
        db, user_id, user_name,
        "create", "ar_payment_allocation",
        f"Penerimaan AR {payment_no} dari {customer_name}, {len(data.allocations)} invoice, Rp {total_payment:,.0f}",
        request.client.host if request.client else "",
        branch_id
    )
    
    return {
        "status": "success",
        "message": "Penerimaan piutang berhasil dibuat",
        "payment_no": payment_no,
        "payment_id": payment_id,
        "journal_no": journal_no,
        "total_amount": total_payment,
        "allocation_count": len(data.allocations),
        "allocations": [
            {"invoice_no": a.invoice_no, "amount": a.allocated_amount}
            for a in data.allocations
        ]
    }


@router.get("/ar/{payment_id}")
async def get_ar_payment_with_allocations(
    payment_id: str,
    user: dict = Depends(get_current_user)
):
    """Get AR payment detail with all allocations"""
    payment = await ar_payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Pembayaran tidak ditemukan")
    
    allocations = await ar_allocations.find(
        {"payment_header_id": payment_id}, 
        {"_id": 0}
    ).to_list(100)
    
    payment["allocations"] = allocations
    
    total_allocated = sum(a.get("allocated_amount", 0) for a in allocations)
    payment["allocation_integrity"] = {
        "total_allocated": total_allocated,
        "header_amount": payment.get("total_amount", 0),
        "is_valid": abs(total_allocated - payment.get("total_amount", 0)) < 0.01
    }
    
    return payment


@router.get("/ar/customer/{customer_id}/unpaid")
async def get_unpaid_ar_invoices(
    customer_id: str,
    user: dict = Depends(get_current_user)
):
    """Get list of unpaid/partial AR invoices for a customer"""
    invoices = await ar_collection.find(
        {
            "customer_id": customer_id,
            "status": {"$in": ["open", "partial", "overdue"]},
            "$or": [
                {"is_deleted": {"$exists": False}},
                {"is_deleted": False}
            ]
        },
        {"_id": 0}
    ).sort("ar_date", 1).to_list(100)
    
    for inv in invoices:
        if "outstanding_amount" not in inv:
            inv["outstanding_amount"] = inv.get("amount", 0) - inv.get("paid_amount", 0)
    
    return {
        "customer_id": customer_id,
        "invoices": invoices,
        "total_outstanding": sum(i.get("outstanding_amount", 0) for i in invoices)
    }


# ==================== INTEGRITY CHECK ENDPOINTS ====================

@router.get("/integrity/ap")
async def check_ap_allocation_integrity(user: dict = Depends(get_current_user)):
    """Check AP payment allocation integrity"""
    payments = await ap_payments.find(
        {"status": "posted"},
        {"_id": 0}
    ).to_list(1000)
    
    issues = []
    for p in payments:
        allocations = await ap_allocations.find(
            {"payment_header_id": p["id"]},
            {"_id": 0}
        ).to_list(100)
        
        total_allocated = sum(a.get("allocated_amount", 0) for a in allocations)
        header_amount = p.get("total_amount", 0)
        
        if abs(total_allocated - header_amount) > 0.01:
            issues.append({
                "payment_no": p.get("payment_no"),
                "header_amount": header_amount,
                "total_allocated": total_allocated,
                "difference": total_allocated - header_amount
            })
    
    return {
        "status": "passed" if not issues else "failed",
        "total_payments": len(payments),
        "issues_found": len(issues),
        "issues": issues,
        "rule": "SUM(allocation.amount) = payment.amount"
    }


@router.get("/integrity/ar")
async def check_ar_allocation_integrity(user: dict = Depends(get_current_user)):
    """Check AR payment allocation integrity"""
    payments = await ar_payments.find(
        {"status": "posted"},
        {"_id": 0}
    ).to_list(1000)
    
    issues = []
    for p in payments:
        allocations = await ar_allocations.find(
            {"payment_header_id": p["id"]},
            {"_id": 0}
        ).to_list(100)
        
        total_allocated = sum(a.get("allocated_amount", 0) for a in allocations)
        header_amount = p.get("total_amount", 0)
        
        if abs(total_allocated - header_amount) > 0.01:
            issues.append({
                "payment_no": p.get("payment_no"),
                "header_amount": header_amount,
                "total_allocated": total_allocated,
                "difference": total_allocated - header_amount
            })
    
    return {
        "status": "passed" if not issues else "failed",
        "total_payments": len(payments),
        "issues_found": len(issues),
        "issues": issues,
        "rule": "SUM(allocation.amount) = payment.amount"
    }



# ==================== PAYMENT REVERSAL SYSTEM ====================
# ENTERPRISE RULE: Invoice LUNAS tidak bisa di-edit
# Jika ada kesalahan → REVERSAL JOURNAL, bukan edit/delete

class PaymentReversalRequest(BaseModel):
    """Request untuk reversal payment"""
    reason: str = Field(..., min_length=5, description="Alasan reversal - wajib diisi")
    notes: Optional[str] = None


@router.post("/ap/payments/{payment_id}/reverse")
async def reverse_ap_payment(
    payment_id: str,
    data: PaymentReversalRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    REVERSAL AP PAYMENT
    
    Flow:
    1. Create reversal journal (kebalikan dari journal asli)
    2. Restore outstanding amount pada semua invoice yang terkait
    3. Update status invoice (PAID → PARTIAL/OPEN)
    4. Mark payment as REVERSED
    5. Create audit log
    
    TIDAK BOLEH: Edit atau delete payment langsung
    """
    user_id = user.get("user_id", "")
    user_name = user.get("name", "System")
    
    # Get original payment
    payment = await ap_payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment tidak ditemukan")
    
    if payment.get("status") == "reversed":
        raise HTTPException(status_code=400, detail="Payment ini sudah di-reverse sebelumnya")
    
    if payment.get("status") != "posted":
        raise HTTPException(status_code=400, detail="Hanya payment dengan status POSTED yang bisa di-reverse")
    
    # Get all allocations for this payment
    allocations = await ap_allocations.find(
        {"payment_header_id": payment_id},
        {"_id": 0}
    ).to_list(100)
    
    if not allocations:
        raise HTTPException(status_code=400, detail="Tidak ada alokasi yang ditemukan untuk payment ini")
    
    supplier_name = payment.get("supplier_name", "Unknown")
    branch_id = payment.get("branch_id", "")
    total_amount = payment.get("total_amount", 0)
    discount_amount = payment.get("discount_amount", 0)
    
    # Create REVERSAL Journal Entry
    # Kebalikan dari journal asli: yang tadinya Debit jadi Credit, dst
    ap_account = await derive_account("ap_account", branch_id)
    
    if payment.get("payment_method") in ["bank", "transfer"]:
        cash_bank_account = await derive_account("bank_account", branch_id)
        if payment.get("bank_account_code"):
            cash_bank_account = {"code": payment.get("bank_account_code"), "name": "Bank"}
    else:
        cash_bank_account = await derive_account("cash_account", branch_id)
    
    reversal_entries = [
        {
            "account_code": cash_bank_account["code"],
            "account_name": cash_bank_account["name"],
            "debit": total_amount,  # REVERSAL: Kas/Bank naik kembali
            "credit": 0,
            "description": f"REVERSAL - Pembayaran Hutang {payment.get('payment_no')} - {supplier_name}"
        },
        {
            "account_code": ap_account["code"],
            "account_name": ap_account["name"],
            "debit": 0,
            "credit": total_amount,  # REVERSAL: Hutang kembali bertambah
            "description": f"REVERSAL - Pembayaran Hutang {payment.get('payment_no')} - {supplier_name}"
        }
    ]
    
    # If original had discount, reverse it too
    if discount_amount > 0:
        discount_account = await derive_account("discount_purchase", branch_id)
        reversal_entries.append({
            "account_code": discount_account["code"],
            "account_name": discount_account["name"],
            "debit": discount_amount,  # REVERSAL: Potongan dibatalkan
            "credit": 0,
            "description": f"REVERSAL - Potongan Pembelian {payment.get('payment_no')}"
        })
        # Adjust credit on AP account
        reversal_entries[1]["credit"] = total_amount + discount_amount
    
    # Generate reversal journal
    reversal_journal_no = await create_journal_entry(
        reference_type="ap_payment_reversal",
        reference_id=payment_id,
        reference_no=f"REV-{payment.get('payment_no')}",
        description=f"REVERSAL Pembayaran Hutang {payment.get('payment_no')} - {data.reason}",
        entries=reversal_entries,
        branch_id=branch_id,
        user_id=user_id,
        user_name=user_name
    )
    
    # Restore outstanding on each invoice
    restored_invoices = []
    for alloc in allocations:
        invoice = await ap_collection.find_one({"id": alloc["invoice_id"]}, {"_id": 0})
        if invoice:
            current_paid = invoice.get("paid_amount", 0)
            current_outstanding = invoice.get("outstanding_amount", 0)
            original_amount = invoice.get("original_amount", invoice.get("amount", 0))
            
            # Restore: paid berkurang, outstanding bertambah
            new_paid = max(0, current_paid - alloc.get("allocated_amount", 0))
            new_outstanding = min(original_amount, current_outstanding + alloc.get("allocated_amount", 0))
            
            await ap_collection.update_one(
                {"id": alloc["invoice_id"]},
                {"$set": {
                    "paid_amount": new_paid,
                    "outstanding_amount": new_outstanding,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Update invoice status
            await update_invoice_status(ap_collection, alloc["invoice_id"], "ap")
            
            restored_invoices.append({
                "invoice_no": alloc.get("invoice_no"),
                "restored_amount": alloc.get("allocated_amount", 0)
            })
    
    # Mark payment as REVERSED
    await ap_payments.update_one(
        {"id": payment_id},
        {"$set": {
            "status": "reversed",
            "reversal_journal_no": reversal_journal_no,
            "reversal_reason": data.reason,
            "reversal_notes": data.notes,
            "reversed_by": user_id,
            "reversed_by_name": user_name,
            "reversed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Audit log
    await log_activity(
        db, user_id, user_name,
        "ap_payment_reversal",
        f"REVERSAL Payment AP {payment.get('payment_no')} - Rp {total_amount:,.0f}",
        "ap_payments",
        payment_id,
        request.client.host if request.client else "",
        severity="warning"
    )
    
    return {
        "message": "Payment berhasil di-reverse",
        "payment_no": payment.get("payment_no"),
        "reversal_journal_no": reversal_journal_no,
        "total_reversed": total_amount,
        "restored_invoices": restored_invoices,
        "reason": data.reason
    }


@router.post("/ar/payments/{payment_id}/reverse")
async def reverse_ar_payment(
    payment_id: str,
    data: PaymentReversalRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    REVERSAL AR PAYMENT
    
    Flow:
    1. Create reversal journal (kebalikan dari journal asli)
    2. Restore outstanding amount pada semua invoice yang terkait
    3. Update status invoice (PAID → PARTIAL/OPEN)
    4. Mark payment as REVERSED
    5. Create audit log
    """
    user_id = user.get("user_id", "")
    user_name = user.get("name", "System")
    
    # Get original payment
    payment = await ar_payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment tidak ditemukan")
    
    if payment.get("status") == "reversed":
        raise HTTPException(status_code=400, detail="Payment ini sudah di-reverse sebelumnya")
    
    if payment.get("status") != "posted":
        raise HTTPException(status_code=400, detail="Hanya payment dengan status POSTED yang bisa di-reverse")
    
    # Get all allocations for this payment
    allocations = await ar_allocations.find(
        {"payment_header_id": payment_id},
        {"_id": 0}
    ).to_list(100)
    
    if not allocations:
        raise HTTPException(status_code=400, detail="Tidak ada alokasi yang ditemukan untuk payment ini")
    
    customer_name = payment.get("customer_name", "Unknown")
    branch_id = payment.get("branch_id", "")
    total_amount = payment.get("total_amount", 0)
    discount_amount = payment.get("discount_amount", 0)
    
    # Create REVERSAL Journal Entry
    ar_account = await derive_account("ar_account", branch_id)
    
    if payment.get("payment_method") in ["bank", "transfer"]:
        cash_bank_account = await derive_account("bank_account", branch_id)
        if payment.get("bank_account_code"):
            cash_bank_account = {"code": payment.get("bank_account_code"), "name": "Bank"}
    else:
        cash_bank_account = await derive_account("cash_account", branch_id)
    
    reversal_entries = [
        {
            "account_code": ar_account["code"],
            "account_name": ar_account["name"],
            "debit": total_amount,  # REVERSAL: Piutang kembali bertambah
            "credit": 0,
            "description": f"REVERSAL - Pembayaran Piutang {payment.get('payment_no')} - {customer_name}"
        },
        {
            "account_code": cash_bank_account["code"],
            "account_name": cash_bank_account["name"],
            "debit": 0,
            "credit": total_amount,  # REVERSAL: Kas/Bank berkurang
            "description": f"REVERSAL - Pembayaran Piutang {payment.get('payment_no')} - {customer_name}"
        }
    ]
    
    # If original had discount, reverse it too
    if discount_amount > 0:
        discount_account = await derive_account("discount_sales", branch_id)
        reversal_entries.append({
            "account_code": discount_account["code"],
            "account_name": discount_account["name"],
            "debit": 0,
            "credit": discount_amount,  # REVERSAL: Potongan penjualan dibatalkan
            "description": f"REVERSAL - Potongan Penjualan {payment.get('payment_no')}"
        })
        # Adjust debit on AR account
        reversal_entries[0]["debit"] = total_amount + discount_amount
    
    # Generate reversal journal
    reversal_journal_no = await create_journal_entry(
        reference_type="ar_payment_reversal",
        reference_id=payment_id,
        reference_no=f"REV-{payment.get('payment_no')}",
        description=f"REVERSAL Pembayaran Piutang {payment.get('payment_no')} - {data.reason}",
        entries=reversal_entries,
        branch_id=branch_id,
        user_id=user_id,
        user_name=user_name
    )
    
    # Restore outstanding on each invoice
    restored_invoices = []
    for alloc in allocations:
        invoice = await ar_collection.find_one({"id": alloc["invoice_id"]}, {"_id": 0})
        if invoice:
            current_paid = invoice.get("paid_amount", 0)
            current_outstanding = invoice.get("outstanding_amount", 0)
            original_amount = invoice.get("original_amount", invoice.get("amount", 0))
            
            # Restore: paid berkurang, outstanding bertambah
            new_paid = max(0, current_paid - alloc.get("allocated_amount", 0))
            new_outstanding = min(original_amount, current_outstanding + alloc.get("allocated_amount", 0))
            
            await ar_collection.update_one(
                {"id": alloc["invoice_id"]},
                {"$set": {
                    "paid_amount": new_paid,
                    "outstanding_amount": new_outstanding,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Update invoice status
            await update_invoice_status(ar_collection, alloc["invoice_id"], "ar")
            
            restored_invoices.append({
                "invoice_no": alloc.get("invoice_no"),
                "restored_amount": alloc.get("allocated_amount", 0)
            })
    
    # Mark payment as REVERSED
    await ar_payments.update_one(
        {"id": payment_id},
        {"$set": {
            "status": "reversed",
            "reversal_journal_no": reversal_journal_no,
            "reversal_reason": data.reason,
            "reversal_notes": data.notes,
            "reversed_by": user_id,
            "reversed_by_name": user_name,
            "reversed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Audit log
    await log_activity(
        db, user_id, user_name,
        "ar_payment_reversal",
        f"REVERSAL Payment AR {payment.get('payment_no')} - Rp {total_amount:,.0f}",
        "ar_payments",
        payment_id,
        request.client.host if request.client else "",
        severity="warning"
    )
    
    return {
        "message": "Payment berhasil di-reverse",
        "payment_no": payment.get("payment_no"),
        "reversal_journal_no": reversal_journal_no,
        "total_reversed": total_amount,
        "restored_invoices": restored_invoices,
        "reason": data.reason
    }


@router.get("/ap/payments/{payment_id}/can-reverse")
async def check_ap_payment_reversible(
    payment_id: str,
    user: dict = Depends(get_current_user)
):
    """Check if AP payment can be reversed"""
    payment = await ap_payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment tidak ditemukan")
    
    can_reverse = payment.get("status") == "posted"
    reason = None
    
    if payment.get("status") == "reversed":
        reason = "Payment sudah di-reverse sebelumnya"
    elif payment.get("status") != "posted":
        reason = f"Status payment: {payment.get('status')} - hanya POSTED yang bisa di-reverse"
    
    return {
        "payment_id": payment_id,
        "payment_no": payment.get("payment_no"),
        "can_reverse": can_reverse,
        "reason": reason,
        "current_status": payment.get("status"),
        "total_amount": payment.get("total_amount", 0)
    }


@router.get("/ar/payments/{payment_id}/can-reverse")
async def check_ar_payment_reversible(
    payment_id: str,
    user: dict = Depends(get_current_user)
):
    """Check if AR payment can be reversed"""
    payment = await ar_payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment tidak ditemukan")
    
    can_reverse = payment.get("status") == "posted"
    reason = None
    
    if payment.get("status") == "reversed":
        reason = "Payment sudah di-reverse sebelumnya"
    elif payment.get("status") != "posted":
        reason = f"Status payment: {payment.get('status')} - hanya POSTED yang bisa di-reverse"
    
    return {
        "payment_id": payment_id,
        "payment_no": payment.get("payment_no"),
        "can_reverse": can_reverse,
        "reason": reason,
        "current_status": payment.get("status"),
        "total_amount": payment.get("total_amount", 0)
    }
