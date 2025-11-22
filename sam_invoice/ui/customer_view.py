"""Vue des clients utilisant la classe de base."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMessageBox

import sam_invoice.models.crud_customer as crud
from sam_invoice.ui.base_widgets import BaseListView
from sam_invoice.ui.customer_detail import CustomerDetailWidget


class CustomerView(BaseListView):
    """Widget de vue clients avec disposition deux colonnes.

    Colonne gauche: recherche et liste des clients
    Colonne droite: détail du client avec actions edit/save/delete
    """

    customer_selected = Signal(object)

    def _search_placeholder(self) -> str:
        """Texte du placeholder de recherche."""
        return "Rechercher un client (nom, email)..."

    def _search_function(self, query: str, limit: int):
        """Fonction de recherche pour les clients."""
        rows = crud.search_customers(query, limit=limit)
        return sorted(rows, key=lambda c: (getattr(c, "name", "") or "").lower())

    def _create_detail_widget(self):
        """Créer le widget de détail client."""
        detail = CustomerDetailWidget(self)
        detail.customer_saved.connect(self._on_saved)
        detail.customer_deleted.connect(self._on_deleted)
        return detail

    def _get_all_items(self):
        """Obtenir tous les clients."""
        return crud.get_customers()

    def _format_list_item(self, customer) -> str:
        """Formater un client pour l'affichage dans la liste."""
        name = getattr(customer, "name", "") or "(sans nom)"
        email = getattr(customer, "email", "")
        if email:
            return f"{name} ({email})"
        return name

    def _on_saved(self, data: dict):
        """Callback quand un client est sauvegardé."""
        cust_id = data.get("id")
        try:
            if cust_id:
                # Mise à jour
                crud.update_customer(
                    cust_id, name=data.get("name"), address=data.get("address"), email=data.get("email")
                )
            else:
                # Création
                crud.create_customer(name=data.get("name"), address=data.get("address"), email=data.get("email"))
            self.reload_items()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save customer: {e}")

    def _on_deleted(self, cust_id: int):
        """Callback quand un client est supprimé."""
        try:
            crud.delete_customer(cust_id)
            self.reload_items()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete customer: {e}")

    def _on_item_activated(self, item):
        """Callback quand un item est activé."""
        if not item:
            return
        selected_customer = item.data(Qt.ItemDataRole.UserRole)
        self._detail_widget.set_customer(selected_customer)
        self.customer_selected.emit(selected_customer)

    def _on_add_item(self):
        """Callback pour ajouter un nouvel item."""
        # Effacer la sélection
        self._results_list.clearSelection()
        self._detail_widget.set_customer(None)
        # Passer en mode édition
        self._detail_widget._enter_edit_mode(True)
