from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class ProductBase(BaseModel):
    company_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float
    cost: Optional[float] = None
    sku: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    sku: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float
    cost: Optional[float] = None
    sku: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool
    created_at: datetime