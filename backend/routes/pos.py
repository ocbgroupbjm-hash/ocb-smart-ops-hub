# OCB TITAN - POS (Point of Sale) API
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from database import (
    transactions, held_transactions, products, product_stocks, 
    customers, branches, cash_movements, stock_movements, get_next_sequence
)
from utils.auth import get_current_user
from models.titan_models import (
    Transaction, TransactionItem, PaymentDetail, TransactionStatus,
    PaymentMethod, StockMovement, StockMovementType, CashMovement
)
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/pos", tags=["POS"])

class CartItem(BaseModel):
    product_id: str
    quantity: int
    discount_percent: float = 0
    discount_amount: float = 0
    price_override: Optional[float] = None

class PaymentInput(BaseModel):
    method: str  # cash, bank_transfer, qris, ewallet, store_credit
    amount: float
    reference: str = ""

class CreateTransaction(BaseModel):
    items: List[CartItem]
    customer_id: Optional[str] = None
    customer_name: str = ""
    customer_phone: str = ""
    discount_percent: float = 0
    discount_amount: float = 0
    payments: List[PaymentInput]
    notes: str = ""

class HoldTransaction(BaseModel):
    items: List[CartItem]
    customer_id: Optional[str] = None
    customer_name: str = ""
    hold_name: str = ""
    notes: str = ""

# ==================== TRANSACTION ====================

@router.post("/transaction")
async def create_transaction(data: CreateTransaction, user: dict = Depends(get_current_user)):
    """Create a new POS transaction"""
    branch_id = user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=400, detail="User not assigned to a branch")
    
    # Validate and build items
    tx_items = []
    subtotal = 0
    total_cost = 0
    
    for cart_item in data.items:
        product = await products.find_one({"id": cart_item.product_id, "is_active": True}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=400, detail=f"Product not found: {cart_item.product_id}")
        
        # Check stock
        stock = await product_stocks.find_one(
            {"product_id": cart_item.product_id, "branch_id": branch_id},
            {"_id": 0}
        )
        available = stock.get("available", 0) if stock else 0
        
        if product.get("track_stock", True) and available < cart_item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for {product['name']}. Available: {available}"
            )
        
        # Calculate pricing
        unit_price = cart_item.price_override or product.get("sell_price", 0) or product.get("selling_price", 0)
        
        # Apply customer segment pricing
        if data.customer_id:
            customer = await customers.find_one({"id": data.customer_id}, {"_id": 0})
            if customer:
                segment = customer.get("segment", "regular")
                if segment == "member" and product.get("member_price", 0) > 0:
                    unit_price = product["member_price"]
                elif segment == "reseller" and product.get("reseller_price", 0) > 0:
                    unit_price = product["reseller_price"]
                elif segment == "wholesale" and product.get("wholesale_price", 0) > 0:
                    unit_price = product["wholesale_price"]
        
        item_subtotal = unit_price * cart_item.quantity
        
        # Item discount
        item_discount = cart_item.discount_amount
        if cart_item.discount_percent > 0:
            item_discount = item_subtotal * (cart_item.discount_percent / 100)
        
        # Tax
        tax_rate = product.get("tax_rate", 0)
        item_after_discount = item_subtotal - item_discount
        tax_amount = item_after_discount * (tax_rate / 100)
        item_total = item_after_discount + tax_amount
        
        cost_price = product.get("cost_price", 0) * cart_item.quantity
        
        tx_item = TransactionItem(
            product_id=cart_item.product_id,
            product_code=product.get("code", ""),
            product_name=product.get("name", ""),
            quantity=cart_item.quantity,
            unit_price=unit_price,
            discount_percent=cart_item.discount_percent,
            discount_amount=item_discount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            subtotal=item_subtotal,
            total=item_total,
            cost_price=cost_price
        )
        
        tx_items.append(tx_item)
        subtotal += item_subtotal
        total_cost += cost_price
    
    # Transaction-level discount
    tx_discount = data.discount_amount
    if data.discount_percent > 0:
        tx_discount = subtotal * (data.discount_percent / 100)
    
    # Calculate totals
    total_tax = sum(item.tax_amount for item in tx_items)
    total = subtotal - tx_discount + total_tax
    
    # Validate payments
    paid_amount = sum(p.amount for p in data.payments)
    if paid_amount < total:
        raise HTTPException(status_code=400, detail=f"Insufficient payment. Total: {total}, Paid: {paid_amount}")
    
    change = paid_amount - total
    
    # Generate invoice number
    invoice = await get_next_sequence("invoice", "INV")
    
    # Create transaction
    tx = Transaction(
        invoice_number=invoice,
        branch_id=branch_id,
        cashier_id=user.get("user_id", ""),
        cashier_name=user.get("name", ""),
        customer_id=data.customer_id,
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        items=[item.model_dump() for item in tx_items],
        subtotal=subtotal,
        discount_percent=data.discount_percent,
        discount_amount=tx_discount,
        tax_amount=total_tax,
        total=total,
        payments=[PaymentDetail(method=PaymentMethod(p.method), amount=p.amount, reference=p.reference).model_dump() for p in data.payments],
        paid_amount=paid_amount,
        change_amount=change,
        status=TransactionStatus.COMPLETED,
        total_cost=total_cost,
        profit=total - total_cost,
        notes=data.notes
    )
    
    await transactions.insert_one(tx.model_dump())
    
    # Update stock
    for item in tx_items:
        await product_stocks.update_one(
            {"product_id": item.product_id, "branch_id": branch_id},
            {"$inc": {"quantity": -item.quantity, "available": -item.quantity}}
        )
        
        # Record stock movement
        movement = StockMovement(
            product_id=item.product_id,
            branch_id=branch_id,
            movement_type=StockMovementType.SALE,
            quantity=-item.quantity,
            reference_id=tx.id,
            reference_type="transaction",
            cost_price=item.cost_price,
            user_id=user.get("user_id", "")
        )
        await stock_movements.insert_one(movement.model_dump())
    
    # Update cash balance if cash payment
    cash_payment = sum(p.amount for p in data.payments if p.method == "cash")
    if cash_payment > 0:
        branch = await branches.find_one({"id": branch_id}, {"_id": 0})
        current_balance = branch.get("cash_balance", 0) if branch else 0
        new_balance = current_balance + total  # Only add the actual sale amount (excluding change)
        
        await branches.update_one(
            {"id": branch_id},
            {"$set": {"cash_balance": new_balance}}
        )
        
        # Record cash movement
        cash_mov = CashMovement(
            branch_id=branch_id,
            movement_type="cash_in",
            amount=total,
            balance_after=new_balance,
            category="sales",
            description=f"Sale {invoice}",
            reference_id=tx.id,
            reference_type="transaction",
            user_id=user.get("user_id", ""),
            user_name=user.get("name", "")
        )
        await cash_movements.insert_one(cash_mov.model_dump())
    
    # Update customer stats
    if data.customer_id:
        await customers.update_one(
            {"id": data.customer_id},
            {
                "$inc": {
                    "total_spent": total,
                    "total_transactions": 1,
                    "loyalty_points": int(total / 10000)  # 1 point per 10k
                }
            }
        )
    
    return {
        "id": tx.id,
        "invoice_number": invoice,
        "total": total,
        "paid": paid_amount,
        "change": change,
        "message": "Transaction completed"
    }

# ==================== HOLD & RECALL ====================

@router.post("/hold")
async def hold_transaction(data: HoldTransaction, user: dict = Depends(get_current_user)):
    """Hold a transaction for later"""
    branch_id = user.get("branch_id")
    
    held = {
        "id": str(uuid.uuid4()),
        "branch_id": branch_id,
        "cashier_id": user.get("user_id", ""),
        "cashier_name": user.get("name", ""),
        "items": [item.model_dump() for item in data.items],
        "customer_id": data.customer_id,
        "customer_name": data.customer_name,
        "hold_name": data.hold_name or f"Hold-{datetime.now().strftime('%H%M')}",
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await held_transactions.insert_one(held)
    
    return {"id": held["id"], "message": "Transaction held"}

@router.get("/held")
async def list_held_transactions(user: dict = Depends(get_current_user)):
    """List held transactions for current branch"""
    branch_id = user.get("branch_id")
    items = await held_transactions.find(
        {"branch_id": branch_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return items

@router.get("/held/{held_id}")
async def get_held_transaction(held_id: str, user: dict = Depends(get_current_user)):
    """Get a held transaction"""
    held = await held_transactions.find_one({"id": held_id}, {"_id": 0})
    if not held:
        raise HTTPException(status_code=404, detail="Held transaction not found")
    
    # Enrich with product details
    for item in held.get("items", []):
        product = await products.find_one({"id": item["product_id"]}, {"_id": 0})
        if product:
            item["product_name"] = product.get("name", "")
            item["product_code"] = product.get("code", "")
            item["unit_price"] = product.get("selling_price", 0)
    
    return held

@router.delete("/held/{held_id}")
async def delete_held_transaction(held_id: str, user: dict = Depends(get_current_user)):
    """Delete a held transaction"""
    result = await held_transactions.delete_one({"id": held_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Held transaction not found")
    return {"message": "Held transaction deleted"}

# ==================== VOID & RETURN ====================

@router.post("/void/{transaction_id}")
async def void_transaction(transaction_id: str, reason: str = "", user: dict = Depends(get_current_user)):
    """Void a transaction (same day only)"""
    tx = await transactions.find_one({"id": transaction_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Can only void completed transactions")
    
    # Check if same day
    tx_date = tx.get("created_at", "")[:10]
    today = datetime.now(timezone.utc).isoformat()[:10]
    if tx_date != today:
        raise HTTPException(status_code=400, detail="Can only void same-day transactions. Use return for older transactions.")
    
    # Reverse stock
    branch_id = tx.get("branch_id")
    for item in tx.get("items", []):
        await product_stocks.update_one(
            {"product_id": item["product_id"], "branch_id": branch_id},
            {"$inc": {"quantity": item["quantity"], "available": item["quantity"]}}
        )
        
        movement = StockMovement(
            product_id=item["product_id"],
            branch_id=branch_id,
            movement_type=StockMovementType.RETURN,
            quantity=item["quantity"],
            reference_id=transaction_id,
            reference_type="void",
            notes=reason,
            user_id=user.get("user_id", "")
        )
        await stock_movements.insert_one(movement.model_dump())
    
    # Update transaction status
    await transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "status": "voided",
            "notes": f"VOIDED: {reason}",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Reverse cash if applicable
    cash_paid = sum(p.get("amount", 0) for p in tx.get("payments", []) if p.get("method") == "cash")
    if cash_paid > 0:
        branch = await branches.find_one({"id": branch_id}, {"_id": 0})
        new_balance = branch.get("cash_balance", 0) - tx.get("total", 0)
        await branches.update_one({"id": branch_id}, {"$set": {"cash_balance": new_balance}})
        
        cash_mov = CashMovement(
            branch_id=branch_id,
            movement_type="cash_out",
            amount=tx.get("total", 0),
            balance_after=new_balance,
            category="void",
            description=f"Void {tx.get('invoice_number')}",
            reference_id=transaction_id,
            reference_type="void",
            user_id=user.get("user_id", ""),
            user_name=user.get("name", "")
        )
        await cash_movements.insert_one(cash_mov.model_dump())
    
    return {"message": "Transaction voided"}

# ==================== HISTORY ====================

@router.get("/transactions")
async def list_transactions(
    date: str = "",
    status: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """List transactions for current branch"""
    branch_id = user.get("branch_id")
    query = {"branch_id": branch_id}
    
    if date:
        query["created_at"] = {"$regex": f"^{date}"}
    
    if status:
        query["status"] = status
    
    items = await transactions.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await transactions.count_documents(query)
    
    return {"items": items, "total": total}

@router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str, user: dict = Depends(get_current_user)):
    """Get transaction details"""
    tx = await transactions.find_one({"id": transaction_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx

# ==================== DAILY SUMMARY ====================

@router.get("/summary/today")
async def get_today_summary(user: dict = Depends(get_current_user)):
    """Get today's sales summary for current branch"""
    branch_id = user.get("branch_id")
    today = datetime.now(timezone.utc).isoformat()[:10]
    
    pipeline = [
        {
            "$match": {
                "branch_id": branch_id,
                "status": "completed",
                "created_at": {"$regex": f"^{today}"}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_sales": {"$sum": "$total"},
                "total_profit": {"$sum": "$profit"},
                "total_transactions": {"$sum": 1},
                "total_items": {"$sum": {"$size": "$items"}}
            }
        }
    ]
    
    result = await transactions.aggregate(pipeline).to_list(1)
    
    summary = result[0] if result else {
        "total_sales": 0,
        "total_profit": 0,
        "total_transactions": 0,
        "total_items": 0
    }
    
    # Get branch cash balance
    branch = await branches.find_one({"id": branch_id}, {"_id": 0, "cash_balance": 1, "name": 1})
    summary["cash_balance"] = branch.get("cash_balance", 0) if branch else 0
    summary["branch_name"] = branch.get("name", "") if branch else ""
    summary["date"] = today
    
    return summary
