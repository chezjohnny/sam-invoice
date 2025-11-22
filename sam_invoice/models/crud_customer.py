"""Opérations CRUD pour les clients."""

from sqlalchemy import func, or_

from . import database
from .customer import Customer


def create_customer(name: str, address: str, email: str):
    """Créer un nouveau client dans la base de données."""
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
    """Récupérer tous les clients, triés par nom (insensible à la casse)."""
    session = database.SessionLocal()
    try:
        return session.query(Customer).order_by(func.lower(Customer.name)).all()
    finally:
        session.close()


def search_customers(query: str, limit: int | None = None):
    """Rechercher des clients par ID exact ou par correspondance partielle sur nom, adresse, email.

    Args:
        query: Texte de recherche
        limit: Nombre maximum de résultats (None = pas de limite)

    Returns:
        Liste d'objets Customer correspondants
    """
    session = database.SessionLocal()
    try:
        q = (query or "").strip()

        # Si pas de recherche, retourner tous les clients
        if not q:
            stmt = session.query(Customer).order_by(func.lower(Customer.name))
            return stmt.limit(limit).all() if limit else stmt.all()

        # Construire les filtres de recherche
        filters = [
            Customer.name.ilike(f"%{q}%"),
            Customer.email.ilike(f"%{q}%"),
            Customer.address.ilike(f"%{q}%"),
        ]

        # Ajouter filtre ID si la recherche est numérique
        try:
            filters.append(Customer.id == int(q))
        except ValueError:
            pass

        # Exécuter la recherche
        stmt = session.query(Customer).filter(or_(*filters)).order_by(func.lower(Customer.name))
        return stmt.limit(limit).all() if limit else stmt.all()
    finally:
        session.close()


def get_customer_by_id(customer_id: int):
    """Récupérer un client par son ID."""
    session = database.SessionLocal()
    try:
        return session.query(Customer).filter(Customer.id == customer_id).first()
    finally:
        session.close()


def update_customer(customer_id: int, name: str = None, address: str = None, email: str = None):
    """Mettre à jour les informations d'un client existant."""
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
    """Supprimer un client de la base de données."""
    session = database.SessionLocal()
    try:
        customer = session.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            session.delete(customer)
            session.commit()
        return customer
    finally:
        session.close()
