import typer

from sam_invoice.models.database import init_db

app = typer.Typer()


@app.command()
def initdb():
    """Initialize the SQLite database."""
    init_db()
    typer.echo("Database initialized.")


def main():
    app()


if __name__ == "__main__":
    main()
