"""Modèle de données pour les articles."""

from sqlalchemy import Column, Float, Integer, String

from .customer import Base


class Article(Base):
    """Modèle d'article avec référence, description, prix, stock et quantité vendue."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    ref = Column(String, nullable=False)  # Référence unique de l'article
    desc = Column(String)  # Description de l'article
    prix = Column(Float)  # Prix unitaire
    stock = Column(Integer)  # Quantité en stock
    vendu = Column(Integer)  # Quantité vendue
