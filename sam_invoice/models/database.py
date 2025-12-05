"""SQLite database configuration for Sam Invoice."""

import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import all models to register them with Base metadata
from . import company, customer, invoice, product  # noqa: F401
from .customer import Base

# Reduce SQLAlchemy logs to WARNING level
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


class DatabaseManager:
    """Manages SQLite database connections and session factory.

    Le chemin par défaut est `invoices.db` dans le répertoire courant si aucun
    chemin n'est fourni au constructeur.
    """

    def __init__(self, db_path: Path | str | None = None):
        self.engine = None
        self.SessionLocal = None
        if db_path is None:
            db_path = Path.cwd() / "invoices.db"
        self.set_database_path(db_path)

    def set_database_path(self, db_path: Path | str) -> None:
        """Set the database path and reinitialize the engine.

        Args:
            db_path: Path to the SQLite database file
        """
        if isinstance(db_path, str):
            db_path = Path(db_path)

        database_url = f"sqlite:///{db_path.absolute()}"
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def init_db(self) -> None:
        """Initialize the database by creating all tables."""
        if self.engine is None:
            # Réinitialise sur le chemin par défaut si jamais non initialisé
            self.set_database_path(Path.cwd() / "invoices.db")
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a new database session."""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        return self.SessionLocal()


# Singleton instance exposée
db_manager = DatabaseManager()

# NOTE: Les alias historiques `engine` et `SessionLocal` ont été supprimés.
# Utiliser uniquement l'instance `db_manager`.
