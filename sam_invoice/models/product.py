"""Data model for products."""

from sqlalchemy import Column, Float, Integer, String

from .customer import Base


class Product(Base):
    """Product model with reference, name, price, stock and sold quantity."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    reference = Column(String, unique=True, nullable=False)  # Product reference
    name = Column(String)  # Product name/description
    price = Column(Float)  # Unit price
    stock = Column(Integer)  # Quantity in stock
    sold = Column(Integer)  # Quantity sold
