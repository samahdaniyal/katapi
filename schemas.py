from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

# -------- Product --------
class ProductBase(BaseModel):
    name: str = Field(..., min_length=4)
    price: float
    weight: float

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    class Config:
        orm_mode = True

# -------- Order --------
class OrderProductBase(BaseModel):
    product_id: int
    quantity: int

class OrderProductCreate(OrderProductBase):
    pass

class OrderProductResponse(OrderProductBase):
    id: int
    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    status: str = "pending"

class OrderCreate(OrderBase):
    products: List[OrderProductCreate]

class OrderResponse(OrderBase):
    id: int
    shipment_amount: float
    total_amount: float
    weight: float
    products: List[OrderProductResponse]
    class Config:
        orm_mode = True

# -------- Bill --------
class BillResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    creation_date: datetime
    class Config:
        orm_mode = True
