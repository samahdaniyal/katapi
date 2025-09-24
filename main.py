from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import models
import schemas
from DB import engine, Base, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Katapi with SQLite")

# ---------- Startup Event ----------
@app.on_event("startup")
def seed_data():
    db = next(get_db())

    # Seed products if DB is empty
    if db.query(models.Product).count() == 0:
        laptop = models.Product(name="Laptop", price=1200.50, weight=2.5)
        phone = models.Product(name="Smartphone", price=800.00, weight=0.4)
        headphones = models.Product(name="Headphones", price=150.75, weight=0.2)
        db.add_all([laptop, phone, headphones])
        db.commit()

        # Create a demo order with some products
        order = models.Order(status="paid")
        db.add(order)
        db.commit()
        db.refresh(order)

        # Add products to the order
        order_items = [
            models.OrderProduct(order_id=order.id, product_id=laptop.id, quantity=1),
            models.OrderProduct(order_id=order.id, product_id=phone.id, quantity=2),
        ]
        db.add_all(order_items)
        db.commit()

        # Calculate totals for order
        total_amount = laptop.price * 1 + phone.price * 2
        total_weight = laptop.weight * 1 + phone.weight * 2
        shipment_amount = (int(total_weight // 10) + (1 if total_weight % 10 else 0)) * 25 if total_weight else 0
        total_amount_with_shipping = total_amount + shipment_amount

        # Update order
        order.total_amount = total_amount_with_shipping
        order.shipment_amount = shipment_amount
        order.weight = total_weight
        db.commit()

        # Add a bill since status is "paid"
        bill = models.Bill(order_id=order.id, amount=order.total_amount)
        db.add(bill)
        db.commit()

        print("Demo products, order, and bill added!")


# ---------- Products ----------
@app.get("/")
def root():
    return {"message": "Katapi API is running. See /docs for API documentation."}

@app.post("/products", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products", response_model=list[schemas.ProductResponse])
def list_products(db: Session = Depends(get_db), sort_by: str = None):
    query = db.query(models.Product)
    if sort_by in {"name", "price", "weight"}:
        query = query.order_by(getattr(models.Product, sort_by))
    return query.all()

@app.get("/products/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    return product

@app.put("/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int, updated: schemas.ProductCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    product.name, product.price, product.weight = updated.name, updated.price, updated.weight
    db.commit()
    db.refresh(product)
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}


# ---------- Orders ----------
def calculate_order_totals(db: Session, products_data):
    total_price = total_weight = 0
    for item in products_data:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(404, f"Product {item.product_id} not found")
        total_price += product.price * item.quantity
        total_weight += product.weight * item.quantity
    if total_price > 1000:
        total_price *= 0.95
    shipment_amount = (int(total_weight // 10) + (1 if total_weight % 10 else 0)) * 25 if total_weight else 0
    return total_price + shipment_amount, total_weight, shipment_amount

@app.post("/orders", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    total_amount, weight, shipment_amount = calculate_order_totals(db, order.products)
    db_order = models.Order(status=order.status, shipment_amount=shipment_amount,
                            total_amount=total_amount, weight=weight)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    # Save order products
    for item in order.products:
        db_item = models.OrderProduct(order_id=db_order.id, product_id=item.product_id, quantity=item.quantity)
        db.add(db_item)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.put("/orders/{order_id}", response_model=schemas.OrderResponse)
def update_order(order_id: int, order: schemas.OrderCreate, db: Session = Depends(get_db)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(404, "Order not found")
    total_amount, weight, shipment_amount = calculate_order_totals(db, order.products)
    db_order.status, db_order.shipment_amount, db_order.total_amount, db_order.weight = order.status, shipment_amount, total_amount, weight
    db.query(models.OrderProduct).filter(models.OrderProduct.order_id == order_id).delete()
    for item in order.products:
        db_item = models.OrderProduct(order_id=order_id, product_id=item.product_id, quantity=item.quantity)
        db.add(db_item)
    db.commit()
    db.refresh(db_order)
    if order.status == "paid":
        bill = models.Bill(order_id=db_order.id, amount=db_order.total_amount, creation_date=datetime.utcnow())
        db.add(bill)
        db.commit()
    return db_order

@app.get("/orders", response_model=list[schemas.OrderResponse])
def list_orders(db: Session = Depends(get_db)):
    return db.query(models.Order).all()

# ---------- Bills ----------
@app.get("/bills", response_model=list[schemas.BillResponse])
def list_bills(db: Session = Depends(get_db)):
    return db.query(models.Bill).all()
