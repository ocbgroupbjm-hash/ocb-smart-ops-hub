"""
Sales Module API - iPOS Ultimate Style
Modul Penjualan Enterprise lengkap dengan integrasi Stok, Piutang, dan Akuntansi
ASYNC Version - Compatible with Motor MongoDB driver
INTEGRATED: Fiscal Period Validation & Multi-Currency Support
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import os
from database import get_db as get_database
from utils.auth import get_current_user

router = APIRouter(prefix="/api/sales", tags=["Sales Module"])

# ==================== FISCAL PERIOD & MULTI-CURRENCY IMPORTS ====================
async def enforce_fiscal_period(transaction_date: str, action: str = "create"):
    """Enforce fiscal period validation"""
    from routes.erp_hardening import enforce_fiscal_period as _enforce
    return await _enforce(transaction_date, action)

async def get_exchange_rate(currency_code: str, transaction_date: str = None) -> float:
    """Get exchange rate for multi-currency"""
    from routes.erp_hardening import get_exchange_rate as _get_rate
    return await _get_rate(currency_code, transaction_date)

async def convert_to_base_currency(amount: float, currency_code: str, transaction_date: str = None) -> Dict:
    """Convert to base currency (IDR)"""
    from routes.erp_hardening import convert_to_base_currency as _convert
    return await _convert(amount, currency_code, transaction_date)

# ==================== MODELS ====================

class SalesOrderItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: float
    discount_percent: float = 0
    tax_percent: float = 0

class SalesOrderCreate(BaseModel):
    customer_id: str
    sales_person_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    branch_id: Optional[str] = None  # Branch/Cabang for stock
    delivery_date: Optional[str] = None
    ppn_type: str = "exclude"
    ppn_percent: float = 11
    notes: Optional[str] = None
    items: List[SalesOrderItem]
    subtotal: float = 0
    discount_amount: float = 0
    tax_amount: float = 0
    total: float = 0
    dp_amount: float = 0

class SalesInvoiceCreate(BaseModel):
    sales_order_id: Optional[str] = None
    customer_id: str
    sales_person_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    branch_id: Optional[str] = None  # Branch/Cabang for stock
    ppn_type: str = "exclude"
    ppn_percent: float = 11
    notes: Optional[str] = None
    voucher_code: Optional[str] = None
    items: List[SalesOrderItem]
    subtotal: float = 0
    discount_amount: float = 0
    tax_amount: float = 0
    other_cost: float = 0
    total: float = 0
    payment_type: str = "cash"
    cash_amount: float = 0
    credit_amount: float = 0
    dp_used: float = 0
    deposit_used: float = 0

class SalesReturnCreate(BaseModel):
    customer_id: str
    sales_person_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    ppn_type: str = "exclude"
    notes: Optional[str] = None
    refund_type: str = "ar_deduct"
    items: List[dict]
    subtotal: float = 0
    discount_amount: float = 0
    tax_amount: float = 0
    total: float = 0
    cash_refund: float = 0
    deposit_add: float = 0

class ARPaymentCreate(BaseModel):
    customer_id: str
    account_id: Optional[str] = None
    payment_method: str = "cash"
    reference_no: Optional[str] = None
    notes: Optional[str] = None
    items: List[dict]
    total_discount: float = 0
    total_amount: float = 0

# ==================== ASYNC HELPER FUNCTIONS ====================

async def generate_number(prefix: str, db) -> str:
    """Generate auto number like iPOS: PREFIX-YYYYMMDD-XXXX"""
    date_str = datetime.now().strftime("%Y%m%d")
    
    last = await db.counters.find_one({"prefix": prefix, "date": date_str})
    
    if last:
        seq = last.get("seq", 0) + 1
        await db.counters.update_one({"prefix": prefix, "date": date_str}, {"$set": {"seq": seq}})
    else:
        seq = 1
        await db.counters.insert_one({"prefix": prefix, "date": date_str, "seq": seq})
    
    return f"{prefix}-{date_str}-{str(seq).zfill(4)}"

async def get_product_info(db, product_id: str, branch_id: str = None) -> dict:
    """Get product information with stock from stock_movements (single source of truth)"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        return {}
    
    # Get stock from stock_movements (SINGLE SOURCE OF TRUTH)
    if branch_id:
        pipeline = [
            {"$match": {"product_id": product_id, "branch_id": branch_id}},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ]
        result = await db.stock_movements.aggregate(pipeline).to_list(1)
        product["stock"] = result[0]["total"] if result else 0
    else:
        # Fallback to product_stocks if no branch specified
        stock_record = await db.product_stocks.find_one({"product_id": product_id}, {"_id": 0, "quantity": 1})
        product["stock"] = stock_record.get("quantity", 0) if stock_record else 0
    
    return product

async def get_customer_info(db, customer_id: str) -> dict:
    """Get customer information"""
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    return customer or {}

# Default account settings for fallback
DEFAULT_ACCOUNTS = {
    "pembayaran_tunai": {"code": "1-1100", "name": "Kas"},
    "pembayaran_kredit": {"code": "1-1300", "name": "Piutang Usaha"},
    "pendapatan_jual": {"code": "4-1000", "name": "Penjualan"},
    "ppn_keluaran": {"code": "2-1400", "name": "PPN Keluaran"},
    "hpp": {"code": "5-1000", "name": "Harga Pokok Penjualan"},
    "persediaan_barang": {"code": "1-1400", "name": "Persediaan Barang"},
    "retur_penjualan": {"code": "4-1100", "name": "Retur Penjualan"},
    "komisi_sales": {"code": "5-4000", "name": "Beban Komisi Sales"},
}

async def derive_account(db, account_key: str, branch_id: str = None, warehouse_id: str = None, 
                        category_id: str = None, payment_method: str = None) -> dict:
    """
    ACCOUNT DERIVATION ENGINE
    Priority: Branch > Warehouse > Category > Payment > Global > Default
    """
    # Priority 1: Branch mapping
    if branch_id:
        mapping = await db.account_mapping_branch.find_one({
            "branch_id": branch_id, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 2: Warehouse mapping
    if warehouse_id:
        mapping = await db.account_mapping_warehouse.find_one({
            "warehouse_id": warehouse_id, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 3: Category mapping
    if category_id:
        mapping = await db.account_mapping_category.find_one({
            "category_id": category_id, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 4: Payment method mapping
    if payment_method:
        mapping = await db.account_mapping_payment.find_one({
            "payment_method_id": payment_method, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 5: Global setting
    global_setting = await db.account_settings.find_one({
        "account_key": account_key
    }, {"_id": 0})
    if global_setting:
        return {"code": global_setting["account_code"], "name": global_setting["account_name"]}
    
    # Priority 6: Default fallback
    default = DEFAULT_ACCOUNTS.get(account_key)
    if default:
        return default
    
    # Final fallback
    return {"code": "9-9999", "name": f"Unknown Account ({account_key})"}

async def update_stock(db, product_id: str, branch_id: str, qty_change: int, movement_type: str, reference: str, user_id: str = None):
    """Update stock via stock_movements (SINGLE SOURCE OF TRUTH)"""
    # NOTE: Tidak lagi update products.stock - stock dihitung dari movements
    
    # Create movement record
    movement = {
        "id": str(ObjectId()),
        "product_id": product_id,
        "branch_id": branch_id,  # Use branch_id as primary location
        "warehouse_id": branch_id,  # Backward compatibility
        "quantity": qty_change,
        "movement_type": movement_type,  # Correct field name
        "reference_type": "sales",
        "reference_number": reference,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_movements.insert_one(movement)
    
    # Sync product_stocks for quick lookup (optional, for UI speed)
    from routes.inventory import sync_product_stock_from_movements
    await sync_product_stock_from_movements(product_id, branch_id)
    
    return movement

async def create_journal_entry(db, entries: List[dict], reference: str, description: str, user_id: str = None):
    """Create journal entry with multiple lines"""
    journal_number = await generate_number("JV", db)
    
    journal = {
        "id": str(ObjectId()),
        "journal_number": journal_number,
        "date": datetime.now(timezone.utc).isoformat(),
        "reference": reference,
        "description": description,
        "entries": entries,
        "status": "posted",
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.journal_entries.insert_one(journal)
    
    for entry in entries:
        ledger_entry = {
            "id": str(ObjectId()),
            "journal_id": journal["id"],
            "account_code": entry.get("account_code"),
            "account_name": entry.get("account_name"),
            "debit": entry.get("debit", 0),
            "credit": entry.get("credit", 0),
            "date": journal["date"],
            "reference": reference,
            "description": description
        }
        await db.general_ledger.insert_one(ledger_entry)
    
    return journal

async def create_receivable(db, customer_id: str, invoice_number: str, amount: float, due_days: int = 30):
    """Create accounts receivable entry"""
    customer = await get_customer_info(db, customer_id)
    due_date = datetime.now(timezone.utc) + timedelta(days=due_days)
    ar_number = await generate_number("AR", db)
    
    ar = {
        "id": str(ObjectId()),
        "ar_no": ar_number,  # Use ar_no to match existing schema/index
        "ar_number": ar_number,
        "invoice_number": invoice_number,
        "customer_id": customer_id,
        "customer_name": customer.get("name", ""),
        "customer_code": customer.get("code", ""),
        "amount": amount,
        "paid_amount": 0,
        "remaining_amount": amount,
        "outstanding_amount": amount,  # Add for compatibility
        "due_date": due_date.isoformat(),
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.accounts_receivable.insert_one(ar)
    return ar

# ==================== SALES ORDER ENDPOINTS ====================

@router.get("/orders")
async def get_sales_orders(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    limit: int = 100
):
    """Get list of sales orders - Pesanan Jual List"""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    orders = await db.sales_orders.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    for order in orders:
        customer = await get_customer_info(db, order.get("customer_id", ""))
        order["customer_name"] = customer.get("name", "")
        order["customer_code"] = customer.get("code", "")
    
    return {"items": orders, "total": len(orders)}

@router.post("/orders")
async def create_sales_order(data: SalesOrderCreate):
    """Create sales order - Tambah Pesanan Penjualan"""
    db = get_database()
    
    # =============== FISCAL PERIOD VALIDATION ===============
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await enforce_fiscal_period(today, "create")
    
    customer = await get_customer_info(db, data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    subtotal = 0
    items_data = []
    
    for item in data.items:
        product = await get_product_info(db, item.product_id, data.branch_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Produk {item.product_id} tidak ditemukan")
        
        item_subtotal = item.quantity * item.unit_price
        item_discount = item_subtotal * (item.discount_percent / 100)
        item_after_disc = item_subtotal - item_discount
        item_tax = item_after_disc * (item.tax_percent / 100)
        item_total = item_after_disc + item_tax
        
        items_data.append({
            "product_id": item.product_id,
            "product_code": product.get("code", ""),
            "product_name": product.get("name", ""),
            "quantity": item.quantity,
            "delivered_qty": 0,
            "unit": product.get("unit", "PCS"),
            "unit_price": item.unit_price,
            "discount_percent": item.discount_percent,
            "discount_amount": item_discount,
            "tax_percent": item.tax_percent,
            "tax_amount": item_tax,
            "subtotal": item_subtotal,
            "total": item_total
        })
        subtotal += item_total
    
    trans_discount = data.discount_amount or 0
    after_discount = subtotal - trans_discount
    ppn_amount = after_discount * (data.ppn_percent / 100) if data.ppn_type == "exclude" else 0
    grand_total = after_discount + ppn_amount
    
    order_number = await generate_number("SO", db)
    
    order = {
        "id": str(ObjectId()),
        "order_number": order_number,
        "date": datetime.now(timezone.utc).isoformat(),
        "customer_id": data.customer_id,
        "customer_name": customer.get("name", ""),
        "customer_code": customer.get("code", ""),
        "sales_person_id": data.sales_person_id,
        "warehouse_id": data.warehouse_id,
        "delivery_date": data.delivery_date,
        "ppn_type": data.ppn_type,
        "ppn_percent": data.ppn_percent,
        "notes": data.notes,
        "items": items_data,
        "subtotal": subtotal,
        "discount_amount": trans_discount,
        "tax_amount": ppn_amount,
        "total": grand_total,
        "dp_amount": data.dp_amount,
        "total_qty": sum(i["quantity"] for i in items_data),
        "delivered_qty": 0,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.sales_orders.insert_one(order)
    order.pop("_id", None)
    
    return order

@router.get("/orders/{order_id}")
async def get_sales_order(order_id: str):
    """Get sales order detail"""
    db = get_database()
    order = await db.sales_orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Sales order tidak ditemukan")
    return order

# ==================== SALES INVOICE ENDPOINTS ====================

@router.get("/invoices")
async def get_sales_invoices(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    has_tax: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100
):
    """Get list of sales invoices - Daftar Penjualan"""
    db = get_database()
    
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["status"] = status
    if has_tax == "true":
        query["tax_amount"] = {"$gt": 0}
    
    invoices = await db.sales_invoices.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"items": invoices, "total": len(invoices)}

@router.post("/invoices")
async def create_sales_invoice(data: SalesInvoiceCreate, current_user: dict = Depends(get_current_user)):
    """Create sales invoice - Tambah Penjualan with full integration"""
    db = get_database()
    user = current_user  # For use in the function
    
    # =============== FISCAL PERIOD VALIDATION ===============
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await enforce_fiscal_period(today, "create")
    
    customer = await get_customer_info(db, data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    subtotal = 0
    total_hpp = 0
    items_data = []
    
    for item in data.items:
        product = await get_product_info(db, item.product_id, data.branch_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Produk {item.product_id} tidak ditemukan")
        
        current_stock = product.get("stock", 0)
        if current_stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Stok {product.get('name')} tidak cukup ({current_stock} tersedia)")
        
        item_subtotal = item.quantity * item.unit_price
        item_discount = item_subtotal * (item.discount_percent / 100)
        item_after_disc = item_subtotal - item_discount
        item_tax = item_after_disc * (item.tax_percent / 100)
        item_total = item_after_disc + item_tax
        item_hpp = item.quantity * product.get("cost_price", 0)
        
        items_data.append({
            "product_id": item.product_id,
            "product_code": product.get("code", ""),
            "product_name": product.get("name", ""),
            "quantity": item.quantity,
            "unit": product.get("unit", "PCS"),
            "unit_price": item.unit_price,
            "cost_price": product.get("cost_price", 0),
            "discount_percent": item.discount_percent,
            "discount_amount": item_discount,
            "tax_percent": item.tax_percent,
            "tax_amount": item_tax,
            "subtotal": item_subtotal,
            "total": item_total,
            "hpp": item_hpp
        })
        subtotal += item_total
        total_hpp += item_hpp
    
    trans_discount = data.discount_amount or 0
    after_discount = subtotal - trans_discount
    ppn_amount = after_discount * (data.ppn_percent / 100) if data.ppn_type == "exclude" else 0
    other_cost = data.other_cost or 0
    grand_total = after_discount + ppn_amount + other_cost
    
    is_credit = data.payment_type in ["credit", "combo"] and data.credit_amount > 0
    credit_amount = grand_total - data.cash_amount - data.dp_used - data.deposit_used if is_credit else 0
    
    # =============== CREDIT CONTROL - HARD STOP ===============
    if is_credit and credit_amount > 0:
        from routes.credit_control import check_credit_transaction
        credit_check = await check_credit_transaction(db, data.customer_id, credit_amount, {})
        
        if not credit_check["allowed"]:
            # Check if there's an approved override
            override_approval = await db.approval_requests.find_one({
                "reference_id": data.customer_id,
                "approval_type": "credit_override",
                "status": "approved",
                "data.requested_amount": {"$gte": credit_amount}
            })
            
            if not override_approval:
                raise HTTPException(
                    status_code=403, 
                    detail={
                        "message": credit_check["reason"],
                        "error_type": "CREDIT_LIMIT_EXCEEDED",
                        "requires_override": credit_check.get("requires_override", False),
                        "credit_info": credit_check.get("credit_info")
                    }
                )
    
    invoice_number = await generate_number("INV", db)
    
    invoice = {
        "id": str(ObjectId()),
        "invoice_number": invoice_number,
        "sales_order_id": data.sales_order_id,
        "date": datetime.now(timezone.utc).isoformat(),
        "customer_id": data.customer_id,
        "customer_name": customer.get("name", ""),
        "customer_code": customer.get("code", ""),
        "customer_npwp": customer.get("npwp", ""),
        "customer_address": customer.get("address", ""),
        "sales_person_id": data.sales_person_id,
        "warehouse_id": data.warehouse_id,
        "ppn_type": data.ppn_type,
        "ppn_percent": data.ppn_percent,
        "notes": data.notes,
        "voucher_code": data.voucher_code,
        "items": items_data,
        "subtotal": subtotal,
        "discount_amount": trans_discount,
        "tax_amount": ppn_amount,
        "other_cost": other_cost,
        "total": grand_total,
        "total_hpp": total_hpp,
        "payment_type": data.payment_type,
        "cash_amount": data.cash_amount,
        "credit_amount": credit_amount,
        "dp_used": data.dp_used,
        "deposit_used": data.deposit_used,
        "paid_amount": data.cash_amount + data.dp_used + data.deposit_used,
        "is_credit": is_credit,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.sales_invoices.insert_one(invoice)
    
    # ===== INTEGRATION: Update Stock =====
    branch_id = data.branch_id or user.get("branch_id") or "0acd2ffd-c2d9-4324-b860-a4626840e80e"  # Default HQ
    for item in items_data:
        await update_stock(
            db,
            item["product_id"],
            branch_id,  # Use branch_id instead of warehouse_id
            -item["quantity"],
            "sales_out",
            invoice_number,
            user.get("id")
        )
    
    # ===== INTEGRATION: Create Receivable if credit =====
    if is_credit and credit_amount > 0:
        await create_receivable(db, data.customer_id, invoice_number, credit_amount)
    
    # ===== INTEGRATION: Create Journal Entries using Account Derivation Engine =====
    journal_entries = []
    
    # Get product category for account derivation (use first item's category)
    first_item = items_data[0] if items_data else {}
    product = await get_product_info(db, first_item.get("product_id", ""), data.branch_id)
    category_id = product.get("category_id")
    
    if data.cash_amount > 0:
        cash_account = await derive_account(db, "pembayaran_tunai", 
            branch_id=None, warehouse_id=data.warehouse_id, 
            category_id=category_id, payment_method="cash")
        journal_entries.append({
            "account_code": cash_account["code"],
            "account_name": cash_account["name"],
            "debit": data.cash_amount,
            "credit": 0
        })
    
    if credit_amount > 0:
        ar_account = await derive_account(db, "pembayaran_kredit",
            branch_id=None, warehouse_id=data.warehouse_id,
            category_id=category_id, payment_method="credit")
        journal_entries.append({
            "account_code": ar_account["code"],
            "account_name": ar_account["name"],
            "debit": credit_amount,
            "credit": 0
        })
        
        # ===== INTEGRATION: Create AR Entry for Credit Sales =====
        await create_receivable(db, data.customer_id, invoice_number, credit_amount, due_days=30)
    
    sales_net = grand_total - ppn_amount
    sales_account = await derive_account(db, "pendapatan_jual",
        branch_id=None, warehouse_id=data.warehouse_id, category_id=category_id)
    journal_entries.append({
        "account_code": sales_account["code"],
        "account_name": sales_account["name"],
        "debit": 0,
        "credit": sales_net
    })
    
    if ppn_amount > 0:
        ppn_account = await derive_account(db, "ppn_keluaran",
            branch_id=None, warehouse_id=data.warehouse_id, category_id=category_id)
        journal_entries.append({
            "account_code": ppn_account["code"],
            "account_name": ppn_account["name"],
            "debit": 0,
            "credit": ppn_amount
        })
    
    if total_hpp > 0:
        hpp_account = await derive_account(db, "hpp",
            branch_id=None, warehouse_id=data.warehouse_id, category_id=category_id)
        inventory_account = await derive_account(db, "persediaan_barang",
            branch_id=None, warehouse_id=data.warehouse_id, category_id=category_id)
        journal_entries.append({
            "account_code": hpp_account["code"],
            "account_name": hpp_account["name"],
            "debit": total_hpp,
            "credit": 0
        })
        journal_entries.append({
            "account_code": inventory_account["code"],
            "account_name": inventory_account["name"],
            "debit": 0,
            "credit": total_hpp
        })
    
    await create_journal_entry(db, journal_entries, invoice_number, f"Penjualan {invoice_number}")
    
    # ===== INTEGRATION: Record Price History =====
    for item in items_data:
        price_history = {
            "id": str(ObjectId()),
            "product_id": item["product_id"],
            "product_code": item["product_code"],
            "product_name": item["product_name"],
            "customer_id": data.customer_id,
            "customer_name": customer.get("name", ""),
            "invoice_number": invoice_number,
            "date": datetime.now(timezone.utc).isoformat(),
            "unit_price": item["unit_price"],
            "quantity": item["quantity"],
            "unit": item["unit"],
            "discount_percent": item["discount_percent"],
            "tax_percent": item["tax_percent"],
            "sales_person_id": data.sales_person_id
        }
        await db.sales_price_history.insert_one(price_history)
    
    invoice.pop("_id", None)
    return invoice

# ==================== SALES RETURNS ENDPOINTS ====================

@router.get("/returns")
async def get_sales_returns(limit: int = 100):
    """Get list of sales returns - Daftar Retur Penjualan"""
    db = get_database()
    returns = await db.sales_returns.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"items": returns, "total": len(returns)}

@router.post("/returns")
async def create_sales_return(data: SalesReturnCreate):
    """Create sales return - Tambah Retur Penjualan with full integration"""
    db = get_database()
    
    customer = await get_customer_info(db, data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    return_number = await generate_number("SRT", db)
    
    items_data = []
    total_return = 0
    total_hpp_return = 0
    
    for item in data.items:
        product = await get_product_info(db, item.get("product_id"), data.branch_id if hasattr(data, 'branch_id') else None)
        qty = item.get("quantity", 0)
        price = item.get("unit_price", 0)
        item_total = qty * price
        hpp = qty * product.get("cost_price", 0) if product else 0
        
        items_data.append({
            "invoice_id": item.get("invoice_id"),
            "product_id": item.get("product_id"),
            "product_code": product.get("code", "") if product else "",
            "product_name": product.get("name", "") if product else "",
            "quantity": qty,
            "unit_price": price,
            "total": item_total,
            "hpp": hpp
        })
        total_return += item_total
        total_hpp_return += hpp
    
    sales_return = {
        "id": str(ObjectId()),
        "return_number": return_number,
        "date": datetime.now(timezone.utc).isoformat(),
        "customer_id": data.customer_id,
        "customer_name": customer.get("name", ""),
        "customer_code": customer.get("code", ""),
        "sales_person_id": data.sales_person_id,
        "warehouse_id": data.warehouse_id,
        "ppn_type": data.ppn_type,
        "notes": data.notes,
        "refund_type": data.refund_type,
        "items": items_data,
        "subtotal": total_return,
        "discount_amount": data.discount_amount,
        "tax_amount": data.tax_amount,
        "total": data.total or total_return,
        "cash_refund": data.cash_refund,
        "deposit_add": data.deposit_add,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.sales_returns.insert_one(sales_return)
    
    # ===== INTEGRATION: Update Stock (add back) =====
    for item in items_data:
        if item.get("product_id"):
            await update_stock(
                db,
                item["product_id"],
                data.warehouse_id or "main",
                item["quantity"],
                "sales_return_in",
                return_number
            )
    
    # ===== INTEGRATION: Reduce AR if refund_type is ar_deduct =====
    if data.refund_type == "ar_deduct":
        ar_deduct = data.total - data.cash_refund - data.deposit_add
        if ar_deduct > 0:
            ar = await db.accounts_receivable.find_one(
                {"customer_id": data.customer_id, "status": "open"},
                sort=[("created_at", 1)]
            )
            if ar:
                new_remaining = max(0, ar.get("remaining_amount", 0) - ar_deduct)
                new_status = "paid" if new_remaining == 0 else "open"
                await db.accounts_receivable.update_one(
                    {"id": ar["id"]},
                    {"$set": {"remaining_amount": new_remaining, "status": new_status}}
                )
    
    # ===== INTEGRATION: Create Journal for Return =====
    journal_entries = []
    
    journal_entries.append({
        "account_code": "4-1100",
        "account_name": "Retur Penjualan",
        "debit": total_return,
        "credit": 0
    })
    
    if data.cash_refund > 0:
        journal_entries.append({
            "account_code": "1-1100",
            "account_name": "Kas",
            "debit": 0,
            "credit": data.cash_refund
        })
    
    ar_deduct_amount = total_return - data.cash_refund - data.deposit_add
    if ar_deduct_amount > 0:
        journal_entries.append({
            "account_code": "1-1300",
            "account_name": "Piutang Usaha",
            "debit": 0,
            "credit": ar_deduct_amount
        })
    
    if total_hpp_return > 0:
        journal_entries.append({
            "account_code": "1-1400",
            "account_name": "Persediaan Barang",
            "debit": total_hpp_return,
            "credit": 0
        })
        journal_entries.append({
            "account_code": "5-1000",
            "account_name": "Harga Pokok Penjualan",
            "debit": 0,
            "credit": total_hpp_return
        })
    
    await create_journal_entry(db, journal_entries, return_number, f"Retur Penjualan {return_number}")
    
    sales_return.pop("_id", None)
    return sales_return

# ==================== PRICE HISTORY ENDPOINTS ====================

@router.get("/price-history")
async def get_sales_price_history(
    customer_id: Optional[str] = None,
    product_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 500
):
    """Get sales price history - History Harga Jual"""
    db = get_database()
    
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if product_id:
        query["product_id"] = product_id
    
    history = await db.sales_price_history.find(query, {"_id": 0}).sort("date", -1).limit(limit).to_list(limit)
    return {"items": history, "total": len(history)}

# ==================== TRADE-IN ENDPOINTS ====================

@router.get("/trade-in")
async def get_trade_in_list(limit: int = 100):
    """Get trade-in transactions - Daftar Tukar Tambah"""
    db = get_database()
    transactions = await db.trade_in_transactions.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"items": transactions, "total": len(transactions)}

@router.post("/trade-in")
async def create_trade_in(data: dict):
    """Create trade-in transaction - Tambah Tukar Tambah"""
    db = get_database()
    
    trade_in_number = await generate_number("TI", db)
    
    trade_in = {
        "id": str(ObjectId()),
        "transaction_number": trade_in_number,
        "date": datetime.now(timezone.utc).isoformat(),
        "customer_id": data.get("customer_id"),
        "customer_name": data.get("customer_name", ""),
        "sales_person_id": data.get("sales_person_id"),
        "warehouse_id": data.get("warehouse_id"),
        "items_in": data.get("items_in", []),
        "items_out": data.get("items_out", []),
        "total_in": data.get("total_in", 0),
        "total_out": data.get("total_out", 0),
        "difference": data.get("total_out", 0) - data.get("total_in", 0),
        "notes": data.get("notes"),
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trade_in_transactions.insert_one(trade_in)
    
    for item in data.get("items_in", []):
        await update_stock(db, item["product_id"], data.get("warehouse_id", "main"), item["quantity"], "trade_in", trade_in_number)
    
    for item in data.get("items_out", []):
        await update_stock(db, item["product_id"], data.get("warehouse_id", "main"), -item["quantity"], "trade_out", trade_in_number)
    
    trade_in.pop("_id", None)
    return trade_in

# ==================== POINTS ENDPOINTS ====================

@router.get("/points")
async def get_customer_points(customer_id: Optional[str] = None, limit: int = 100):
    """Get customer loyalty points - Point Transaksi"""
    db = get_database()
    
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    
    points = await db.loyalty_points.find(query, {"_id": 0}).sort("date", -1).limit(limit).to_list(limit)
    return {"items": points, "total": len(points)}

@router.post("/points/redeem")
async def redeem_points(data: dict):
    """Redeem customer points - Ambil Point"""
    db = get_database()
    
    customer_id = data.get("customer_id")
    points_to_redeem = data.get("points", 0)
    
    pipeline = [
        {"$match": {"customer_id": customer_id}},
        {"$group": {"_id": None, "total": {"$sum": "$points"}}}
    ]
    total_points = await db.loyalty_points.aggregate(pipeline).to_list(1)
    available = total_points[0]["total"] if total_points else 0
    
    if points_to_redeem > available:
        raise HTTPException(status_code=400, detail="Point tidak cukup")
    
    redemption = {
        "id": str(ObjectId()),
        "customer_id": customer_id,
        "transaction_type": "redeem",
        "points": -points_to_redeem,
        "date": datetime.now(timezone.utc).isoformat(),
        "notes": data.get("notes", "Point redemption")
    }
    await db.loyalty_points.insert_one(redemption)
    
    return {"success": True, "redeemed": points_to_redeem, "remaining": available - points_to_redeem}

# ==================== COMMISSION PAYMENTS ENDPOINTS ====================

@router.get("/commission-payments")
async def get_commission_payments(limit: int = 100):
    """Get commission payments - Daftar Pembayaran Komisi Sales"""
    db = get_database()
    payments = await db.commission_payments.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"items": payments, "total": len(payments)}

@router.post("/commission-payments")
async def create_commission_payment(data: dict):
    """Create commission payment - Tambah Pembayaran Komisi Sales"""
    db = get_database()
    
    payment_number = await generate_number("COM", db)
    
    payment = {
        "id": str(ObjectId()),
        "payment_number": payment_number,
        "date": datetime.now(timezone.utc).isoformat(),
        "sales_person_id": data.get("sales_person_id"),
        "sales_name": data.get("sales_name", ""),
        "account_id": data.get("account_id"),
        "payment_method": data.get("payment_method", "cash"),
        "period_from": data.get("period_from"),
        "period_to": data.get("period_to"),
        "transactions": data.get("transactions", []),
        "total_sales": data.get("total_sales", 0),
        "total_return": data.get("total_return", 0),
        "commission_rate": data.get("commission_rate", 0),
        "amount": data.get("amount", 0),
        "notes": data.get("notes"),
        "status": "paid",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.commission_payments.insert_one(payment)
    
    journal_entries = [
        {"account_code": "5-2000", "account_name": "Beban Komisi Sales", "debit": payment["amount"], "credit": 0},
        {"account_code": "1-1100", "account_name": "Kas", "debit": 0, "credit": payment["amount"]}
    ]
    await create_journal_entry(db, journal_entries, payment_number, f"Pembayaran Komisi {payment_number}")
    
    payment.pop("_id", None)
    return payment

# ==================== DELIVERIES ENDPOINTS ====================

@router.get("/deliveries")
async def get_deliveries(
    status: Optional[str] = None,
    courier: Optional[str] = None,
    limit: int = 100
):
    """Get deliveries - Daftar Pengiriman"""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    if courier:
        query["courier"] = courier
    
    deliveries = await db.deliveries.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"items": deliveries, "total": len(deliveries)}

@router.put("/deliveries/{delivery_id}")
async def update_delivery(delivery_id: str, data: dict):
    """Update delivery status"""
    db = get_database()
    
    update_data = {}
    if "status" in data:
        update_data["status"] = data["status"]
    if "tracking_number" in data:
        update_data["tracking_number"] = data["tracking_number"]
    if "courier" in data:
        update_data["courier"] = data["courier"]
    if "ship_date" in data:
        update_data["ship_date"] = data["ship_date"]
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.deliveries.update_one({"id": delivery_id}, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Delivery tidak ditemukan")
    
    return {"success": True, "updated": delivery_id}

# ==================== TAX EXPORT ENDPOINTS ====================

@router.post("/tax-export/csv")
async def export_tax_csv(data: dict):
    """Export tax invoices to CSV - Laporan CSV Faktur Pajak"""
    db = get_database()
    
    invoice_ids = data.get("invoice_ids", [])
    if not invoice_ids:
        raise HTTPException(status_code=400, detail="Pilih minimal 1 faktur")
    
    invoices = await db.sales_invoices.find({"id": {"$in": invoice_ids}}, {"_id": 0}).to_list(1000)
    
    csv_lines = ["FK,KD_JENIS_TRANSAKSI,FG_PENGGANTI,NOMOR_FAKTUR,MASA_PAJAK,TAHUN_PAJAK,TANGGAL_FAKTUR,NPWP,NAMA,ALAMAT_LENGKAP,JUMLAH_DPP,JUMLAH_PPN,JUMLAH_PPNBM,ID_KETERANGAN_TAMBAHAN,FG_UANG_MUKA,UANG_MUKA_DPP,UANG_MUKA_PPN,UANG_MUKA_PPNBM,REFERENSI"]
    
    for inv in invoices:
        date_obj = datetime.fromisoformat(inv.get("date", "").replace("Z", "+00:00"))
        dpp = inv.get("total", 0) - inv.get("tax_amount", 0)
        ppn = inv.get("tax_amount", 0)
        
        line = f"FK,01,0,{inv.get('tax_invoice_number', '')},{date_obj.month},{date_obj.year},{date_obj.strftime('%d/%m/%Y')},{inv.get('customer_npwp', '')},{inv.get('customer_name', '')},{inv.get('customer_address', '')},{dpp},{ppn},0,,0,0,0,0,{inv.get('invoice_number', '')}"
        csv_lines.append(line)
    
    csv_content = "\n".join(csv_lines)
    
    from fastapi.responses import Response
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=faktur_pajak.csv"}
    )

@router.post("/tax-export/xml")
async def export_tax_xml(data: dict):
    """Export tax invoices to XML - Laporan XML Faktur Pajak"""
    db = get_database()
    
    invoice_ids = data.get("invoice_ids", [])
    if not invoice_ids:
        raise HTTPException(status_code=400, detail="Pilih minimal 1 faktur")
    
    invoices = await db.sales_invoices.find({"id": {"$in": invoice_ids}}, {"_id": 0}).to_list(1000)
    
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<FakturPajak>']
    
    for inv in invoices:
        xml_lines.append('  <Faktur>')
        xml_lines.append(f'    <NomorFaktur>{inv.get("tax_invoice_number", "")}</NomorFaktur>')
        xml_lines.append(f'    <TanggalFaktur>{inv.get("date", "")[:10]}</TanggalFaktur>')
        xml_lines.append(f'    <NPWP>{inv.get("customer_npwp", "")}</NPWP>')
        xml_lines.append(f'    <NamaPKP>{inv.get("customer_name", "")}</NamaPKP>')
        xml_lines.append(f'    <DPP>{inv.get("total", 0) - inv.get("tax_amount", 0)}</DPP>')
        xml_lines.append(f'    <PPN>{inv.get("tax_amount", 0)}</PPN>')
        xml_lines.append('  </Faktur>')
    
    xml_lines.append('</FakturPajak>')
    xml_content = "\n".join(xml_lines)
    
    from fastapi.responses import Response
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=faktur_pajak.xml"}
    )

# ==================== AR PAYMENTS FROM SALES MODULE ====================

@router.get("/ar-payments")
async def get_ar_payments_list(limit: int = 100):
    """Get AR payments from sales - alias for /api/ar/payments"""
    db = get_database()
    payments = await db.ar_payments.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"items": payments, "total": len(payments)}
