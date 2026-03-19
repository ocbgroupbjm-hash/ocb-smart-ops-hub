# OCB TITAN RETAIL AI SYSTEM - Database Models
# Enterprise-grade retail operating system for OCB GROUP

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

def gen_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ==================== ENUMS ====================

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    CASHIER = "cashier"
    FINANCE = "finance"
    INVENTORY = "inventory"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    VOIDED = "voided"
    REFUNDED = "refunded"
    HELD = "held"

class PaymentMethod(str, Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    QRIS = "qris"
    EWALLET = "ewallet"
    STORE_CREDIT = "store_credit"
    SPLIT = "split"

class StockMovementType(str, Enum):
    STOCK_IN = "stock_in"
    STOCK_OUT = "stock_out"
    TRANSFER = "transfer"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    SALE = "sale"
    OPNAME = "opname"

class PurchaseStatus(str, Enum):
    DRAFT = "draft"
    ORDERED = "ordered"
    PARTIAL = "partial"
    RECEIVED = "received"
    CANCELLED = "cancelled"

class CustomerSegment(str, Enum):
    REGULAR = "regular"
    MEMBER = "member"
    VIP = "vip"
    RESELLER = "reseller"
    WHOLESALE = "wholesale"

# ==================== USER & AUTH ====================

class User(BaseModel):
    id: str = Field(default_factory=gen_id)
    email: str
    password_hash: str
    name: str
    phone: str = ""
    role: UserRole = UserRole.CASHIER
    branch_id: Optional[str] = None
    branch_ids: List[str] = []  # For multi-branch access
    permissions: List[str] = []
    is_active: bool = True
    last_login: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

class AuditLog(BaseModel):
    id: str = Field(default_factory=gen_id)
    user_id: str
    user_name: str
    action: str
    module: str
    entity_type: str
    entity_id: str
    old_value: Optional[Dict] = None
    new_value: Optional[Dict] = None
    ip_address: str = ""
    branch_id: Optional[str] = None
    timestamp: str = Field(default_factory=now_iso)

# ==================== BRANCH ====================

class Branch(BaseModel):
    id: str = Field(default_factory=gen_id)
    code: str
    name: str
    address: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    is_warehouse: bool = False
    is_active: bool = True
    manager_id: Optional[str] = None
    cash_balance: float = 0.0
    settings: Dict = {}
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== PRODUCT ====================

class ProductCategory(BaseModel):
    id: str = Field(default_factory=gen_id)
    code: str
    name: str
    parent_id: Optional[str] = None
    description: str = ""
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)

class Product(BaseModel):
    id: str = Field(default_factory=gen_id)
    code: str
    barcode: str = ""
    name: str
    description: str = ""
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    brand: str = ""
    unit: str = "pcs"
    
    # Pricing
    cost_price: float = 0.0
    selling_price: float = 0.0
    wholesale_price: float = 0.0
    member_price: float = 0.0
    reseller_price: float = 0.0
    price_tiers: List[Dict] = []  # [{min_qty, price}]
    
    # Stock
    track_stock: bool = True
    min_stock: int = 5
    
    # Flags
    is_bundle: bool = False
    bundle_items: List[Dict] = []  # [{product_id, qty}]
    track_serial: bool = False
    is_service: bool = False
    is_active: bool = True
    
    # Tax
    tax_rate: float = 0.0
    
    image_url: str = ""
    tags: List[str] = []
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

class ProductStock(BaseModel):
    id: str = Field(default_factory=gen_id)
    product_id: str
    branch_id: str
    quantity: int = 0
    reserved: int = 0  # Reserved for pending orders
    available: int = 0  # quantity - reserved
    unit_cost: float = 0.0  # HPP per unit per warehouse (weighted average)
    total_value: float = 0.0  # quantity * unit_cost
    last_restock: Optional[str] = None
    updated_at: str = Field(default_factory=now_iso)

class StockMovement(BaseModel):
    id: str = Field(default_factory=gen_id)
    product_id: str
    branch_id: str
    movement_type: StockMovementType
    quantity: int
    reference_id: Optional[str] = None  # Transaction ID, Transfer ID, etc
    reference_type: str = ""
    from_branch_id: Optional[str] = None
    to_branch_id: Optional[str] = None
    cost_price: float = 0.0
    notes: str = ""
    user_id: str
    created_at: str = Field(default_factory=now_iso)

# ==================== CUSTOMER ====================

class Customer(BaseModel):
    id: str = Field(default_factory=gen_id)
    code: str = ""
    name: str
    phone: str
    email: str = ""
    address: str = ""
    city: str = ""
    segment: CustomerSegment = CustomerSegment.REGULAR
    
    # Loyalty
    loyalty_points: int = 0
    total_spent: float = 0.0
    total_transactions: int = 0
    
    # Credit
    credit_limit: float = 0.0
    credit_balance: float = 0.0  # Amount owed
    store_credit: float = 0.0  # Prepaid balance
    
    notes: str = ""
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== SUPPLIER ====================

class Supplier(BaseModel):
    id: str = Field(default_factory=gen_id)
    code: str
    name: str
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    city: str = ""
    
    # Financial
    debt_balance: float = 0.0
    credit_limit: float = 0.0
    payment_terms: int = 30  # Days
    
    bank_name: str = ""
    bank_account: str = ""
    bank_holder: str = ""
    
    notes: str = ""
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== POS TRANSACTION ====================

class TransactionItem(BaseModel):
    product_id: str
    product_code: str
    product_name: str
    quantity: int
    unit_price: float
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    subtotal: float
    total: float
    cost_price: float = 0.0
    serial_numbers: List[str] = []

class PaymentDetail(BaseModel):
    method: PaymentMethod
    amount: float
    reference: str = ""
    account_number: str = ""

class Transaction(BaseModel):
    id: str = Field(default_factory=gen_id)
    invoice_number: str
    branch_id: str
    cashier_id: str
    cashier_name: str
    
    # Customer
    customer_id: Optional[str] = None
    customer_name: str = ""
    customer_phone: str = ""
    
    # Items
    items: List[TransactionItem] = []
    
    # Totals
    subtotal: float = 0.0
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    
    # Payment
    payments: List[PaymentDetail] = []
    paid_amount: float = 0.0
    change_amount: float = 0.0
    
    # Status
    status: TransactionStatus = TransactionStatus.COMPLETED
    
    # Credit Sale Fields
    is_credit: bool = False
    credit_due_days: int = 30
    ar_id: Optional[str] = None
    
    # Profit
    total_cost: float = 0.0
    profit: float = 0.0
    
    # Meta
    notes: str = ""
    held_name: str = ""  # For held transactions
    original_transaction_id: Optional[str] = None  # For returns
    
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== PURCHASE ====================

class PurchaseOrderItem(BaseModel):
    product_id: str
    product_code: str
    product_name: str
    quantity: int
    received_qty: int = 0
    unit_cost: float
    discount_percent: float = 0.0
    subtotal: float
    unit: str = "pcs"  # Purchase unit
    conversion_ratio: float = 1.0  # Conversion to base unit
    sn_start: str = ""  # Serial number start
    sn_end: str = ""  # Serial number end

class PurchaseOrder(BaseModel):
    id: str = Field(default_factory=gen_id)
    po_number: str
    supplier_id: str
    supplier_name: str
    branch_id: str
    warehouse_id: str = ""  # Single warehouse for all items
    warehouse_name: str = ""
    pic_id: str = ""  # Person in Charge
    pic_name: str = ""
    payment_account_id: str = ""  # Cash/Bank account
    payment_account_name: str = ""
    
    items: List[PurchaseOrderItem] = []
    
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    
    paid_amount: float = 0.0
    
    status: PurchaseStatus = PurchaseStatus.DRAFT
    
    order_date: str = Field(default_factory=now_iso)
    expected_date: Optional[str] = None
    received_date: Optional[str] = None
    
    notes: str = ""
    user_id: str
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== FINANCE ====================

class CashMovement(BaseModel):
    id: str = Field(default_factory=gen_id)
    branch_id: str
    movement_type: str  # cash_in, cash_out, opening, closing
    amount: float
    balance_after: float
    category: str = ""
    description: str
    reference_id: Optional[str] = None
    reference_type: str = ""
    user_id: str
    user_name: str
    created_at: str = Field(default_factory=now_iso)

class Expense(BaseModel):
    id: str = Field(default_factory=gen_id)
    branch_id: str
    category: str
    description: str
    amount: float
    payment_method: str = "cash"
    reference: str = ""
    date: str = Field(default_factory=now_iso)
    user_id: str
    created_at: str = Field(default_factory=now_iso)

# ==================== JOURNAL ENTRY ====================

class JournalEntry(BaseModel):
    id: str = Field(default_factory=gen_id)
    entry_number: str
    date: str
    description: str
    branch_id: Optional[str] = None
    
    debit_account: str
    credit_account: str
    amount: float
    
    reference_type: str = ""
    reference_id: Optional[str] = None
    
    user_id: str
    created_at: str = Field(default_factory=now_iso)

# ==================== PROMOTION ====================

class Promotion(BaseModel):
    id: str = Field(default_factory=gen_id)
    code: str
    name: str
    description: str = ""
    
    # Type: percentage, fixed, buy_x_get_y, bundle
    promo_type: str = "percentage"
    value: float = 0.0
    
    # Conditions
    min_purchase: float = 0.0
    min_qty: int = 0
    applicable_products: List[str] = []  # Empty = all products
    applicable_categories: List[str] = []
    applicable_branches: List[str] = []  # Empty = all branches
    applicable_segments: List[str] = []
    
    # Dates
    start_date: str
    end_date: str
    
    is_active: bool = True
    usage_limit: int = 0  # 0 = unlimited
    used_count: int = 0
    
    created_at: str = Field(default_factory=now_iso)

# ==================== STOCK TRANSFER ====================

class StockTransfer(BaseModel):
    id: str = Field(default_factory=gen_id)
    transfer_number: str
    from_branch_id: str
    from_branch_name: str
    to_branch_id: str
    to_branch_name: str
    
    items: List[Dict] = []  # [{product_id, product_name, quantity}]
    
    status: str = "pending"  # pending, in_transit, received, cancelled
    
    notes: str = ""
    requested_by: str
    approved_by: Optional[str] = None
    received_by: Optional[str] = None
    
    request_date: str = Field(default_factory=now_iso)
    sent_date: Optional[str] = None
    received_date: Optional[str] = None
    
    created_at: str = Field(default_factory=now_iso)

# ==================== STOCK OPNAME ====================

class StockOpname(BaseModel):
    id: str = Field(default_factory=gen_id)
    opname_number: str
    branch_id: str
    
    items: List[Dict] = []  # [{product_id, system_qty, actual_qty, difference}]
    
    status: str = "draft"  # draft, in_progress, completed, approved
    
    notes: str = ""
    conducted_by: str
    approved_by: Optional[str] = None
    
    start_date: str = Field(default_factory=now_iso)
    completed_date: Optional[str] = None
    
    created_at: str = Field(default_factory=now_iso)
