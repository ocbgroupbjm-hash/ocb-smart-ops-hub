from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class TransactionItemBase(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    profit: float = 0.0

class TransactionItemCreate(TransactionItemBase):
    pass

class TransactionItem(TransactionItemBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class TransactionBase(BaseModel):
    company_id: str
    branch_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    cashier_id: str
    cashier_name: str
    total_amount: float
    total_profit: float = 0.0
    payment_method: str = "cash"  # cash, card, qris, transfer
    payment_status: str = "paid"
    notes: Optional[str] = None

class TransactionCreate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    items: List[TransactionItemCreate]
    payment_method: str = "cash"
    notes: Optional[str] = None

class Transaction(TransactionBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_number: str
    items: List[TransactionItem] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionResponse(BaseModel):
    id: str
    transaction_number: str
    company_id: str
    branch_id: str
    customer_name: Optional[str] = None
    cashier_name: str
    total_amount: float
    total_profit: float
    payment_method: str
    payment_status: str
    items: List[TransactionItem]
    created_at: datetime