from datetime import date

from sam_invoice.models.crud_customer import customer_crud
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


def test_get_invoices_for_customer(in_memory_db):
    """Verify get_for_customer returns invoices filtered by customer ID."""
    # Create customers
    cust1 = customer_crud.create(name="Alice Martin", address="123 Main St", email="alice@example.com")
    cust2 = customer_crud.create(name="Bob Smith", address="456 Oak Ave", email="bob@example.com")

    # Create invoices for customer 1
    _ = invoice_crud.create(
        reference="INV-001",
        date=date(2024, 1, 10),
        customer_id=cust1.id,
        customer_name="Alice Martin",
        items_data=[],
    )
    _ = invoice_crud.create(
        reference="INV-002",
        date=date(2024, 1, 20),
        customer_id=cust1.id,
        customer_name="Alice Martin",
        items_data=[],
    )

    # Create invoice for customer 2
    _ = invoice_crud.create(
        reference="INV-003",
        date=date(2024, 2, 15),
        customer_id=cust2.id,
        customer_name="Bob Smith",
        items_data=[],
    )

    # Test getting invoices for customer 1
    invoices_cust1 = invoice_crud.get_for_customer(cust1.id)
    assert len(invoices_cust1) == 2
    assert all(inv.customer_id == cust1.id for inv in invoices_cust1)
    assert invoices_cust1[0].reference == "INV-002"  # Sorted by date descending
    assert invoices_cust1[1].reference == "INV-001"

    # Test getting invoices for customer 2
    invoices_cust2 = invoice_crud.get_for_customer(cust2.id)
    assert len(invoices_cust2) == 1
    assert invoices_cust2[0].reference == "INV-003"

    # Test with non-existent customer ID
    invoices_empty = invoice_crud.get_for_customer(999)
    assert len(invoices_empty) == 0

    # Test with None
    invoices_none = invoice_crud.get_for_customer(None)
    assert len(invoices_none) == 0
