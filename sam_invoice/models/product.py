"""Data model for products."""

from sqlalchemy import Column, Float, Integer, String

from .customer import Base


class Product(Base):
    """Product model with reference, name, price, stock and sold quantity."""

    __tablename__ = "products"

    reference = Column(String, primary_key=True)  # Product reference as PK
    name = Column(String)  # Product name/description
    price = Column(Float)  # Unit price
    stock = Column(Integer)  # Quantity in stock
    sold = Column(Integer)  # Quantity sold
