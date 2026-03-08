from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models_ocb.transaction import TransactionCreate, TransactionResponse, Transaction, TransactionItem
from database import db
from utils.dependencies import get_current_user
from datetime import datetime, timezone
import random
import string

router = APIRouter(prefix="/pos/transactions", tags=["POS - Transactions"])

def generate_transaction_number():
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"TRX-{date_str}-{random_str}"

@router.post("/", response_model=TransactionResponse)
async def create_transaction(transaction_data: TransactionCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    branch_id = current_user.get("branch_id")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="User must be associated with a company")
    
    # Calculate totals
    total_amount = 0
    total_profit = 0
    transaction_items = []
    
    for item in transaction_data.items:
        # Get product details
        product = await db.products.find_one({"id": item.product_id, "company_id": company_id}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        # Check stock
        if product['stock'] < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product['name']}")
        
        # Calculate item totals
        subtotal = item.quantity * item.unit_price
        item_profit = (item.unit_price - product['purchase_price']) * item.quantity
        
        total_amount += subtotal
        total_profit += item_profit
        
        transaction_items.append(TransactionItem(
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=subtotal,
            profit=item_profit
        ))
        
        # Update product stock
        new_stock = product['stock'] - item.quantity
        await db.products.update_one(
            {"id": item.product_id},
            {"$set": {"stock": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    # Create transaction
    transaction = Transaction(
        company_id=company_id,
        branch_id=branch_id or "",
        customer_id=transaction_data.customer_id,
        customer_name=transaction_data.customer_name,
        cashier_id=current_user['id'],
        cashier_name=current_user['full_name'],
        total_amount=total_amount,
        total_profit=total_profit,
        payment_method=transaction_data.payment_method,
        payment_status="paid",
        notes=transaction_data.notes,
        transaction_number=generate_transaction_number(),
        items=transaction_items
    )
    
    transaction_dict = transaction.model_dump()
    transaction_dict['created_at'] = transaction_dict['created_at'].isoformat()
    
    await db.transactions.insert_one(transaction_dict)
    
    return TransactionResponse(**transaction.model_dump())

@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    branch_id: str = None,
    date_from: str = None,
    date_to: str = None,
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("company_id")
    query = {"company_id": company_id}
    
    if branch_id:
        query["branch_id"] = branch_id
    
    if date_from and date_to:
        query["created_at"] = {
            "$gte": f"{date_from}T00:00:00",
            "$lte": f"{date_to}T23:59:59"
        }
    
    transactions = await db.transactions.find(query, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    
    for txn in transactions:
        if isinstance(txn.get('created_at'), str):
            txn['created_at'] = datetime.fromisoformat(txn['created_at'])
    
    return transactions

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    transaction = await db.transactions.find_one({"id": transaction_id, "company_id": company_id}, {"_id": 0})
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if isinstance(transaction.get('created_at'), str):
        transaction['created_at'] = datetime.fromisoformat(transaction['created_at'])
    
    return transaction