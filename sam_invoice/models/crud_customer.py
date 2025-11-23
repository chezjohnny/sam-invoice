"""CRUD operations for customers."""

from sqlalchemy import func, or_

from . import database
from .customer import Customer


def create_customer(name: str, address: str, email: str):
    """Create a new customer in the database."""
    session = database.SessionLocal()
    try:
        customer = Customer(name=name, address=address, email=email)
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return customer
    finally:
        session.close()


def get_customers():
    """Retrieve all customers, sorted by name (case-insensitive)."""
    session = database.SessionLocal()
    try:
        return session.query(Customer).order_by(func.lower(Customer.name)).all()
    finally:
        session.close()


def search_customers(query: str, limit: int | None = None):
    """Search for customers by exact ID or partial match on name, address, email.

    Args:
        query: Search text
        limit: Maximum number of results (None = no limit)

    Returns:
        List of matching Customer objects
    """
    session = database.SessionLocal()
    try:
        q = (query or "").strip()

        # If no search query, return all customers
        if not q:
            stmt = session.query(Customer).order_by(func.lower(Customer.name))
            return stmt.limit(limit).all() if limit else stmt.all()

        # Build search filters
        filters = [
            Customer.name.ilike(f"%{q}%"),
            Customer.email.ilike(f"%{q}%"),
            Customer.address.ilike(f"%{q}%"),
        ]

        # Add ID filter if search is numeric
        try:
            filters.append(Customer.id == int(q))
        except ValueError:
            pass

        # Execute search
        stmt = session.query(Customer).filter(or_(*filters)).order_by(func.lower(Customer.name))
        return stmt.limit(limit).all() if limit else stmt.all()
    finally:
        session.close()


def get_customer_by_id(customer_id: int):
    """Retrieve a customer by their ID."""
    session = database.SessionLocal()
    try:
        return session.query(Customer).filter(Customer.id == customer_id).first()
    finally:
        session.close()


def update_customer(customer_id: int, name: str = None, address: str = None, email: str = None):
    """Update information of an existing customer."""
    session = database.SessionLocal()
    try:
        customer = session.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            if name:
                customer.name = name
            if address:
                customer.address = address
            if email:
                customer.email = email
            session.commit()
            session.refresh(customer)
        return customer
    finally:
        session.close()


def delete_customer(customer_id: int):
    """Delete a customer from the database."""
    session = database.SessionLocal()
    try:
        customer = session.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            session.delete(customer)
            session.commit()
        return customer
    finally:
        session.close()
