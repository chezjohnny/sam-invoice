"""Customer detail widget using the base class."""

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from sam_invoice.ui.base_widgets import BaseDetailWidget


class CustomerDetailWidget(BaseDetailWidget):
    """Customer detail widget with view/edit.

    Displays customer information (name, address, email) with
    ability to edit, save and delete.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Define signal aliases
        self.customer_saved = self.item_saved
        self.customer_deleted = self.item_deleted

        # Add customer-specific fields
        self._add_field("name", "", "e.g. John Doe", is_primary=True)
        self._add_field("address", "", "e.g. 1 Wine St, Apt 2", word_wrap=True)
        self._add_field("email", "", "e.g. john@example.com")

        # Finalize base layout first
        self._finalize_layout()

        # Add last order and invoice sections AFTER finalize (full width in main layout)
        import qtawesome as qta
        from PySide6.QtCore import QSize
        from PySide6.QtWidgets import (
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QPushButton,
            QVBoxLayout,
        )

        # === Last Order Section ===
        last_order_group = QGroupBox("Last Order Items")
        last_order_layout = QVBoxLayout()
        self._last_order_label = QLabel("No orders yet")
        self._last_order_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        self._last_order_label.setWordWrap(True)
        last_order_layout.addWidget(self._last_order_label)
        last_order_group.setLayout(last_order_layout)
        self.layout().addWidget(last_order_group)

        # === Invoice History Section ===
        history_layout = QVBoxLayout()

        # Header with Create Invoice button
        header_layout = QHBoxLayout()
        history_label = QLabel("<b>Invoice History</b>")
        header_layout.addWidget(history_label)
        header_layout.addStretch()

        # Create Invoice button (icon only)
        self._invoice_btn = QPushButton()
        self._invoice_btn.setIcon(qta.icon("fa5s.plus", color="#2196F3"))
        self._invoice_btn.setIconSize(QSize(20, 20))
        self._invoice_btn.setToolTip("Create Invoice")
        self._invoice_btn.setEnabled(False)
        self._invoice_btn.clicked.connect(self._on_create_invoice)
        self._invoice_btn.setFixedSize(36, 36)
        header_layout.addWidget(self._invoice_btn)

        history_layout.addLayout(header_layout)

        # Invoice list
        self._invoices_list = QListWidget()
        self._invoices_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background: #f5f5f5;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
                color: black;
            }
        """)
        history_layout.addWidget(self._invoices_list)  # Add the list widget to the history layout

        # Add to main layout for full width
        self.layout().addLayout(history_layout)

        # Connect list signals
        self._invoices_list.itemSelectionChanged.connect(self._on_invoice_selection_changed)
        self._invoices_list.itemDoubleClicked.connect(self._on_invoice_double_click)

        # Load icon
        self._load_avatar_icon("customers")

    def _save_changes(self):
        """Save customer changes."""
        data = {
            "id": self._current_id,
            "name": self._fields["name"][1].text().strip(),
            "address": self._fields["address"][1].text().strip(),
            "email": self._fields["email"][1].text().strip(),
        }
        self.customer_saved.emit(data)
        self._enter_edit_mode(False)

    def _on_delete_clicked(self):
        """Request confirmation and delete the customer."""
        if self._current_id is None:
            return

        name = self._fields["name"][0].text() or ""
        res = QMessageBox.question(
            self,
            "Delete",
            f"Delete customer '{name}'? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if res == QMessageBox.StandardButton.Yes:
            self.customer_deleted.emit(int(self._current_id))

    def _validate_fields(self) -> bool:
        """Validate form fields."""
        name = self._fields["name"][1].text().strip()
        address = self._fields["address"][1].text().strip()
        email = self._fields["email"][1].text().strip()

        valid = True

        # Name validation
        name_label, name_edit, name_err = self._fields["name"]
        if not name:
            name_err.setText("Name is required")
            name_err.setVisible(True)
            valid = False
        else:
            name_err.setVisible(False)

        # Address validation
        addr_label, addr_edit, addr_err = self._fields["address"]
        if not address:
            addr_err.setText("Address is required")
            addr_err.setVisible(True)
            valid = False
        else:
            addr_err.setVisible(False)

        # Email validation (if provided)
        email_label, email_edit, email_err = self._fields["email"]
        if email and "@" not in email:
            email_err.setText("Invalid email")
            email_err.setVisible(True)
            valid = False
        else:
            email_err.setVisible(False)

        self._save_btn.setEnabled(valid)
        return valid

    def set_customer(self, cust):
        """Display customer information."""
        self._current_id = getattr(cust, "id", None) if cust else None
        self._current_customer = cust  # Store for invoice creation

        if not cust:
            # Clear display
            self._fields["name"][0].setText("")
            self._fields["address"][0].setText("")
            self._fields["email"][0].setText("")
            self._edit_btn.setEnabled(False)
            self._edit_btn.setVisible(False)
            self._delete_btn.setEnabled(False)
            self._invoice_btn.setEnabled(False)
            self._invoices_list.clear()
            self._last_order_label.setText("No orders yet")
            self._view_invoice_btn.setEnabled(False)
            self._edit_invoice_btn.setEnabled(False)
        else:
            # Display customer data
            self._fields["name"][0].setText(getattr(cust, "name", ""))
            self._fields["address"][0].setText(getattr(cust, "address", ""))
            self._fields["email"][0].setText(getattr(cust, "email", ""))
            self._edit_btn.setEnabled(True)
            self._edit_btn.setVisible(True)
            self._delete_btn.setEnabled(self._current_id is not None)
            self._invoice_btn.setEnabled(self._current_id is not None)

            # Load invoice history and last order
            self._load_invoices_for_customer(cust.id)
            self._load_last_order_items(cust.id)

    def _load_invoices_for_customer(self, customer_id):
        """Load and display invoices for this customer."""
        import qtawesome as qta
        from PySide6.QtCore import QSize, Qt
        from PySide6.QtWidgets import (
            QHBoxLayout,
            QLabel,
            QListWidgetItem,
            QPushButton,
            QWidget,
        )

        from sam_invoice.models.crud_invoice import invoice_crud

        try:
            # Search invoices by customer ID
            invoices = invoice_crud.get_for_customer(customer_id)

            # Sort by date descending (newest first)
            invoices = sorted(invoices, key=lambda x: x.date if x.date else date.min, reverse=True)

            self._invoices_list.clear()
            for inv in invoices:
                # Create list item
                item = QListWidgetItem()

                # Create widget for the item
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(4, 4, 4, 4)

                # Invoice info
                date_str = inv.date.strftime("%d.%m.%Y") if inv.date else ""
                info_label = QLabel(f"<b>{inv.reference}</b><br>{date_str} - {inv.total:.2f} CHF")
                info_label.setStyleSheet("border: none;")
                item_layout.addWidget(info_label)
                item_layout.addStretch()

                # Edit button
                edit_btn = QPushButton()
                edit_btn.setIcon(qta.icon("fa5s.edit", color="#FFC107"))
                edit_btn.setIconSize(QSize(16, 16))
                edit_btn.setToolTip("Edit")
                edit_btn.setFixedSize(28, 28)
                edit_btn.clicked.connect(lambda checked, i=inv: self._on_edit_invoice_from_list(i))
                item_layout.addWidget(edit_btn)

                # PDF button
                pdf_btn = QPushButton()
                pdf_btn.setIcon(qta.icon("fa5s.file-pdf", color="#F44336"))
                pdf_btn.setIconSize(QSize(16, 16))
                pdf_btn.setToolTip("View PDF")
                pdf_btn.setFixedSize(28, 28)
                pdf_btn.clicked.connect(lambda checked, i=inv: self._on_view_invoice_from_list(i))
                item_layout.addWidget(pdf_btn)

                # Store invoice in item
                item.setData(Qt.UserRole, inv)
                item.setSizeHint(item_widget.sizeHint())

                self._invoices_list.addItem(item)
                self._invoices_list.setItemWidget(item, item_widget)

            # Enable list if invoices exist
            has_invoices = self._invoices_list.count() > 0
            self._invoices_list.setEnabled(has_invoices)
        except Exception as e:
            print(f"Error loading invoices: {e}")

    def _load_last_order_items(self, customer_id):
        """Load and display items from the last order."""
        from sam_invoice.models.crud_invoice import invoice_crud

        try:
            # Get all invoices for this customer
            invoices = invoice_crud.get_for_customer(customer_id)

            if not invoices:
                self._last_order_label.setText("No orders yet")
                return

            # Sort by date descending
            invoices = sorted(invoices, key=lambda x: x.date if x.date else date.min, reverse=True)
            last_invoice = invoices[0]

            # Format items display
            if not last_invoice.items:
                text = f"Last order ({last_invoice.date.strftime('%d.%m.%Y')}): No items"
            else:
                items_text = []
                for item in last_invoice.items:
                    # Assuming item has product_name and quantity
                    name = getattr(item, "product_name", "Unknown Product")
                    qty = getattr(item, "quantity", 0)
                    items_text.append(f"• {name} (Qty: {qty})")

                date_str = last_invoice.date.strftime("%d.%m.%Y") if last_invoice.date else "Unknown Date"
                text = f"<b>Last Order ({date_str}):</b><br>" + "<br>".join(items_text)

            self._last_order_label.setText(text)

        except Exception as e:
            print(f"Error loading last order: {e}")
            self._last_order_label.setText("Error loading last order")

    def _on_invoice_selection_changed(self):
        """Enable/disable invoice buttons based on selection."""
        has_selection = self._invoices_list.currentRow() >= 0
        self._view_invoice_btn.setEnabled(has_selection)
        self._edit_invoice_btn.setEnabled(has_selection)

    def _on_invoice_double_click(self, item):
        """Handle invoice double-click to edit."""
        invoice = item.data(Qt.UserRole)
        if invoice:
            self._on_edit_invoice_from_list(invoice)

    def _on_edit_invoice_from_list(self, invoice):
        """Edit a specific invoice from the list."""
        from sam_invoice.ui.invoice_edit_dialog import InvoiceEditDialog

        dialog = InvoiceEditDialog(self, invoice=invoice)
        if dialog.exec():
            # Reload invoices after editing
            self._load_invoices_for_customer(self._current_customer.name)
            self._load_last_order_items(self._current_customer.name)

    def _on_view_invoice_from_list(self, invoice):
        """View a specific invoice from the list."""
        if invoice:
            from PySide6.QtWidgets import QDialog, QVBoxLayout

            from sam_invoice.ui.invoice_detail import InvoiceDetailWidget

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Invoice {invoice.reference}")
            dialog.setMinimumSize(800, 600)

            layout = QVBoxLayout(dialog)
            detail_widget = InvoiceDetailWidget()
            detail_widget.set_invoice(invoice)
            layout.addWidget(detail_widget)

            dialog.exec()

    def _on_view_invoice(self):
        """View selected invoice in detail dialog."""
        item = self._invoices_list.currentItem()
        if not item:
            return

        invoice = item.data(Qt.UserRole)
        self._on_view_invoice_from_list(invoice)

    def _on_edit_invoice(self):
        """Edit selected invoice."""
        item = self._invoices_list.currentItem()
        if not item:
            return

        invoice = item.data(Qt.UserRole)
        self._on_edit_invoice_from_list(invoice)

    def _on_create_invoice(self):
        """Create a new invoice for this customer."""
        from sam_invoice.ui.invoice_edit_dialog import InvoiceEditDialog

        # Pre-select current customer
        dialog = InvoiceEditDialog(self)
        dialog._select_customer_in_combo(self._current_customer)

        if dialog.exec():
            # Reload invoices after creation
            self._load_invoices_for_customer(self._current_customer.name)
            self._load_last_order_items(self._current_customer.name)
            return
