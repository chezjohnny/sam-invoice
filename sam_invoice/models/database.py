"""SQLite database configuration for Sam Invoice."""

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import all models to register them with Base metadata
from . import customer, product  # noqa: F401
from .customer import Base

# Local SQLite database URL
DATABASE_URL = "sqlite:///sam_invoice.db"

# Create SQLAlchemy engine without displaying SQL queries
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory for CRUD operations
SessionLocal = sessionmaker(bind=engine)

# Reduce SQLAlchemy logs to WARNING level
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
