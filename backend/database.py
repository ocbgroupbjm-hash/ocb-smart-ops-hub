# OCB TITAN - Database Collections & Utilities (Dynamic Multi-Business Support)
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

# Global MongoDB client (shared across all databases)
client = AsyncIOMotorClient(mongo_url)

# Active database name - can be changed at runtime
_active_db_name = os.environ.get('DB_NAME', 'ocb_titan')

def get_active_db_name() -> str:
    """Get the currently active database name"""
    return _active_db_name

def set_active_db_name(db_name: str):
    """Set the active database name (called when switching business)"""
    global _active_db_name
    _active_db_name = db_name

def get_db():
    """Get the currently active database object"""
    return client[_active_db_name]

# ==================== DYNAMIC COLLECTION GETTERS ====================

def get_users():
    return get_db()['users']

def get_branches():
    return get_db()['branches']

def get_audit_logs():
    return get_db()['audit_logs']

def get_categories():
    return get_db()['categories']

def get_products():
    return get_db()['products']

def get_product_stocks():
    return get_db()['product_stocks']

def get_stock_movements():
    return get_db()['stock_movements']

def get_stock_transfers():
    return get_db()['stock_transfers']

def get_stock_opnames():
    return get_db()['stock_opnames']

def get_transactions():
    return get_db()['transactions']

def get_held_transactions():
    return get_db()['held_transactions']

def get_customers():
    return get_db()['customers']

def get_promotions():
    return get_db()['promotions']

def get_suppliers():
    return get_db()['suppliers']

def get_purchase_orders():
    return get_db()['purchase_orders']

def get_cash_movements():
    return get_db()['cash_movements']

def get_expenses():
    return get_db()['expenses']

def get_journal_entries():
    return get_db()['journal_entries']

def get_daily_summaries():
    return get_db()['daily_summaries']

def get_branch_summaries():
    return get_db()['branch_summaries']

def get_sequences():
    return get_db()['sequences']

# Backward compatibility - create proxy objects that always use active db
# These work by getting the collection fresh each time they're accessed

class _DynamicCollection:
    """Proxy class that always returns collection from active database"""
    def __init__(self, collection_name: str):
        self._collection_name = collection_name
    
    def __getattr__(self, name):
        return getattr(get_db()[self._collection_name], name)
    
    def __call__(self, *args, **kwargs):
        return get_db()[self._collection_name](*args, **kwargs)

class _DynamicDb:
    """Proxy class that always returns active database"""
    def __getitem__(self, collection_name):
        return get_db()[collection_name]
    
    def __getattr__(self, name):
        return getattr(get_db(), name)

# Dynamic database and collection references
db = _DynamicDb()
users = _DynamicCollection('users')
branches = _DynamicCollection('branches')
audit_logs = _DynamicCollection('audit_logs')
categories = _DynamicCollection('categories')
products = _DynamicCollection('products')
product_stocks = _DynamicCollection('product_stocks')
stock_movements = _DynamicCollection('stock_movements')
stock_transfers = _DynamicCollection('stock_transfers')
stock_opnames = _DynamicCollection('stock_opnames')
transactions = _DynamicCollection('transactions')
held_transactions = _DynamicCollection('held_transactions')
customers = _DynamicCollection('customers')
promotions = _DynamicCollection('promotions')
suppliers = _DynamicCollection('suppliers')
purchase_orders = _DynamicCollection('purchase_orders')
cash_movements = _DynamicCollection('cash_movements')
expenses = _DynamicCollection('expenses')
journal_entries = _DynamicCollection('journal_entries')
daily_summaries = _DynamicCollection('daily_summaries')
branch_summaries = _DynamicCollection('branch_summaries')
sequences = _DynamicCollection('sequences')

# Aliases for different naming conventions used in some routes
customers_collection = customers
branches_collection = branches
sales_orders_collection = _DynamicCollection('sales_orders')
conversations_collection = _DynamicCollection('conversations')
messages_collection = _DynamicCollection('messages')
knowledge_base_collection = _DynamicCollection('knowledge_base')

async def get_next_sequence(name: str, prefix: str = "") -> str:
    """Get next sequence number for invoices, POs, etc."""
    seq_col = get_sequences()
    result = await seq_col.find_one_and_update(
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
    db = get_db()
    # Users
    await db['users'].create_index("email", unique=True)
    await db['users'].create_index("branch_id")
    
    # Products
    await db['products'].create_index("code", unique=True)
    await db['products'].create_index("barcode")
    await db['products'].create_index("category_id")
    await db['products'].create_index("name")
    
    # Product Stocks
    await db['product_stocks'].create_index([("product_id", 1), ("branch_id", 1)], unique=True)
    await db['product_stocks'].create_index("branch_id")
    
    # Transactions
    await db['transactions'].create_index("invoice_number", unique=True)
    await db['transactions'].create_index("branch_id")
    await db['transactions'].create_index("created_at")
    await db['transactions'].create_index("customer_id")
    await db['transactions'].create_index([("branch_id", 1), ("created_at", -1)])
    
    # Customers
    await db['customers'].create_index("phone")
    await db['customers'].create_index("code")
    
    # Audit logs
    await db['audit_logs'].create_index("timestamp")
    await db['audit_logs'].create_index([("user_id", 1), ("timestamp", -1)])
    
    # Stock movements
    await db['stock_movements'].create_index([("product_id", 1), ("created_at", -1)])
    await db['stock_movements'].create_index("branch_id")
    
    # Cash movements
    await db['cash_movements'].create_index([("branch_id", 1), ("created_at", -1)])
