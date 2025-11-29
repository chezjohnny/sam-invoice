"""Invoice edit dialog for creating and editing invoices."""

from datetime import date, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QVBoxLayout,
)

from sam_invoice.models.crud_customer import customer_crud
from sam_invoice.models.crud_invoice import invoice_crud
from sam_invoice.models.crud_product import product_crud


class InvoiceEditDialog(QDialog):
    """Dialog for creating/editing invoices."""

    invoice_saved = Signal(object)

    def __init__(self, parent=None, invoice=None, customer=None):
        super().__init__(parent)
        self.invoice = invoice
        self.is_new = invoice is None
        self.pre_selected_customer = customer  # Customer to pre-select

        self.setWindowTitle("New Invoice" if self.is_new else f"Edit Invoice {invoice.reference}")
        self.setMinimumSize(700, 500)

        self._init_ui()
        self._load_customers()

        # Pre-select customer if provided
        if customer and self.is_new:
            self._select_customer_in_combo(customer)

        if not self.is_new:
            self._load_invoice_data()

    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Form for invoice header
        form = QFormLayout()

        # Reference (read-only, auto-generated for new)
        self.reference_edit = QLineEdit()
        self.reference_edit.setReadOnly(True)
        if self.is_new:
            self.reference_edit.setText(self._generate_next_reference())
        form.addRow("Reference:", self.reference_edit)

        # Client info (read-only when pre-selected)
        self.client_combo = QComboBox()
        self._load_customers()
        self.client_combo.currentIndexChanged.connect(self._on_client_changed)
        form.addRow("Client:", self.client_combo)

        # Customer name and address as labels (read-only display)
        self.customer_name_label = QLabel("")
        self.customer_name_label.setStyleSheet("padding: 5px; background: #f0f0f0; border-radius: 3px;")
        form.addRow("Customer Name:", self.customer_name_label)

        self.customer_address_label = QLabel("")
        self.customer_address_label.setStyleSheet("padding: 5px; background: #f0f0f0; border-radius: 3px;")
        self.customer_address_label.setWordWrap(True)
        form.addRow("Customer Address:", self.customer_address_label)

        # Dates
        self.date_edit = QDateEdit()
        self.date_edit.setDate(date.today())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Invoice Date:", self.date_edit)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(date.today() + timedelta(days=30))
        self.due_date_edit.setCalendarPopup(True)
        form.addRow("Due Date:", self.due_date_edit)

        layout.addLayout(form)

        # Items section
        items_label = QLabel("<b>Items</b>")
        layout.addWidget(items_label)

        self.items_table = QTableWidget(0, 5)
        self.items_table.setHorizontalHeaderLabels(["Description", "Qty", "Unit Price", "Total", ""])
        self.items_table.setColumnWidth(0, 250)
        self.items_table.setColumnWidth(1, 80)
        self.items_table.setColumnWidth(2, 100)
        self.items_table.setColumnWidth(3, 100)
        self.items_table.setColumnWidth(4, 60)
        layout.addWidget(self.items_table)

        # Add item button
        add_item_btn = QPushButton("+ Add Item")
        add_item_btn.clicked.connect(self._add_item_row)
        layout.addWidget(add_item_btn)

        # Totals area
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()

        totals_form = QFormLayout()
        self.subtotal_label = QLabel("0.00")
        self.tax_label = QLabel("0.00")
        self.total_label = QLabel("0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 12pt;")

        totals_form.addRow("Total HT:", self.subtotal_label)
        totals_form.addRow("TVA (7.7%):", self.tax_label)
        totals_form.addRow("Total TTC:", self.total_label)

        totals_layout.addLayout(totals_form)
        layout.addLayout(totals_layout)

        # Dialog buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        save_btn.setDefault(True)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        # Add initial empty row
        self._add_item_row()

    def _load_customers(self):
        """Load customers into dropdown."""
        try:
            customers = customer_crud.get_all()
            self.client_combo.addItem("-- Select Client --", None)
            for customer in customers:
                self.client_combo.addItem(customer.name, customer)
        except Exception as e:
            print(f"Error loading customers: {e}")

    def _on_client_changed(self, index):
        """Auto-fill client info when client is selected."""
        customer = self.client_combo.currentData()
        if customer:
            self.customer_name_label.setText(customer.name or "")
            self.customer_address_label.setText(customer.address or "")
        else:
            self.customer_name_label.clear()
            self.customer_address_label.clear()

    def _select_customer_in_combo(self, customer):
        """Select a specific customer in the combo box."""
        if not customer:
            return

        customer_id = getattr(customer, "id", None)
        for i in range(self.client_combo.count()):
            item = self.client_combo.itemData(i)
            if item and getattr(item, "id", None) == customer_id:
                self.client_combo.setCurrentIndex(i)
                self.client_combo.setEnabled(False)  # Lock selection
                break

    def _generate_next_reference(self):
        """Generate next invoice reference."""
        try:
            invoices = invoice_crud.get_all()
            year = date.today().year

            # Find max number for current year
            max_num = 0
            prefix = f"INV-{year}-"
            for inv in invoices:
                if inv.reference and inv.reference.startswith(prefix):
                    try:
                        num = int(inv.reference.replace(prefix, ""))
                        max_num = max(max_num, num)
                    except ValueError:
                        pass

            return f"{prefix}{max_num + 1:03d}"
        except Exception:
            return f"INV-{date.today().year}-001"

    def _add_item_row(self):
        """Add a new item row to the table."""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        # Description with autocomplete
        desc_edit = QLineEdit()

        # Setup autocomplete (use cached products)
        try:
            if not hasattr(self, "_products_by_name"):
                # Load products once if not already loaded
                products = product_crud.get_all()
                self._products_by_name = {p.name: p for p in products if p.name}

            if self._products_by_name:
                completer = QCompleter(list(self._products_by_name.keys()))
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)  # Better matching
                desc_edit.setCompleter(completer)

                # Auto-fill price when product selected
                desc_edit.textChanged.connect(lambda text, r=row: self._on_product_selected(r, text))
        except Exception as e:
            print(f"Error setup autocomplete: {e}")

        self.items_table.setCellWidget(row, 0, desc_edit)

        # Quantity
        qty_spin = QSpinBox()
        qty_spin.setMinimum(1)
        qty_spin.setValue(1)
        qty_spin.valueChanged.connect(self._update_totals)
        self.items_table.setCellWidget(row, 1, qty_spin)

        # Unit price
        price_spin = QDoubleSpinBox()
        price_spin.setDecimals(2)
        price_spin.setMaximum(999999.99)
        price_spin.setSuffix(" CHF")
        price_spin.valueChanged.connect(self._update_totals)
        self.items_table.setCellWidget(row, 2, price_spin)

        # Total (read-only label)
        total_label = QLabel("0.00 CHF")
        total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.items_table.setCellWidget(row, 3, total_label)

        # Delete button
        del_btn = QPushButton("×")
        del_btn.setMaximumWidth(40)
        del_btn.clicked.connect(lambda: self._remove_item_row(row))
        self.items_table.setCellWidget(row, 4, del_btn)

        self._update_totals()

    def _on_product_selected(self, row, product_name):
        """Auto-fill price when a product is selected from autocomplete."""
        if not hasattr(self, "_products_by_name"):
            return

        product = self._products_by_name.get(product_name)
        desc_widget = self.items_table.cellWidget(row, 0)

        if product:
            # Store product_id in widget for later retrieval
            desc_widget.setProperty("product_id", product.reference)

            # Auto-fill price if not manually edited
            if product.price:
                price_widget = self.items_table.cellWidget(row, 2)
                if price_widget and price_widget.value() == 0:
                    price_widget.setValue(product.price)
        else:
            # Clear product_id if text doesn't match
            desc_widget.setProperty("product_id", None)

    def _remove_item_row(self, row):
        """Remove an item row."""
        if self.items_table.rowCount() > 1:  # Keep at least one row
            self.items_table.removeRow(row)
            self._update_totals()

    def _update_totals(self):
        """Calculate and update totals."""
        subtotal = 0.0

        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 1)
            price_widget = self.items_table.cellWidget(row, 2)
            total_widget = self.items_table.cellWidget(row, 3)

            if qty_widget and price_widget and total_widget:
                qty = qty_widget.value()
                price = price_widget.value()
                item_total = qty * price
                subtotal += item_total
                total_widget.setText(f"{item_total:.2f} CHF")

        tva = subtotal * 0.077  # 7.7% TVA
        total = subtotal + tva

        self.subtotal_label.setText(f"{subtotal:.2f} CHF")
        self.tax_label.setText(f"{tva:.2f} CHF")
        self.total_label.setText(f"{total:.2f} CHF")

    def _load_invoice_data(self):
        """Load invoice data for editing."""
        if not self.invoice:
            return

        self.reference_edit.setText(self.invoice.reference)
        self.date_edit.setDate(self.invoice.date)
        if self.invoice.due_date:
            self.due_date_edit.setDate(self.invoice.due_date)

        # Find and select client
        for i in range(self.client_combo.count()):
            customer = self.client_combo.itemData(i)
            if customer and customer.name == self.invoice.customer_name:
                self.client_combo.setCurrentIndex(i)
                break

        self.customer_name_label.setText(self.invoice.customer_name or "")
        self.customer_address_label.setText(self.invoice.customer_address or "")

        # Clear items table
        self.items_table.setRowCount(0)

        # Load items
        for item in self.invoice.items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)

            # Description
            desc_edit = QLineEdit(item.product_name)
            # Setup autocomplete
            try:
                if hasattr(self, "_products_by_name"):
                    completer = QCompleter(list(self._products_by_name.keys()))
                    completer.setCaseSensitivity(Qt.CaseInsensitive)
                    desc_edit.setCompleter(completer)
                    desc_edit.textChanged.connect(lambda text, r=row: self._on_product_selected(r, text))
            except Exception:
                pass

            # Store product_id if present
            if item.product_id:
                desc_edit.setProperty("product_id", item.product_id)

            self.items_table.setCellWidget(row, 0, desc_edit)

            # Quantity
            qty_spin = QSpinBox()
            qty_spin.setMinimum(1)
            qty_spin.setValue(item.quantity)
            qty_spin.valueChanged.connect(self._update_totals)
            self.items_table.setCellWidget(row, 1, qty_spin)

            # Unit price
            price_spin = QDoubleSpinBox()
            price_spin.setDecimals(2)
            price_spin.setMaximum(999999.99)
            price_spin.setSuffix(" CHF")
            price_spin.setValue(item.unit_price)
            price_spin.valueChanged.connect(self._update_totals)
            self.items_table.setCellWidget(row, 2, price_spin)

            # Total (read-only label)
            total_label = QLabel(f"{item.total_price:.2f} CHF")
            total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setCellWidget(row, 3, total_label)

            # Delete button
            del_btn = QPushButton("×")
            del_btn.setMaximumWidth(40)
            del_btn.clicked.connect(lambda checked=False, r=row: self._remove_item_row(r))
            self.items_table.setCellWidget(row, 4, del_btn)

        self._update_totals()

    def _save(self):
        """Save the invoice."""
        # Validation
        if self.client_combo.currentIndex() == 0:
            QMessageBox.warning(self, "Validation Error", "Please select a client.")
            return

        # Collect items
        items_data = []
        for row in range(self.items_table.rowCount()):
            desc_widget = self.items_table.cellWidget(row, 0)
            qty_widget = self.items_table.cellWidget(row, 1)
            price_widget = self.items_table.cellWidget(row, 2)

            if desc_widget and qty_widget and price_widget:
                desc = desc_widget.text().strip()
                if not desc:
                    continue

                qty = qty_widget.value()
                unit_price = price_widget.value()
                total_price = qty * unit_price
                product_id = desc_widget.property("product_id")  # Get stored product_id

                items_data.append(
                    {
                        "product_name": desc,
                        "quantity": qty,
                        "unit_price": unit_price,
                        "total_price": total_price,
                        "product_id": product_id,  # Include product reference
                    }
                )

        if not items_data:
            QMessageBox.warning(self, "Validation Error", "Please add at least one item.")
            return

        # Calculate totals
        subtotal = sum(item["total_price"] for item in items_data)
        tax = subtotal * 0.077
        total = subtotal + tax

        try:
            if self.is_new:
                # Create new invoice
                customer = self.client_combo.currentData()
                invoice = invoice_crud.create(
                    reference=self.reference_edit.text(),
                    date=self.date_edit.date().toPython(),
                    due_date=self.due_date_edit.date().toPython(),
                    customer_name=customer.name,
                    customer_address=self.customer_address_label.text(),
                    subtotal=subtotal,
                    tax=tax,
                    total=total,
                    items_data=items_data,
                )
                self.invoice_saved.emit(invoice)
                self.accept()
            else:
                # Update existing invoice
                invoice = invoice_crud.update(
                    invoice_id=self.invoice.id,
                    reference=self.reference_edit.text(),
                    date=self.date_edit.date().toPython(),
                    due_date=self.due_date_edit.date().toPython(),
                    customer_name=self.invoice.customer_name,  # Client name doesn't change on edit usually
                    customer_address=self.customer_address_label.text(),
                    subtotal=subtotal,
                    tax=tax,
                    total=total,
                    items_data=items_data,
                )
                self.invoice_saved.emit(invoice)
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save invoice: {e}")
