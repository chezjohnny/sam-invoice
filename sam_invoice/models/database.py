"""Configuration de la base de données SQLite pour Sam Invoice."""

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .customer import Base

# URL de la base de données SQLite locale
DATABASE_URL = "sqlite:///sam_invoice.db"

# Créer le moteur SQLAlchemy sans afficher les requêtes SQL
engine = create_engine(DATABASE_URL, echo=False)

# Créer la fabrique de sessions pour les opérations CRUD
SessionLocal = sessionmaker(bind=engine)

# Réduire les logs SQLAlchemy au niveau WARNING
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def init_db():
    """Initialiser la base de données en créant toutes les tables."""
    Base.metadata.create_all(bind=engine)
