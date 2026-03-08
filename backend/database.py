# OCB TITAN - Database Collections & Utilities
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'ocb_titan')

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# ==================== COLLECTIONS ====================

# Core
users = db['users']
branches = db['branches']
audit_logs = db['audit_logs']

# Products & Inventory
categories = db['categories']
products = db['products']
product_stocks = db['product_stocks']
stock_movements = db['stock_movements']
stock_transfers = db['stock_transfers']
stock_opnames = db['stock_opnames']

# Sales & POS
transactions = db['transactions']
held_transactions = db['held_transactions']
customers = db['customers']
promotions = db['promotions']

# Purchase
suppliers = db['suppliers']
purchase_orders = db['purchase_orders']

# Finance
cash_movements = db['cash_movements']
expenses = db['expenses']
journal_entries = db['journal_entries']

# Analytics
daily_summaries = db['daily_summaries']
branch_summaries = db['branch_summaries']

# Sequences for auto-numbering
sequences = db['sequences']

async def get_next_sequence(name: str, prefix: str = "") -> str:
    """Get next sequence number for invoices, POs, etc."""
    result = await sequences.find_one_and_update(
        {"_id": name},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True
    )
    num = result.get("value", 1)
    if prefix:
        return f"{prefix}{num:06d}"
    return f"{num:06d}"

async def init_indexes():
    """Create database indexes for performance"""
    # Users
    await users.create_index("email", unique=True)
    await users.create_index("branch_id")
    
    # Products
    await products.create_index("code", unique=True)
    await products.create_index("barcode")
    await products.create_index("category_id")
    await products.create_index("name")
    
    # Product Stocks
    await product_stocks.create_index([("product_id", 1), ("branch_id", 1)], unique=True)
    await product_stocks.create_index("branch_id")
    
    # Transactions
    await transactions.create_index("invoice_number", unique=True)
    await transactions.create_index("branch_id")
    await transactions.create_index("created_at")
    await transactions.create_index("customer_id")
    await transactions.create_index([("branch_id", 1), ("created_at", -1)])
    
    # Customers
    await customers.create_index("phone")
    await customers.create_index("code")
    
    # Audit logs
    await audit_logs.create_index("timestamp")
    await audit_logs.create_index([("user_id", 1), ("timestamp", -1)])
    
    # Stock movements
    await stock_movements.create_index([("product_id", 1), ("created_at", -1)])
    await stock_movements.create_index("branch_id")
    
    # Cash movements
    await cash_movements.create_index([("branch_id", 1), ("created_at", -1)])
