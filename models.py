from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from DB import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    weight = Column(Float)

    order_items = relationship("OrderProduct", back_populates="product")

# class Order(Base):
#     __tablename__ = "orders"

#     id = Column(Integer, primary_key=True, index=True)
#     status = Column(String, default="pending")
#     shipment_amount = Column(Float, default=0.0)
#     total_amount = Column(Float, default=0.0)
#     weight = Column(Float, default=0.0)

#     products = relationship("OrderProduct", back_populates="order")
#     bill = relationship("Bill", back_populates="order", uselist=False)

# class OrderProduct(Base):
#     __tablename__ = "order_products"

#     id = Column(Integer, primary_key=True, index=True)
#     order_id = Column(Integer, ForeignKey("orders.id"))
#     product_id = Column(Integer, ForeignKey("products.id"))
#     quantity = Column(Integer)

#     order = relationship("Order", back_populates="products")
#     product = relationship("Product", back_populates="order_items")

# class Bill(Base):
#     __tablename__ = "bills"

#     id = Column(Integer, primary_key=True, index=True)
#     order_id = Column(Integer, ForeignKey("orders.id"))
#     amount = Column(Float)
#     creation_date = Column(DateTime, default=datetime.utcnow)

#     order = relationship("Order", back_populates="bill")
