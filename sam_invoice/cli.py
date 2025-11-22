"""Interface en ligne de commande pour Sam Invoice."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

import sam_invoice.models.crud_article as crud_article
import sam_invoice.models.crud_customer as crud_customer
from sam_invoice.models.database import init_db

console = Console()
app = typer.Typer()

# Groupe de commandes pour la base de données
db_app = typer.Typer()
app.add_typer(db_app, name="db")

# Groupe de commandes pour les fixtures
fixtures_app = typer.Typer()
app.add_typer(fixtures_app, name="fixtures")


@db_app.command("init")
def initdb():
    """Initialiser la base de données SQLite."""
    init_db()
    typer.echo("Database initialized.")


@fixtures_app.command("load-customers")
def load_customers(path: Path = None, verbose: bool = True):
    """Charger des clients depuis un fichier JSON de fixtures dans la base de données.

    Fichier par défaut: `fixtures/customers.json` à la racine du projet.
    """
    # Déterminer le chemin du fichier de fixtures
    if path is None:
        pkg_dir = Path(__file__).resolve().parent.parent
        path = pkg_dir / "fixtures" / "customers.json"

    if not path.exists():
        typer.echo(f"Fixtures file not found: {path}")
        raise typer.Exit(code=1)

    # S'assurer que la DB existe
    init_db()

    # Charger les données JSON
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Importer avec barre de progression
    created = 0
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

            # Créer le client (pas de vérification de doublon)
            cust = crud_customer.create_customer(name=name, address=address, email=email)
            if cust:
                created += 1
                progress.advance(task)
                if verbose:
                    console.print(f"Created customer {cust.id} - {cust.name}")

    console.print(f"Loaded {created} customers from {path}", style="green")


@fixtures_app.command("load-articles")
def load_articles(path: Path = None, verbose: bool = True):
    """Charger des articles depuis un fichier JSON de fixtures dans la base de données.

    Fichier par défaut: `fixtures/articles.json` à la racine du projet.
    """
    # Déterminer le chemin du fichier de fixtures
    if path is None:
        pkg_dir = Path(__file__).resolve().parent.parent
        path = pkg_dir / "fixtures" / "articles.json"

    if not path.exists():
        typer.echo(f"Fixtures file not found: {path}")
        raise typer.Exit(code=1)

    # S'assurer que la DB existe
    init_db()

    # Charger les données JSON
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Importer avec barre de progression
    created = 0
    with Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Importing articles", total=len(data))

        for item in data:
            ref = item.get("ref")
            desc = item.get("desc")
            prix = item.get("prix", 0.0)
            stock = item.get("stock", 0)
            vendu = item.get("vendu", 0)

            # Créer l'article (pas de vérification de doublon)
            article = crud_article.create_article(ref=ref, desc=desc, prix=prix, stock=stock, vendu=vendu)
            if article:
                created += 1
                progress.advance(task)
                if verbose:
                    console.print(f"Created article {article.id} - {article.ref}")

    console.print(f"Loaded {created} articles from {path}", style="green")


def main():
    app()


if __name__ == "__main__":
    main()
