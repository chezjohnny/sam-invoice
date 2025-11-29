from datetime import date

from sam_invoice.models.crud_customer import customer_crud
from sam_invoice.models.crud_invoice import invoice_crud
from sam_invoice.models.crud_product import product_crud


def test_invoice_editing_workflow(in_memory_db):
    # 1. Setup data
    customer = customer_crud.create(name="Test Client", address="123 Test St", email="test@test.com")
    # Use a unique reference to avoid IntegrityError if DB is not cleared
    import random

    suffix = random.randint(1000, 9999)
    product = product_crud.create(reference=f"TEST-PROD-UNIQUE-{suffix}", name="Test Product", price=100.0)

    # 2. Create initial invoice
    items_data = [
        {
            "product_name": "Test Product",
            "quantity": 2,
            "unit_price": 100.0,
            "total_price": 200.0,
            "product_id": product.reference,
        },
        {
            "product_name": "Custom Item",
            "quantity": 1,
            "unit_price": 50.0,
            "total_price": 50.0,
            # No product_id
        },
    ]

    invoice = invoice_crud.create(
        reference="INV-TEST-001",
        date=date.today(),
        customer_name=customer.name,
        customer_address=customer.address,
        subtotal=250.0,
        tax=19.25,
        total=269.25,
        items_data=items_data,
    )

    assert invoice.id is not None
    assert len(invoice.items) == 2
    assert invoice.items[0].product_id == product.reference
    assert invoice.items[1].product_id is None

    # 3. Update invoice (Edit)
    # Change quantity of product item, remove custom item, add new custom item
    new_items_data = [
        {
            "product_name": "Test Product",
            "quantity": 3,  # Changed from 2 to 3
            "unit_price": 100.0,
            "total_price": 300.0,
            "product_id": product.reference,
        },
        {
            "product_name": "New Custom Item",
            "quantity": 5,
            "unit_price": 10.0,
            "total_price": 50.0,
            # No product_id
        },
    ]

    updated_invoice = invoice_crud.update(
        invoice_id=invoice.id, items_data=new_items_data, subtotal=350.0, tax=26.95, total=376.95
    )

    # 4. Verify updates
    assert updated_invoice.id == invoice.id
    assert len(updated_invoice.items) == 2

    # Check items (order might vary, so check by description)
    items_map = {item.product_name: item for item in updated_invoice.items}

    assert "Test Product" in items_map
    prod_item = items_map["Test Product"]
    assert prod_item.quantity == 3
    assert prod_item.total_price == 300.0
    assert prod_item.product_id == product.reference

    assert "New Custom Item" in items_map
    custom_item = items_map["New Custom Item"]
    assert custom_item.quantity == 5
    assert custom_item.total_price == 50.0
    assert custom_item.product_id is None

    assert "Custom Item" not in items_map  # Should be removed
