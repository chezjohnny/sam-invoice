"""Widget de détail article utilisant la classe de base."""

from PySide6.QtWidgets import QMessageBox

from sam_invoice.ui.base_widgets import BaseDetailWidget


class ArticleDetailWidget(BaseDetailWidget):
    """Widget de détail article avec vue/édition.

    Affiche les informations de l'article (ref, desc, prix, stock, vendu)
    avec possibilité d'éditer, sauvegarder et supprimer.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Définir les alias pour les signaux
        self.article_saved = self.item_saved
        self.article_deleted = self.item_deleted

        # Stocker les valeurs brutes pour l'édition
        self._raw_values = {}

        # Ajouter les champs spécifiques à l'article
        self._add_field("ref", "", "e.g. ART-001", is_primary=True)
        self._add_field("desc", "", "Description", word_wrap=True)
        self._add_field("prix", "", "Prix (e.g. 12.50)")
        self._add_field("stock", "", "Stock (entier)")
        self._add_field("vendu", "", "Vendu (entier)")

        # Finaliser le layout
        self._finalize_layout()

        # Charger l'icône
        self._load_avatar_icon("articles")

    def _save_changes(self):
        """Sauvegarder les modifications de l'article."""
        data = {
            "id": self._current_id,
            "ref": self._fields["ref"][1].text().strip(),
            "desc": self._fields["desc"][1].text().strip(),
            "prix": self._to_float(self._fields["prix"][1].text()),
            "stock": self._to_int(self._fields["stock"][1].text()),
            "vendu": self._to_int(self._fields["vendu"][1].text()),
        }
        self.article_saved.emit(data)
        self._enter_edit_mode(False)

    def _on_delete_clicked(self):
        """Demander confirmation et supprimer l'article."""
        if self._current_id is None:
            return

        ref = self._fields["ref"][0].text() or ""
        res = QMessageBox.question(
            self,
            "Delete",
            f"Delete article '{ref}'? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if res == QMessageBox.StandardButton.Yes:
            self.article_deleted.emit(int(self._current_id))

    def _validate_fields(self) -> bool:
        """Valider les champs du formulaire."""
        ref = self._fields["ref"][1].text().strip()
        desc = self._fields["desc"][1].text().strip()
        prix_str = self._fields["prix"][1].text().strip()

        valid = True  # Validation de la référence
        ref_label, ref_edit, ref_err = self._fields["ref"]
        if not ref:
            ref_err.setText("Reference is required")
            ref_err.setVisible(True)
            valid = False
        else:
            ref_err.setVisible(False)

        # Validation de la description
        desc_label, desc_edit, desc_err = self._fields["desc"]
        if not desc:
            desc_err.setText("Description is required")
            desc_err.setVisible(True)
            valid = False
        else:
            desc_err.setVisible(False)

        # Validation du prix
        prix_label, prix_edit, prix_err = self._fields["prix"]
        prix = self._to_float(prix_str)
        if prix is None:
            prix_err.setText("Invalid price (use decimal number)")
            prix_err.setVisible(True)
            valid = False
        else:
            prix_err.setVisible(False)

        # Validation du stock (optionnel, pas d'erreur visible)

        # Validation du vendu (optionnel, pas d'erreur visible)

        self._save_btn.setEnabled(valid)
        return valid

    def set_article(self, art):
        """Afficher les informations d'un article."""
        self._current_id = getattr(art, "id", None) if art else None

        if not art:
            # Effacer l'affichage
            self._fields["ref"][0].setText("")
            self._fields["desc"][0].setText("")
            self._fields["prix"][0].setText("")
            self._fields["stock"][0].setText("")
            self._fields["vendu"][0].setText("")
            self._raw_values = {}
            self._edit_btn.setEnabled(False)
            self._edit_btn.setVisible(False)
            self._delete_btn.setVisible(False)
        else:
            # Stocker les valeurs brutes
            self._raw_values = {
                "ref": getattr(art, "ref", ""),
                "desc": getattr(art, "desc", ""),
                "prix": str(getattr(art, "prix", 0.0)),
                "stock": str(getattr(art, "stock", 0)),
                "vendu": str(getattr(art, "vendu", 0)),
            }

            # Afficher les données de l'article avec formatage
            self._fields["ref"][0].setText(self._raw_values["ref"])
            self._fields["desc"][0].setText(self._raw_values["desc"])

            # Prix formaté
            prix = getattr(art, "prix", 0.0)
            self._fields["prix"][0].setText(f"Prix: {prix:.2f} €" if prix else "")

            # Stock et vendu
            stock = getattr(art, "stock", 0)
            self._fields["stock"][0].setText(f"Stock: {stock}")

            vendu = getattr(art, "vendu", 0)
            self._fields["vendu"][0].setText(f"Vendu: {vendu}")

            self._edit_btn.setEnabled(True)
            self._edit_btn.setVisible(True)
            self._delete_btn.setVisible(self._current_id is not None)

    def _enter_edit_mode(self, editing: bool):
        """Basculer entre le mode visualisation et le mode édition."""
        self.editing_changed.emit(editing)

        # Afficher/masquer les widgets
        for field_name, (label, edit, _error) in self._fields.items():
            label.setVisible(not editing)
            edit.setVisible(editing)
            if editing:
                # Utiliser les valeurs brutes au lieu du texte formaté du label
                raw_value = self._raw_values.get(field_name, "")
                edit.setText(raw_value)

        self._edit_btn.setVisible(not editing)
        self._save_btn.setVisible(editing)
        self._cancel_btn.setVisible(editing)
        self._delete_btn.setVisible(not editing and self._current_id is not None)

        if editing:
            self._validate_fields()

    # === Méthodes utilitaires pour conversion ===

    @staticmethod
    def _to_float(s: str):
        """Convertir une chaîne en float, retourner None si invalide."""
        try:
            return float(s) if s.strip() else 0.0
        except ValueError:
            return None

    @staticmethod
    def _to_int(s: str) -> int:
        """Convertir une chaîne en int, retourner 0 si vide ou invalide."""
        try:
            return int(s) if s.strip() else 0
        except ValueError:
            return 0
