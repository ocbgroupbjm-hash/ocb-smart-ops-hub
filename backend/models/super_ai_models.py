# OCB GROUP SUPER AI OPERATING SYSTEM - Extended Models
# Enterprise AI System for Sales, CRM, Marketing, CFO, Warroom

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

class ConversationChannel(str, Enum):
    WHATSAPP = "whatsapp"
    INTERNAL_CHAT = "internal_chat"
    WEBSITE = "website"
    MARKETPLACE = "marketplace"

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    WAITING_PAYMENT = "waiting_payment"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    READY_PICKUP = "ready_pickup"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class DeliveryMethod(str, Enum):
    PICKUP = "pickup"
    COURIER = "courier"
    SAME_DAY = "same_day"
    INSTANT = "instant"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    EXPIRED = "expired"
    FAILED = "failed"
    REFUNDED = "refunded"

class CustomerActivity(str, Enum):
    ACTIVE = "active"          # Transaksi dalam 30 hari
    PASSIVE = "passive"        # Tidak transaksi 30-90 hari
    DORMANT = "dormant"        # Tidak transaksi > 90 hari
    NEW = "new"                # Baru pertama kali

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProcessStatus(str, Enum):
    COMPLETED = "completed"
    RETRY = "retry"
    ESCALATION = "escalation"

# ==================== AI SALES CONVERSATION ====================

class SalesMessage(BaseModel):
    id: str = Field(default_factory=gen_id)
    role: str  # "customer", "ai", "human_agent"
    content: str
    message_type: str = "text"  # text, image, product_card, invoice, qris
    metadata: Dict = {}
    timestamp: str = Field(default_factory=now_iso)

class SalesConversation(BaseModel):
    id: str = Field(default_factory=gen_id)
    channel: ConversationChannel = ConversationChannel.INTERNAL_CHAT
    status: ConversationStatus = ConversationStatus.ACTIVE
    
    # Customer Info
    customer_id: Optional[str] = None
    customer_name: str = ""
    customer_phone: str = ""
    customer_whatsapp: str = ""
    
    # Conversation
    messages: List[SalesMessage] = []
    
    # Sales Context
    interested_products: List[str] = []
    recommended_products: List[str] = []
    cart_items: List[Dict] = []  # [{product_id, qty, price}]
    
    # Order
    order_id: Optional[str] = None
    invoice_id: Optional[str] = None
    
    # Branch
    branch_id: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    
    # AI Analysis
    customer_intent: str = ""  # browsing, buying, complaining, asking
    sentiment: str = "neutral"  # positive, neutral, negative
    urgency: str = "normal"  # low, normal, high
    
    # Timestamps
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    last_message_at: str = Field(default_factory=now_iso)

# ==================== INVOICE & PAYMENT ====================

class InvoiceItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    discount: float = 0
    subtotal: float

class Invoice(BaseModel):
    id: str = Field(default_factory=gen_id)
    invoice_number: str
    
    # Customer
    customer_id: Optional[str] = None
    customer_name: str
    customer_phone: str
    customer_email: str = ""
    
    # Items
    items: List[InvoiceItem] = []
    
    # Totals
    subtotal: float = 0
    discount_amount: float = 0
    tax_amount: float = 0
    shipping_cost: float = 0
    total: float = 0
    
    # Payment
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_method: str = ""
    payment_reference: str = ""
    paid_at: Optional[str] = None
    
    # QRIS
    qris_code: str = ""
    qris_image_url: str = ""
    qris_expired_at: Optional[str] = None
    
    # Source
    conversation_id: Optional[str] = None
    channel: str = "internal_chat"
    branch_id: Optional[str] = None
    
    # Timestamps
    due_date: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== ORDER & DELIVERY ====================

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    product_code: str
    quantity: int
    unit_price: float
    subtotal: float
    serial_numbers: List[str] = []

class DeliveryInfo(BaseModel):
    method: DeliveryMethod = DeliveryMethod.PICKUP
    courier_name: str = ""
    tracking_number: str = ""
    pickup_code: str = ""
    
    # Address
    recipient_name: str = ""
    recipient_phone: str = ""
    address: str = ""
    city: str = ""
    postal_code: str = ""
    
    # Status
    shipped_at: Optional[str] = None
    delivered_at: Optional[str] = None
    
    # Pickup
    pickup_branch_id: Optional[str] = None
    pickup_branch_name: str = ""

class Order(BaseModel):
    id: str = Field(default_factory=gen_id)
    order_number: str
    
    # Customer
    customer_id: Optional[str] = None
    customer_name: str
    customer_phone: str
    
    # Items
    items: List[OrderItem] = []
    
    # Totals
    subtotal: float = 0
    discount_amount: float = 0
    tax_amount: float = 0
    shipping_cost: float = 0
    total: float = 0
    
    # Payment
    invoice_id: Optional[str] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING
    
    # Delivery
    delivery: DeliveryInfo = Field(default_factory=DeliveryInfo)
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    
    # Source
    conversation_id: Optional[str] = None
    channel: str = "internal_chat"
    branch_id: Optional[str] = None
    
    # Notes
    customer_notes: str = ""
    internal_notes: str = ""
    
    # Timestamps
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== ENHANCED CRM ====================

class CustomerProfile(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    # Basic Info
    code: str = ""
    name: str
    phone: str
    whatsapp: str = ""
    email: str = ""
    
    # Address
    address: str = ""
    city: str = ""
    province: str = ""
    postal_code: str = ""
    
    # Segmentation
    segment: str = "regular"  # regular, member, vip, reseller, wholesale
    activity_status: CustomerActivity = CustomerActivity.NEW
    
    # Value Metrics
    lifetime_value: float = 0
    total_orders: int = 0
    total_spent: float = 0
    average_order_value: float = 0
    
    # Loyalty
    loyalty_points: int = 0
    loyalty_tier: str = "bronze"  # bronze, silver, gold, platinum
    
    # Credit
    credit_limit: float = 0
    credit_balance: float = 0  # hutang
    store_credit: float = 0    # deposit
    
    # Preferences
    favorite_products: List[str] = []
    favorite_categories: List[str] = []
    preferred_branch_id: Optional[str] = None
    preferred_payment: str = ""
    
    # Communication
    last_contact: Optional[str] = None
    contact_frequency: str = "normal"  # low, normal, high
    preferred_channel: str = "whatsapp"
    opt_in_marketing: bool = True
    
    # Notes
    notes: str = ""
    tags: List[str] = []
    
    # Timestamps
    first_purchase_date: Optional[str] = None
    last_purchase_date: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== AI MARKETING ====================

class MarketingCampaign(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    # Campaign Info
    name: str
    description: str = ""
    campaign_type: str = "broadcast"  # broadcast, promo, reminder, followup
    
    # Target
    target_segments: List[str] = []  # customer segments
    target_activity: List[str] = []  # active, passive, dormant
    target_branches: List[str] = []  # branch ids
    target_customer_ids: List[str] = []  # specific customers
    
    # Content
    message_template: str = ""
    image_url: str = ""
    promo_code: str = ""
    product_ids: List[str] = []
    
    # Channel
    channels: List[str] = ["whatsapp"]  # whatsapp, sms, email, push
    
    # Schedule
    scheduled_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Status
    status: CampaignStatus = CampaignStatus.DRAFT
    
    # Metrics
    total_targets: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    read_count: int = 0
    clicked_count: int = 0
    converted_count: int = 0
    
    # Budget
    budget: float = 0
    spent: float = 0
    
    # Timestamps
    created_by: str = ""
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== BRANCH MONITORING ====================

class BranchMetrics(BaseModel):
    branch_id: str
    branch_name: str
    branch_code: str
    
    # Date
    date: str
    
    # Sales
    total_transactions: int = 0
    total_revenue: float = 0
    total_profit: float = 0
    average_transaction: float = 0
    
    # Products
    products_sold: int = 0
    top_products: List[Dict] = []  # [{product_id, name, qty, revenue}]
    
    # Stock
    total_stock_value: float = 0
    low_stock_count: int = 0
    out_of_stock_count: int = 0
    
    # Cash
    opening_cash: float = 0
    closing_cash: float = 0
    cash_in: float = 0
    cash_out: float = 0
    
    # Performance
    target_revenue: float = 0
    achievement_percent: float = 0
    
    updated_at: str = Field(default_factory=now_iso)

class StockAlert(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    branch_id: str
    branch_name: str
    product_id: str
    product_name: str
    product_code: str
    
    alert_type: str  # low_stock, out_of_stock, overstock, expiring
    current_stock: int
    min_stock: int
    recommended_order: int = 0
    
    is_resolved: bool = False
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    
    created_at: str = Field(default_factory=now_iso)

# ==================== AI CFO / FINANCIAL ANALYSIS ====================

class FinancialSummary(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    # Period
    period_type: str  # daily, weekly, monthly, yearly
    period_start: str
    period_end: str
    branch_id: Optional[str] = None  # None = all branches
    
    # Revenue
    gross_revenue: float = 0
    net_revenue: float = 0
    returns_amount: float = 0
    discounts_amount: float = 0
    
    # Costs
    cost_of_goods: float = 0
    operating_expenses: float = 0
    
    # Profit
    gross_profit: float = 0
    gross_margin_percent: float = 0
    net_profit: float = 0
    net_margin_percent: float = 0
    
    # Cash Flow
    cash_in: float = 0
    cash_out: float = 0
    net_cash_flow: float = 0
    
    # Receivables & Payables
    accounts_receivable: float = 0  # piutang
    accounts_payable: float = 0     # hutang
    
    # Metrics
    transaction_count: int = 0
    average_transaction: float = 0
    customer_count: int = 0
    new_customer_count: int = 0
    
    # Comparison
    prev_period_revenue: float = 0
    revenue_growth_percent: float = 0
    
    created_at: str = Field(default_factory=now_iso)

# ==================== WARROOM ====================

class WarroomSnapshot(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    # Timestamp
    snapshot_time: str = Field(default_factory=now_iso)
    
    # Overall Metrics
    total_branches: int = 0
    active_branches: int = 0
    
    # Today's Sales
    today_revenue: float = 0
    today_transactions: int = 0
    today_profit: float = 0
    
    # Comparison
    yesterday_revenue: float = 0
    revenue_change_percent: float = 0
    
    # Branch Performance
    top_branches: List[Dict] = []  # [{branch_id, name, revenue}]
    bottom_branches: List[Dict] = []
    
    # Stock
    total_stock_value: float = 0
    critical_stock_alerts: int = 0
    
    # Active Sales
    active_conversations: int = 0
    pending_orders: int = 0
    pending_payments: int = 0
    
    # Marketing
    active_campaigns: int = 0
    campaign_conversions: int = 0

# ==================== AUDIT LOG ENHANCED ====================

class SystemAuditLog(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    # Action
    action: str
    module: str
    entity_type: str
    entity_id: str
    
    # User
    user_id: Optional[str] = None
    user_name: str = ""
    user_role: str = ""
    
    # System (for AI actions)
    is_system_action: bool = False
    ai_module: str = ""  # ai_sales, ai_marketing, ai_cfo
    
    # Data
    old_value: Optional[Dict] = None
    new_value: Optional[Dict] = None
    
    # Status
    status: ProcessStatus = ProcessStatus.COMPLETED
    retry_count: int = 0
    error_message: str = ""
    
    # Context
    branch_id: Optional[str] = None
    ip_address: str = ""
    user_agent: str = ""
    
    # Timestamps
    timestamp: str = Field(default_factory=now_iso)

# ==================== WHATSAPP INTEGRATION ====================

class WhatsAppMessage(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    # Message
    message_id: str  # WhatsApp message ID
    conversation_id: str
    
    # Direction
    direction: str  # inbound, outbound
    
    # Sender/Receiver
    from_number: str
    to_number: str
    
    # Content
    message_type: str  # text, image, document, template, interactive
    content: str
    media_url: str = ""
    
    # Template (for outbound)
    template_name: str = ""
    template_params: Dict = {}
    
    # Status
    status: str = "sent"  # sent, delivered, read, failed
    
    # Timestamps
    sent_at: str = Field(default_factory=now_iso)
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
