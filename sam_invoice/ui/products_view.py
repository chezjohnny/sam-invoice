"""Products view using the base class."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMessageBox

import sam_invoice.models.crud_product as crud
from sam_invoice.ui.base_widgets import BaseListView
from sam_invoice.ui.product_detail import ProductDetailWidget


class ProductsView(BaseListView):
    """Products view widget with two-column layout.

    Left column: search and product list
    Right column: product details with edit/save/delete actions
    """

    product_selected = Signal(object)

    def _search_placeholder(self) -> str:
        """Search placeholder text."""
        return "Search products (reference, name)..."

    def _search_function(self, query: str, limit: int):
        """Search function for products."""
        rows = crud.search_products(query, limit=limit)
        return sorted(rows, key=lambda a: (getattr(a, "reference", "") or "").lower())

    def _create_detail_widget(self):
        """Create product detail widget."""
        detail = ProductDetailWidget(self)
        detail.product_saved.connect(self._on_saved)
        detail.product_deleted.connect(self._on_deleted)
        return detail

    def _get_all_items(self):
        """Get all products."""
        return crud.get_products()

    def _format_list_item(self, product) -> str:
        """Format an product for display in the list."""
        reference = getattr(product, "reference", "") or "(no reference)"
        name = getattr(product, "name", "")
        if name:
            return f"{reference} - {name}"
        return reference

    def _on_saved(self, data: dict):
        """Callback when an product is saved."""
        art_id = data.get("id")
        try:
            if art_id:
                # Update
                crud.update_product(
                    art_id,
                    reference=data.get("reference"),
                    name=data.get("name"),
                    price=data.get("price"),
                    stock=data.get("stock"),
                    sold=data.get("sold"),
                )
            else:
                # Create
                crud.create_product(
                    reference=data.get("reference"),
                    name=data.get("name"),
                    price=data.get("price"),
                    stock=data.get("stock"),
                    sold=data.get("sold"),
                )
            self.reload_items()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save product: {e}")

    def _on_deleted(self, art_id: int):
        """Callback when an product is deleted."""
        try:
            crud.delete_product(art_id)
            self.reload_items()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete product: {e}")

    def _on_item_activated(self, item):
        """Callback when an item is activated."""
        if not item:
            return
        selected_product = item.data(Qt.ItemDataRole.UserRole)
        self._detail_widget.set_product(selected_product)
        self.product_selected.emit(selected_product)

    def _on_add_item(self):
        """Callback to add a new item."""
        # Clear selection
        self._results_list.clearSelection()
        self._detail_widget.set_product(None)
        # Enter edit mode
        self._detail_widget._enter_edit_mode(True)
