import tempfile
from datetime import date
from pathlib import Path

from sam_invoice.models.crud_invoice import invoice_crud
from sam_invoice.tools.pdf_generator import InvoicePDFGenerator


def test_pdf_generation(in_memory_db):
    """Verify PDF generation creates a non-empty file."""
    # Create a dummy invoice
    items = [
        {"product_name": "Wine Bottle", "quantity": 6, "unit_price": 15.0, "total_price": 90.0},
    ]
    inv = invoice_crud.create(
        reference="PDF-TEST",
        date=date.today(),
        customer_name="PDF Client",
        customer_address="PDF Address",
        subtotal=90.0,
        tax=7.0,
        total=97.0,
        items_data=items,
    )

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        generator = InvoicePDFGenerator(tmp_path)
        generator.generate(inv)

        assert tmp_path.exists()
        assert tmp_path.stat().st_size > 0

        # Check header signature (PDF files start with %PDF)
        with open(tmp_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF"

    finally:
        if tmp_path.exists():
            tmp_path.unlink()
