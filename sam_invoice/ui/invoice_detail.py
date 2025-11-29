"""Invoice detail widget with tabbed interface."""

import tempfile
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

from sam_invoice.tools.pdf_generator import InvoicePDFGenerator


class InvoiceDetailWidget(QWidget):
    """Widget displaying invoice details with PDF preview in tabs."""

    # Signals expected by BaseListView (must be class attributes)
    item_saved = Signal(dict)
    item_deleted = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_invoice = None

        # Required attributes for BaseListView compatibility
        from sam_invoice.ui.widget_helpers import create_icon_button

        self._delete_btn = create_icon_button("fa5s.trash", "Delete")
        self._delete_btn.setEnabled(False)  # Invoices are read-only
        self._delete_btn.setVisible(False)  # Hide since not used

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Details
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)

        self._info_label = QLabel("Select an invoice to view details")
        self._info_label.setStyleSheet("padding: 20px; font-size: 11pt;")
        self._info_label.setWordWrap(True)
        details_layout.addWidget(self._info_label)
        details_layout.addStretch()

        self.tabs.addTab(details_tab, "Details")

        # Tab 2: PDF Preview
        pdf_tab = QWidget()
        pdf_layout = QVBoxLayout(pdf_tab)
        pdf_layout.setContentsMargins(0, 0, 0, 0)

        self.pdf_view = QPdfView()
        self.pdf_document = QPdfDocument(self)
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
        pdf_layout.addWidget(self.pdf_view)

        self.tabs.addTab(pdf_tab, "PDF Preview")

    def set_invoice(self, invoice):
        """Set the invoice to display."""
        self._current_invoice = invoice

        if not invoice:
            self._info_label.setText("Select an invoice to view details")
            self.pdf_document.close()
            self.tabs.setCurrentIndex(0)  # Return to Details tab
            return

        # Update details tab
        info_text = f"<h2>Invoice {invoice.reference}</h2>"
        info_text += f"<p><b>Date:</b> {invoice.date.strftime('%d.%m.%Y')}</p>"
        if invoice.due_date:
            info_text += f"<p><b>Due Date:</b> {invoice.due_date.strftime('%d.%m.%Y')}</p>"
        info_text += f"<p><b>Client:</b> {invoice.customer_name}</p>"
        if invoice.customer_address:
            info_text += f"<p><b>Address:</b><br>{invoice.customer_address.replace(chr(10), '<br>')}</p>"

        info_text += "<hr>"
        info_text += f"<p><b>Total HT:</b> {invoice.subtotal:.2f} CHF</p>"
        info_text += f"<p><b>TVA:</b> {invoice.tax:.2f} CHF</p>"
        info_text += f"""
<p>
    <b>Total TTC:</b>
    <span style='font-size:14pt;font-weight:bold;color:#2c3e50;'>{invoice.total:.2f} CHF</span>
</p>"""

        # Add items
        if invoice.items:
            info_text += "<hr><h3>Items</h3><ul>"
            for item in invoice.items:
                info_text += (
                    f"<li><b>{item.product_name}</b> - Qty: {item.quantity} × "
                    f"{item.unit_price:.2f} = {item.total_price:.2f} CHF</li>"
                )
            info_text += "</ul>"

        self._info_label.setText(info_text)

        # Generate and display PDF
        self._generate_pdf()

    def _generate_pdf(self):
        """Generate PDF for current invoice."""
        if not self._current_invoice:
            return

        # Generate PDF to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            generator = InvoicePDFGenerator(tmp_path)
            generator.generate(self._current_invoice)

            # Load into view
            self.pdf_document.load(str(tmp_path))
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
        except Exception as e:
            self._info_label.setText(f"<p style='color:red;'>Error generating PDF: {e}</p>")
            print(f"Error generating preview: {e}")
