from datetime import date

from sam_invoice.models.crud_invoice import invoice_crud


def test_create_and_query_invoice(in_memory_db):
    """Create an invoice and verify it can be queried back."""
    items = [
        {"product_name": "Item 1", "quantity": 2, "unit_price": 10.0, "total_price": 20.0},
        {"product_name": "Item 2", "quantity": 1, "unit_price": 50.0, "total_price": 50.0},
    ]

    inv = invoice_crud.create(
        reference="INV-001",
        date=date(2023, 1, 1),
        customer_name="Test Client",
        customer_address="123 Test St",
        subtotal=70.0,
        tax=5.0,
        total=75.0,
        items_data=items,
    )

    assert inv.id is not None
    assert inv.reference == "INV-001"
    assert len(inv.items) == 2
    assert inv.items[0].product_name == "Item 1"

    # Query back
    fetched = invoice_crud.get_by_id(inv.id)
    assert fetched is not None
    assert fetched.customer_name == "Test Client"


def test_search_invoices(in_memory_db):
    """Verify search functionality."""
    invoice_crud.create(reference="INV-A", date=date.today(), customer_name="Alice", items_data=[])
    invoice_crud.create(reference="INV-B", date=date.today(), customer_name="Bob", items_data=[])

    results = invoice_crud.search("Alice")
    assert len(results) == 1
    assert results[0].reference == "INV-A"

    results = invoice_crud.search("INV")
    assert len(results) == 2


def test_update_invoice(in_memory_db):
    """Verify update functionality."""
    inv = invoice_crud.create(reference="INV-UPD", date=date.today(), customer_name="Original", items_data=[])

    updated = invoice_crud.update(inv.id, customer_name="Updated", total=100.0)
    assert updated.customer_name == "Updated"
    assert updated.total == 100.0

    # Verify persistence
    fetched = invoice_crud.get_by_id(inv.id)
    assert fetched.customer_name == "Updated"
