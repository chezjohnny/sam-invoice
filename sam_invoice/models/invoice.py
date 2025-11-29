"""Data model for invoices."""

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .customer import Base


class Invoice(Base):
    """Invoice model.

    Stores a snapshot of client details to ensure historical accuracy.
    """

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    reference = Column(String, unique=True, nullable=False)
    date = Column(Date, nullable=False)
    due_date = Column(Date)

    # Customer relationship
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    # Customer snapshot (for historical accuracy)
    customer_name = Column(String, nullable=False)
    customer_address = Column(String)

    # Totals
    subtotal = Column(Float, default=0.0)  # Total HT
    tax = Column(Float, default=0.0)  # Total TVA
    total = Column(Float, default=0.0)  # Total TTC

    # Relationships
    customer = relationship("Customer", foreign_keys=[customer_id])
    # TODO: explain
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin")


class InvoiceItem(Base):
    """Invoice item model."""

    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.reference"), nullable=True)  # NULL for custom items

    product_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product", foreign_keys=[product_id])  # Link to product catalog
