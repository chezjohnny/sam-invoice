"""Command line interface for Sam Invoice."""

import json
from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from sam_invoice.models.crud_customer import customer_crud
from sam_invoice.models.crud_invoice import invoice_crud
from sam_invoice.models.crud_product import product_crud
from sam_invoice.models.database import db_manager

console = Console()
app = typer.Typer()

# Database commands group
db_app = typer.Typer()
app.add_typer(db_app, name="db")

# Fixtures commands group
fixtures_app = typer.Typer()
app.add_typer(fixtures_app, name="fixtures")


@db_app.command("init")
def initdb(db_path: Annotated[Path, typer.Option("--db", help="Path to database file")] = None):
    """Initialize the SQLite database."""
    if db_path:
        db_manager.set_database_path(db_path)
    db_manager.init_db()
    typer.echo("Database initialized.")


@fixtures_app.command("load-customers")
def load_customers(
    path: Annotated[Path, typer.Argument(help="Path to customers JSON file")] = None,
    db_path: Annotated[Path, typer.Option("--db", help="Path to database file")] = None,
    verbose: bool = True,
):
    """Load customers from a JSON fixtures file into the database.

    Default file: `fixtures/customers.json` at project root.
    """
    # Set database path if provided
    if db_path:
        db_manager.set_database_path(db_path)

    # Determine fixtures file path
    if path is None:
        pkg_dir = Path(__file__).resolve().parent.parent
        path = pkg_dir / "fixtures" / "customers.json"

    if not path.exists():
        typer.echo(f"Fixtures file not found: {path}")
        raise typer.Exit(code=1)

    # Ensure DB exists
    db_manager.init_db()

    # Load JSON data
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Import with progress bar
    created = 0
    errors = 0
    with Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Importing customers", total=len(data))

        for item in data:
            name = item.get("name")
            address = item.get("address")
            email = item.get("email")

            try:
                # Create customer (no duplicate check)
                cust = customer_crud.create(name=name, address=address, email=email)
                if cust:
                    created += 1
                    progress.advance(task)
                    if verbose:
                        console.print(f"Created customer {cust.id} - {cust.name}")
                else:
                    progress.advance(task)
            except Exception as e:
                errors += 1
                progress.advance(task)
                console.print(f"[yellow]Warning: Failed to create customer '{name}': {e}[/yellow]")

    if errors > 0:
        console.print(f"Loaded {created} customers from {path} ({errors} errors)", style="yellow")
    else:
        console.print(f"Loaded {created} customers from {path}", style="green")


@fixtures_app.command("load-products")
def load_products(
    path: Annotated[Path, typer.Argument(help="Path to products JSON file")] = None,
    db_path: Annotated[Path, typer.Option("--db", help="Path to database file")] = None,
    verbose: bool = True,
):
    """Load products from a JSON fixtures file into the database.

    Default file: `fixtures/products.json` at project root.
    """
    # Set database path if provided
    if db_path:
        db_manager.set_database_path(db_path)

    # Determine fixtures file path
    if path is None:
        pkg_dir = Path(__file__).resolve().parent.parent
        path = pkg_dir / "fixtures" / "products.json"

    if not path.exists():
        typer.echo(f"Fixtures file not found: {path}")
        raise typer.Exit(code=1)

    # Ensure DB exists
    db_manager.init_db()

    # Load JSON data
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Import with progress bar
    created = 0
    errors = 0
    with Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Importing products", total=len(data))

        for item in data:
            reference = item.get("reference")
            name = item.get("name")
            price = item.get("price", 0.0)
            stock = item.get("stock", 0)
            sold = item.get("sold", 0)

            try:
                # Create or update product (handled by CRUD)
                product = product_crud.create(reference=reference, name=name, price=price, stock=stock, sold=sold)
                if product:
                    created += 1
                    progress.advance(task)
                    if verbose:
                        console.print(f"Processed product {product.id} - {product.reference}")
                else:
                    progress.advance(task)
            except Exception as e:
                errors += 1
                progress.advance(task)
                console.print(f"[yellow]Warning: Failed to process product '{reference}': {e}[/yellow]")

    if errors > 0:
        console.print(f"Loaded {created} products from {path} ({errors} errors)", style="yellow")
    else:
        console.print(f"Loaded {created} products from {path}", style="green")


@fixtures_app.command("load-invoices")
def load_invoices(
    path: Annotated[Path, typer.Argument(help="Path to invoices JSON file")] = None,
    db_path: Annotated[Path, typer.Option("--db", help="Path to database file")] = None,
    verbose: bool = True,
):
    """Load invoices from a JSON fixtures file into the database.

    Default file: `fixtures/invoices.json` at project root.
    """
    # Set database path if provided
    if db_path:
        db_manager.set_database_path(db_path)

    # Determine fixtures file path
    if path is None:
        pkg_dir = Path(__file__).resolve().parent.parent
        path = pkg_dir / "fixtures" / "invoices.json"

    if not path.exists():
        typer.echo(f"Fixtures file not found: {path}")
        raise typer.Exit(code=1)

    # Ensure DB exists
    db_manager.init_db()

    # Load JSON data
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Import with progress bar
    created = 0
    errors = 0
    with Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Importing invoices", total=len(data))

        for item in data:
            reference = item.get("ref")
            date_str = item.get("date")
            due_date_str = item.get("echeance")
            customer_raw = item.get("client", "")

            # Parse customer name and address
            customer_lines = customer_raw.strip().split("\n")
            customer_name = customer_lines[0].strip() if customer_lines else "Unknown"
            customer_address = "\n".join(line.strip() for line in customer_lines[1:] if line.strip())

            # Parse totals
            subtotal = float(item.get("sumHT", 0))
            tax = float(item.get("sumTVA", 0))
            total = float(item.get("sumTTC", 0))

            # Parse items
            achats = item.get("achats", [])
            items_data = []
            for achat in achats:
                items_data.append(
                    {
                        "product_name": achat.get("desc", ""),
                        "quantity": int(achat.get("quantite", 1)),
                        "unit_price": float(achat.get("puht", 0)),
                        "total_price": float(achat.get("pht", 0)),
                    }
                )

            try:
                # Parse dates
                inv_date = date.fromisoformat(date_str) if date_str else date.today()
                due_date = date.fromisoformat(due_date_str) if due_date_str else None

                # Create invoice
                inv = invoice_crud.create(
                    reference=reference,
                    date=inv_date,
                    due_date=due_date,
                    customer_name=customer_name,
                    customer_address=customer_address,
                    subtotal=subtotal,
                    tax=tax,
                    total=total,
                    items_data=items_data,
                )

                if inv:
                    created += 1
                    progress.advance(task)
                    if verbose:
                        console.print(f"Created invoice {inv.reference} - {inv.customer_name}")
                else:
                    progress.advance(task)
            except Exception as e:
                errors += 1
                progress.advance(task)
                console.print(f"[yellow]Warning: Failed to create invoice '{reference}': {e}[/yellow]")

    if errors > 0:
        console.print(f"Loaded {created} invoices from {path} ({errors} errors)", style="yellow")
    else:
        console.print(f"Loaded {created} invoices from {path}", style="green")


def main():
    app()


if __name__ == "__main__":
    main()
