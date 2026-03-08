from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid

class ProductBase(BaseModel):
    company_id: str
    branch_id: Optional[str] = None
    name: str
    barcode: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    purchase_price: float = 0.0
    selling_price: float
    stock: int = 0
    min_stock: int = 5
    unit: str = "pcs"
    supplier_id: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    stock: Optional[int] = None
    min_stock: Optional[int] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductResponse(BaseModel):
    id: str
    company_id: str
    branch_id: Optional[str] = None
    name: str
    barcode: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    purchase_price: float
    selling_price: float
    stock: int
    min_stock: int
    unit: str
    is_active: bool
    created_at: datetime
    profit_margin: Optional[float] = None