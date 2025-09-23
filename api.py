from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import itertools

app = FastAPI(title="Katapi")

# ----------------------------
# Data Models
# ----------------------------
class Product(BaseModel):
    id: int
    name: str = Field(..., min_length=4)  # must be longer than 3 chars
    price: float
    weight: float

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=4)
    price: float
    weight: float

class OrderProduct(BaseModel):
    product_id: int
    quantity: int

class Order(BaseModel):
    id: int
    status: str  # pending, paid, canceled
    products: List[OrderProduct]
    shipment_amount: float
    total_amount: float
    weight: float

class OrderCreate(BaseModel):
    products: List[OrderProduct]
    status: str = "pending"

class Bill(BaseModel):
    id: int
    order_id: int
    amount: float
    creation_date: datetime

# ----------------------------
# In-Memory Storage
# ----------------------------
products_db: List[Product] = []
orders_db: List[Order] = []
bills_db: List[Bill] = []

product_id_counter = itertools.count(1)
order_id_counter = itertools.count(1)
bill_id_counter = itertools.count(1)

# ----------------------------
# Helper functions
# ----------------------------
def calculate_order_totals(order_products: List[OrderProduct]):
    total_price = 0.0
    total_weight = 0.0

    for op in order_products:
        product = next((p for p in products_db if p.id == op.product_id), None)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {op.product_id} not found")
        total_price += product.price * op.quantity
        total_weight += product.weight * op.quantity

    # Apply discount if > 1000€
    if total_price > 1000:
        total_price *= 0.95

    # Shipment: 25€ per 10kg
    shipment_amount = (int(total_weight // 10) + (1 if total_weight % 10 else 0)) * 25 if total_weight > 0 else 0

    total_amount = total_price + shipment_amount
    return total_price, total_weight, shipment_amount, total_amount


# ----------------------------
# Product Routes
# ----------------------------
@app.get("/products")
def list_products(sort_by: Optional[str] = None):
    if sort_by in {"name", "price", "weight"}:
        return sorted(products_db, key=lambda p: getattr(p, sort_by))
    return products_db

@app.post("/products", response_model=Product)
def create_product(product: ProductCreate):
    new_product = Product(id=next(product_id_counter), **product.dict())
    products_db.append(new_product)
    return new_product

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    product = next((p for p in products_db if p.id == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, product: ProductCreate):
    existing = next((p for p in products_db if p.id == product_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    existing.name = product.name
    existing.price = product.price
    existing.weight = product.weight
    return existing

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    global products_db
    products_db = [p for p in products_db if p.id != product_id]
    return {"message": "Product deleted"}

# ----------------------------
# Order Routes
# ----------------------------
@app.post("/orders", response_model=Order)
def create_order(order: OrderCreate):
    total_price, total_weight, shipment_amount, total_amount = calculate_order_totals(order.products)
    new_order = Order(
        id=next(order_id_counter),
        status=order.status,
        products=order.products,
        shipment_amount=shipment_amount,
        total_amount=total_amount,
        weight=total_weight,
    )
    orders_db.append(new_order)
    return new_order

@app.get("/orders", response_model=List[Order])
def list_orders():
    return orders_db

@app.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, order: OrderCreate):
    existing = next((o for o in orders_db if o.id == order_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")

    total_price, total_weight, shipment_amount, total_amount = calculate_order_totals(order.products)
    existing.products = order.products
    existing.status = order.status
    existing.shipment_amount = shipment_amount
    existing.total_amount = total_amount
    existing.weight = total_weight

    # Automatically generate bill if paid
    if order.status == "paid":
        new_bill = Bill(
            id=next(bill_id_counter),
            order_id=existing.id,
            amount=existing.total_amount,
            creation_date=datetime.now(),
        )
        bills_db.append(new_bill)

    return existing

@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    global orders_db
    orders_db = [o for o in orders_db if o.id != order_id]
    return {"message": "Order deleted"}

# ----------------------------
# Bill Routes
# ----------------------------
@app.get("/bills", response_model=List[Bill])
def list_bills():
    return bills_db
