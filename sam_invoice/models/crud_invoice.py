"""CRUD operations for invoices."""

from sqlalchemy import desc

from . import database
from .base_crud import BaseCRUD
from .invoice import Invoice, InvoiceItem


class InvoiceCRUD(BaseCRUD[Invoice]):
    """CRUD operations for Invoice entities."""

    def __init__(self):
        super().__init__(Invoice)

    def create(
        self,
        reference: str,
        date,
        customer_name: str,
        items_data: list[dict],
        customer_address: str = "",
        customer_id: int = None,
        due_date=None,
        subtotal: float = 0.0,
        tax: float = 0.0,
        total: float = 0.0,
    ) -> Invoice:
        """Create a new invoice with items.

        Args:
            reference: Invoice reference
            date: Invoice date
            customer_name: Customer name snapshot
            items_data: List of dicts with item details (product_name, quantity, unit_price, total_price)
            customer_address: Customer address snapshot
            customer_id: Customer ID (optional)
            due_date: Due date
            subtotal: Subtotal (HT)
            tax: Tax (TVA)
            total: Total (TTC)
        """
        # TODO: compute totals
        with database.db_manager.get_session() as session:
            invoice = Invoice(
                reference=reference,
                date=date,
                due_date=due_date,
                customer_id=customer_id,
                customer_name=customer_name,
                customer_address=customer_address,
                subtotal=subtotal,
                tax=tax,
                total=total,
            )

            for item_data in items_data:
                item = InvoiceItem(
                    product_name=item_data["product_name"],
                    quantity=item_data["quantity"],
                    unit_price=item_data["unit_price"],
                    total_price=item_data["total_price"],
                    product_id=item_data.get("product_id"),  # Optional product reference
                )
                invoice.items.append(item)

            session.add(invoice)
            session.commit()
            session.refresh(invoice)
            return invoice

    def update(self, invoice_id: int, items_data: list[dict] = None, **kwargs) -> Invoice | None:
        """Update an existing invoice.

        Args:
            invoice_id: The invoice's ID
            items_data: Optional list of new items (replaces existing ones)
            **kwargs: Fields to update (reference, date, customer_name, etc.)

        Returns:
            The updated invoice if found, None otherwise
        """
        with database.db_manager.get_session() as session:
            invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            if invoice:
                # TODO: uniformize the approach
                # Update fields
                for key, value in kwargs.items():
                    if hasattr(invoice, key):
                        setattr(invoice, key, value)

                # Update items if provided
                if items_data is not None:
                    # Remove existing items
                    session.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).delete()

                    # Add new items
                    for item_data in items_data:
                        item = InvoiceItem(
                            invoice_id=invoice.id,
                            product_name=item_data["product_name"],
                            quantity=item_data["quantity"],
                            unit_price=item_data["unit_price"],
                            total_price=item_data["total_price"],
                            product_id=item_data.get("product_id"),
                        )
                        session.add(item)

                session.commit()
                session.refresh(invoice)
            return invoice

    def _get_search_filters(self, query: str) -> list:
        """Get search filters for invoices.

        Searches in: reference, customer_name
        """
        return [
            Invoice.reference.ilike(f"%{query}%"),
            Invoice.customer_name.ilike(f"%{query}%"),
        ]

    def _get_sort_field(self):
        """Sort invoices by date descending."""
        return desc(Invoice.date)

    def get_for_customer(self, customer_id: int) -> list[Invoice]:
        """Get invoices for a specific customer by ID.

        Args:
            customer_id: The customer's ID

        Returns:
            List of invoices for this customer, sorted by date (newest first)
        """
        if not customer_id:
            return []

        with database.db_manager.get_session() as session:
            invoices = (
                session.query(Invoice).filter(Invoice.customer_id == customer_id).order_by(desc(Invoice.date)).all()
            )
            return invoices


# Create singleton instance
invoice_crud = InvoiceCRUD()
