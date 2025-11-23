"""Customer detail widget using the base class."""

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

        # Finalize layout
        self._finalize_layout()

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

        if not cust:
            # Clear display
            self._fields["name"][0].setText("")
            self._fields["address"][0].setText("")
            self._fields["email"][0].setText("")
            self._edit_btn.setEnabled(False)
            self._edit_btn.setVisible(False)
            self._delete_btn.setEnabled(False)
        else:
            # Display customer data
            self._fields["name"][0].setText(getattr(cust, "name", ""))
            self._fields["address"][0].setText(getattr(cust, "address", ""))
            self._fields["email"][0].setText(getattr(cust, "email", ""))
            self._edit_btn.setEnabled(True)
            self._edit_btn.setVisible(True)
            self._delete_btn.setEnabled(self._current_id is not None)
