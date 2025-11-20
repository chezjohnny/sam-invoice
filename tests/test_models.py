import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sam_invoice.models.crud_customer as crud
import sam_invoice.models.database as database
from sam_invoice.models.customer import Base


@pytest.fixture
def in_memory_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    monkeypatch.setattr(database, "SessionLocal", Session)
    try:
        yield
    finally:
        # teardown: drop all tables and dispose engine
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_create_and_query_customer(in_memory_db):
    cust = crud.create_customer("Dupont", "1 rue du Vin", "dupont@example.com")
    assert cust.id is not None
    assert cust.name == "Dupont"
    customers = crud.get_customers()
    # ensure at least one customer with our email exists
    assert any(c.email == "dupont@example.com" for c in customers)
