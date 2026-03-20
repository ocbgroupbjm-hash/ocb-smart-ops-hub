# OCB TITAN - Database Collections & Utilities (Dynamic Multi-Business Support)
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from contextvars import ContextVar

load_dotenv()

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

# Global MongoDB client (shared across all databases)
client = AsyncIOMotorClient(mongo_url)

# Default database name from environment
_default_db_name = os.environ.get('DB_NAME', 'ocb_titan')

# ============================================================
# MULTI-TENANT ISOLATION FIX
# Using contextvars for per-request database isolation
# This ensures each request uses the correct tenant database
# ============================================================
_request_db_name: ContextVar[str] = ContextVar('request_db_name', default=_default_db_name)

def get_active_db_name() -> str:
    """Get the currently active database name for this request"""
    return _request_db_name.get()

def set_active_db_name(db_name: str):
    """Set the active database name for this request context"""
    _request_db_name.set(db_name)

def get_default_db_name() -> str:
    """Get the default database name from environment"""
    return _default_db_name

def set_default_db_name(db_name: str):
    """Set the default database name (updates global default)"""
    global _default_db_name
    _default_db_name = db_name

def get_db():
    """Get the currently active database object for this request"""
    return client[_request_db_name.get()]

def get_db_for_tenant(tenant_id: str):
    """Get database object for a specific tenant (explicit)"""
    return client[tenant_id]

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
roles = _DynamicCollection('roles')

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
    
    # Helper to safely create index (ignore conflicts)
    async def safe_create_index(collection, keys, **kwargs):
        try:
            await db[collection].create_index(keys, **kwargs)
        except Exception as e:
            if "IndexKeySpecsConflict" not in str(e) and "already exists" not in str(e).lower():
                print(f"Warning: Failed to create index on {collection}: {e}")
    
    # Users
    await safe_create_index('users', "email", unique=True)
    await safe_create_index('users', "branch_id")
    
    # Products
    await safe_create_index('products', "code", unique=True)
    await safe_create_index('products', "barcode")
    await safe_create_index('products', "category_id")
    await safe_create_index('products', "name")
    
    # Product Stocks
    await safe_create_index('product_stocks', [("product_id", 1), ("branch_id", 1)], unique=True)
    await safe_create_index('product_stocks', "branch_id")
    
    # Transactions
    await safe_create_index('transactions', "invoice_number", unique=True)
    await safe_create_index('transactions', "branch_id")
    await safe_create_index('transactions', "created_at")
    await safe_create_index('transactions', "customer_id")
    await safe_create_index('transactions', [("branch_id", 1), ("created_at", -1)])
    
    # Customers
    await safe_create_index('customers', "phone")
    await safe_create_index('customers', "code")
    
    # Audit logs
    await safe_create_index('audit_logs', "timestamp")
    await safe_create_index('audit_logs', [("user_id", 1), ("timestamp", -1)])
    
    # Stock movements
    await safe_create_index('stock_movements', [("product_id", 1), ("created_at", -1)])
    await safe_create_index('stock_movements', "branch_id")
    
    # Cash movements
    await safe_create_index('cash_movements', [("branch_id", 1), ("created_at", -1)])
