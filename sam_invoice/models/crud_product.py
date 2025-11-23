"""CRUD operations for products."""

from sqlalchemy import func

from . import database
from .product import Product


def create_product(
    reference: str, name: str = None, price: float | None = None, stock: int | None = None, sold: int | None = None
):
    """Create a new product in the database."""
    session = database.SessionLocal()
    try:
        prod = Product(reference=reference, name=name, price=price, stock=stock, sold=sold)
        session.add(prod)
        session.commit()
        session.refresh(prod)
        return prod
    finally:
        session.close()


def get_products():
    """Retrieve all products, sorted by reference."""
    session = database.SessionLocal()
    try:
        return session.query(Product).order_by(func.lower(Product.reference)).all()
    finally:
        session.close()


def search_products(query: str, limit: int | None = None):
    """Search for products by exact ID or partial match on reference/name.

    Args:
        query: Search text
        limit: Maximum number of results (None = no limit)

    Returns:
        List of matching Product objects
    """
    session = database.SessionLocal()
    try:
        q = (query or "").strip()

        # If no search query, return all products
        if not q:
            stmt = session.query(Product).order_by(func.lower(Product.reference))
            return stmt.limit(limit).all() if limit else stmt.all()

        # Build search filters
        filters = [
            Product.reference.ilike(f"%{q}%"),
            Product.name.ilike(f"%{q}%"),
        ]

        # Add ID filter if search is numeric
        try:
            filters.append(Product.id == int(q))
        except ValueError:
            pass

        # Execute search
        from sqlalchemy import or_

        stmt = session.query(Product).filter(or_(*filters)).order_by(func.lower(Product.reference))
        return stmt.limit(limit).all() if limit else stmt.all()
    finally:
        session.close()


def get_product_by_id(product_id: int):
    """Retrieve a product by its ID."""
    session = database.SessionLocal()
    try:
        return session.query(Product).filter(Product.id == product_id).first()
    finally:
        session.close()


def update_product(
    product_id: int, reference: str = None, name: str = None, price: float = None, stock: int = None, sold: int = None
):
    """Update information for an existing product."""
    session = database.SessionLocal()
    try:
        prod = session.query(Product).filter(Product.id == product_id).first()
        if prod:
            if reference is not None:
                prod.reference = reference
            if name is not None:
                prod.name = name
            if price is not None:
                prod.price = price
            if stock is not None:
                prod.stock = stock
            if sold is not None:
                prod.sold = sold
            session.commit()
            session.refresh(prod)
        return prod
    finally:
        session.close()


def delete_product(product_id: int):
    """Delete a product from the database."""
    session = database.SessionLocal()
    try:
        prod = session.query(Product).filter(Product.id == product_id).first()
        if prod:
            session.delete(prod)
            session.commit()
        return prod
    finally:
        session.close()
