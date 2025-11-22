"""Modèle de données pour les clients."""

from sqlalchemy import CheckConstraint, Column, Integer, String
from sqlalchemy.orm import declarative_base

# Base déclarative pour tous les modèles SQLAlchemy
Base = declarative_base()


class Customer(Base):
    """Modèle de client avec nom, adresse et email.

    Contraintes:
    - Le nom doit avoir au moins 3 caractères
    - L'adresse doit avoir au moins 3 caractères
    """

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("length(name) >= 3", name="ck_customers_name_minlen"),
        CheckConstraint("length(address) >= 3", name="ck_customers_address_minlen"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    email = Column(String)
