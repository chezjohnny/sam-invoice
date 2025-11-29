"""PDF Generator for Invoices using ReportLab."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from sam_invoice.models.crud_company import get_company
from sam_invoice.models.invoice import Invoice


class InvoicePDFGenerator:
    """Generates PDF invoices."""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Define custom styles for the invoice."""
        self.styles.add(
            ParagraphStyle(
                name="CompanyName",
                parent=self.styles["Heading1"],
                fontSize=16,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=2,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CompanyInfo",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#7f8c8d"),
                leading=11,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="InvoiceTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#2c3e50"),
                alignment=TA_RIGHT,
                spaceAfter=20,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ClientName",
                parent=self.styles["Heading2"],
                fontSize=12,
                textColor=colors.black,
                spaceAfter=2,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ClientAddress",
                parent=self.styles["Normal"],
                fontSize=10,
                leading=12,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="TableHeader",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.white,
                alignment=TA_CENTER,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="TableItem",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.black,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="TableNumber",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.black,
                alignment=TA_RIGHT,
            )
        )

    def generate(self, invoice: Invoice):
        """Generate the PDF for the given invoice."""
        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story = []
        company = get_company()

        # --- Header Section ---
        # Left: Company Info
        company_data = []
        if company:
            company_data.append(Paragraph(company.name, self.styles["CompanyName"]))
            if company.address:
                for line in company.address.split("\n"):
                    company_data.append(Paragraph(line, self.styles["CompanyInfo"]))
            if company.email:
                company_data.append(Paragraph(f"Email: {company.email}", self.styles["CompanyInfo"]))
            if company.phone:
                company_data.append(Paragraph(f"Tel: {company.phone}", self.styles["CompanyInfo"]))
        else:
            company_data.append(Paragraph("My Company", self.styles["CompanyName"]))

        # Right: Invoice Title & Details
        invoice_details = [
            Paragraph("INVOICE", self.styles["InvoiceTitle"]),
            Paragraph(f"<b>Ref:</b> {invoice.reference}", self.styles["Normal"]),
            Paragraph(f"<b>Date:</b> {invoice.date.strftime('%d.%m.%Y')}", self.styles["Normal"]),
        ]
        if invoice.due_date:
            invoice_details.append(
                Paragraph(f"<b>Due Date:</b> {invoice.due_date.strftime('%d.%m.%Y')}", self.styles["Normal"])
            )

        # Header Table (2 columns)
        header_table = Table([[company_data, invoice_details]], colWidths=[10 * cm, 7 * cm])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 1.5 * cm))

        # --- Client Section ---
        story.append(Paragraph("Bill To:", self.styles["CompanyInfo"]))
        story.append(Paragraph(invoice.customer_name, self.styles["ClientName"]))
        if invoice.customer_address:
            for line in invoice.customer_address.split("\n"):
                story.append(Paragraph(line, self.styles["ClientAddress"]))

        story.append(Spacer(1, 1 * cm))

        # --- Items Table ---
        data = []
        # Headers
        headers = ["Description", "Qty", "Unit Price", "Total"]
        data.append([Paragraph(h, self.styles["TableHeader"]) for h in headers])

        # Rows
        for item in invoice.items:
            data.append(
                [
                    Paragraph(item.product_name, self.styles["TableItem"]),
                    Paragraph(str(item.quantity), self.styles["TableNumber"]),
                    Paragraph(f"{item.unit_price:.2f}", self.styles["TableNumber"]),
                    Paragraph(f"{item.total_price:.2f}", self.styles["TableNumber"]),
                ]
            )

        # Table Style
        col_widths = [9 * cm, 2 * cm, 3 * cm, 3 * cm]
        table = Table(data, colWidths=col_widths)

        # Modern Table Styling
        ts = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),  # Numbers right aligned
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ecf0f1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
            ]
        )
        table.setStyle(ts)
        story.append(table)

        # --- Totals Section ---
        story.append(Spacer(1, 0.5 * cm))

        totals_data = [
            ["Total HT:", f"{invoice.subtotal:.2f}"],
            ["TVA:", f"{invoice.tax:.2f}"],
            ["Total TTC:", f"{invoice.total:.2f}"],
        ]

        totals_table = Table(totals_data, colWidths=[14 * cm, 3 * cm])
        totals_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),  # Bold TTC
                    ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#2c3e50")),
                    ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#2c3e50")),  # Line above TTC
                ]
            )
        )
        story.append(totals_table)

        # Build PDF
        doc.build(story)
