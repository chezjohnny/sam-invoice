"""Invoices view using the base class."""

from datetime import date

from PySide6.QtCore import Qt, Signal

from sam_invoice.models.crud_invoice import invoice_crud
from sam_invoice.ui.base_widgets import BaseListView
from sam_invoice.ui.invoice_detail import InvoiceDetailWidget


class InvoicesView(BaseListView):
    """Invoices view widget with two-column layout.

    Left column: search and invoice list
    Right column: invoice detail with PDF preview in tabs
    """

    invoice_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Hide "New" button - invoices are created from customer view
        self._add_btn.setVisible(False)

    def _search_placeholder(self) -> str:
        """Search placeholder text."""
        return "Search invoices (ref, client)..."

    def _search_function(self, query: str, limit: int):
        """Search function for invoices."""
        rows = invoice_crud.search(query, limit=limit)
        return sorted(rows, key=lambda i: i.date, reverse=True)

    def _create_detail_widget(self):
        """Create the invoice detail widget."""
        detail = InvoiceDetailWidget(self)
        return detail

    def _get_all_items(self):
        """Get all invoices (limited to 100 most recent for performance)."""
        try:
            items = invoice_crud.get_all()
            # Limit to 100 most recent for performance
            items_sorted = sorted(items, key=lambda i: i.date if i.date else date(1900, 1, 1), reverse=True)
            return items_sorted[:100]
        except Exception as e:
            print(f"Error loading invoices: {e}")
            import traceback

            traceback.print_exc()
            return []

    def _format_list_item(self, invoice) -> str:
        """Format an invoice for display in the list."""
        ref = getattr(invoice, "ref", "") or "(no ref)"
        client = getattr(invoice, "customer_name", "")
        date = getattr(invoice, "date", None)
        date_str = date.strftime("%d.%m.%Y") if date else ""

        if client and date_str:
            return f"{date_str} - {ref} - {client}"
        elif client:
            return f"{ref} - {client}"
        return ref

    def _on_saved(self, data: dict):
        """Callback when an invoice is saved."""
        # Invoices are read-only, no save action
        pass

    def _on_deleted(self, invoice_id: int):
        """Callback when an invoice is deleted."""
        # Invoices are read-only, no delete action
        pass

    def _on_item_activated(self, item):
        """Callback when an item is activated."""
        if not item:
            return
        selected_invoice = item.data(Qt.ItemDataRole.UserRole)
        self._detail_widget.set_invoice(selected_invoice)
        self.invoice_selected.emit(selected_invoice)

    def _on_add_item(self):
        """Callback to add a new item."""
        from sam_invoice.ui.invoice_edit_dialog import InvoiceEditDialog

        dialog = InvoiceEditDialog(self)
        dialog.invoice_saved.connect(lambda inv: self.reload_items())
        dialog.exec()
