"""Opérations CRUD pour les articles."""

from sqlalchemy import func

from . import database
from .article import Article


def create_article(
    ref: str, desc: str = None, prix: float | None = None, stock: int | None = None, vendu: int | None = None
):
    """Créer un nouvel article dans la base de données."""
    session = database.SessionLocal()
    try:
        art = Article(ref=ref, desc=desc, prix=prix, stock=stock, vendu=vendu)
        session.add(art)
        session.commit()
        session.refresh(art)
        return art
    finally:
        session.close()


def get_articles():
    """Récupérer tous les articles, triés par référence."""
    session = database.SessionLocal()
    try:
        return session.query(Article).order_by(func.lower(Article.ref)).all()
    finally:
        session.close()


def search_articles(query: str, limit: int | None = None):
    """Rechercher des articles par ID exact ou par correspondance partielle sur ref/desc.

    Args:
        query: Texte de recherche
        limit: Nombre maximum de résultats (None = pas de limite)

    Returns:
        Liste d'objets Article correspondants
    """
    session = database.SessionLocal()
    try:
        q = (query or "").strip()

        # Si pas de recherche, retourner tous les articles
        if not q:
            stmt = session.query(Article).order_by(func.lower(Article.ref))
            return stmt.limit(limit).all() if limit else stmt.all()

        # Construire les filtres de recherche
        filters = [
            Article.ref.ilike(f"%{q}%"),
            Article.desc.ilike(f"%{q}%"),
        ]

        # Ajouter filtre ID si la recherche est numérique
        try:
            filters.append(Article.id == int(q))
        except ValueError:
            pass

        # Exécuter la recherche
        from sqlalchemy import or_

        stmt = session.query(Article).filter(or_(*filters)).order_by(func.lower(Article.ref))
        return stmt.limit(limit).all() if limit else stmt.all()
    finally:
        session.close()


def get_article_by_id(article_id: int):
    """Récupérer un article par son ID."""
    session = database.SessionLocal()
    try:
        return session.query(Article).filter(Article.id == article_id).first()
    finally:
        session.close()


def update_article(
    article_id: int, ref: str = None, desc: str = None, prix: float = None, stock: int = None, vendu: int = None
):
    """Mettre à jour les informations d'un article existant."""
    session = database.SessionLocal()
    try:
        art = session.query(Article).filter(Article.id == article_id).first()
        if art:
            if ref is not None:
                art.ref = ref
            if desc is not None:
                art.desc = desc
            if prix is not None:
                art.prix = prix
            if stock is not None:
                art.stock = stock
            if vendu is not None:
                art.vendu = vendu
            session.commit()
            session.refresh(art)
        return art
    finally:
        session.close()


def delete_article(article_id: int):
    """Supprimer un article de la base de données."""
    session = database.SessionLocal()
    try:
        art = session.query(Article).filter(Article.id == article_id).first()
        if art:
            session.delete(art)
            session.commit()
        return art
    finally:
        session.close()
