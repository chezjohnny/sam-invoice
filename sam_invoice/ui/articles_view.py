"""Vue des articles utilisant la classe de base."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMessageBox

import sam_invoice.models.crud_article as crud
from sam_invoice.ui.article_detail import ArticleDetailWidget
from sam_invoice.ui.base_widgets import BaseListView


class ArticlesView(BaseListView):
    """Widget de vue articles avec disposition deux colonnes.

    Colonne gauche: recherche et liste des articles
    Colonne droite: détail de l'article avec actions edit/save/delete
    """

    article_selected = Signal(object)

    def _search_placeholder(self) -> str:
        """Texte du placeholder de recherche."""
        return "Rechercher un article (ref, description)..."

    def _search_function(self, query: str, limit: int):
        """Fonction de recherche pour les articles."""
        rows = crud.search_articles(query, limit=limit)
        return sorted(rows, key=lambda a: (getattr(a, "ref", "") or "").lower())

    def _create_detail_widget(self):
        """Créer le widget de détail article."""
        detail = ArticleDetailWidget(self)
        detail.article_saved.connect(self._on_saved)
        detail.article_deleted.connect(self._on_deleted)
        return detail

    def _get_all_items(self):
        """Obtenir tous les articles."""
        return crud.get_articles()

    def _format_list_item(self, article) -> str:
        """Formater un article pour l'affichage dans la liste."""
        ref = getattr(article, "ref", "") or "(sans ref)"
        desc = getattr(article, "desc", "")
        if desc:
            return f"{ref} - {desc}"
        return ref

    def _on_saved(self, data: dict):
        """Callback quand un article est sauvegardé."""
        art_id = data.get("id")
        try:
            if art_id:
                # Mise à jour
                crud.update_article(
                    art_id,
                    ref=data.get("ref"),
                    desc=data.get("desc"),
                    prix=data.get("prix"),
                    stock=data.get("stock"),
                    vendu=data.get("vendu"),
                )
            else:
                # Création
                crud.create_article(
                    ref=data.get("ref"),
                    desc=data.get("desc"),
                    prix=data.get("prix"),
                    stock=data.get("stock"),
                    vendu=data.get("vendu"),
                )
            self.reload_items()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save article: {e}")

    def _on_deleted(self, art_id: int):
        """Callback quand un article est supprimé."""
        try:
            crud.delete_article(art_id)
            self.reload_items()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete article: {e}")

    def _on_item_activated(self, item):
        """Callback quand un item est activé."""
        if not item:
            return
        selected_article = item.data(Qt.ItemDataRole.UserRole)
        self._detail_widget.set_article(selected_article)
        self.article_selected.emit(selected_article)

    def _on_add_item(self):
        """Callback pour ajouter un nouvel item."""
        # Effacer la sélection
        self._results_list.clearSelection()
        self._detail_widget.set_article(None)
        # Passer en mode édition
        self._detail_widget._enter_edit_mode(True)
