"""Widgets de base réutilisables pour les vues de détail et liste."""

from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QSize, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# Métaclasse combinée pour résoudre le conflit entre QWidget et ABC
class QABCMeta(type(QWidget), ABCMeta):
    """Métaclasse combinée permettant d'utiliser ABC avec QWidget."""

    pass


class ClickableLabel(QLabel):
    """Label qui émet un signal lors d'un double-clic."""

    double_clicked = Signal()

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


class BaseDetailWidget(QWidget, metaclass=QABCMeta):
    """Classe de base pour les widgets de détail (Customer, Article, etc.).

    Fournit la structure commune : avatar, champs éditables, boutons d'action,
    validation, et gestion du mode édition.
    """

    # Signaux à redéfinir dans les sous-classes
    item_saved = Signal(object)
    editing_changed = Signal(bool)
    item_deleted = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_id = None
        self._fields = {}  # Dict[str, tuple[ClickableLabel, QLineEdit, QLabel]]

        # === Avatar ===
        self._avatar = QLabel()
        self._avatar.setFixedSize(96, 96)
        self._avatar.setAlignment(Qt.AlignCenter)

        # Layout principal
        content_layout = QHBoxLayout()
        content_layout.setAlignment(Qt.AlignTop)

        # Colonne gauche: avatar
        self._left_col = QVBoxLayout()
        self._left_col.addWidget(self._avatar, alignment=Qt.AlignHCenter | Qt.AlignTop)

        # Colonne droite: champs (à remplir par les sous-classes)
        self._right_col = QVBoxLayout()

        # Boutons d'action
        self._edit_btn = QPushButton("Edit")
        self._save_btn = QPushButton("Save")
        self._delete_btn = QPushButton("Delete")
        self._cancel_btn = QPushButton("Cancel")
        self._save_btn.setVisible(False)
        self._save_btn.setEnabled(False)
        self._cancel_btn.setVisible(False)
        self._edit_btn.setEnabled(False)
        self._delete_btn.setVisible(False)

        self._actions_layout = QHBoxLayout()
        self._actions_layout.addStretch()
        self._actions_layout.addWidget(self._edit_btn)
        self._actions_layout.addWidget(self._delete_btn)
        self._actions_layout.addWidget(self._save_btn)
        self._actions_layout.addWidget(self._cancel_btn)

        content_layout.addLayout(self._left_col, 1)
        content_layout.addLayout(self._right_col, 3)
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(content_layout)

        # Connexions communes
        self._edit_btn.clicked.connect(lambda: self._enter_edit_mode(True))
        self._cancel_btn.clicked.connect(lambda: self._enter_edit_mode(False))
        self._save_btn.clicked.connect(self._save_changes)
        self._delete_btn.clicked.connect(self._on_delete_clicked)

    def _add_field(
        self, name: str, label_text: str, placeholder: str, is_primary: bool = False, word_wrap: bool = False
    ):
        """Ajouter un champ éditable (label + edit + error).

        Args:
            name: Nom du champ (clé dans _fields)
            label_text: Texte initial du label
            placeholder: Placeholder pour le champ d'édition
            is_primary: Si True, utiliser une police grande et en gras
            word_wrap: Si True, activer le word wrap sur le label
        """
        # Label cliquable
        label = ClickableLabel(label_text)
        if is_primary:
            font = QFont()
            font.setPointSize(16)
            font.setBold(True)
            label.setFont(font)
        else:
            label.setStyleSheet("color: #444444;")
        if word_wrap:
            label.setWordWrap(True)

        # Champ d'édition
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setVisible(False)

        # Label d'erreur
        error = QLabel("")
        error.setStyleSheet("color: #c00; font-size:11px;")
        error.setVisible(False)

        # Stocker dans le dictionnaire
        self._fields[name] = (label, edit, error)

        # Ajouter au layout
        self._right_col.addWidget(label)
        self._right_col.addWidget(edit)
        self._right_col.addWidget(error)

        # Connecter le double-clic pour édition
        label.double_clicked.connect(lambda: self._enter_edit_mode(True))

        # Connecter la validation réactive
        edit.textChanged.connect(self._validate_fields)

        return label, edit, error

    def _load_avatar_icon(self, icon_name: str):
        """Charger l'icône avatar depuis le fichier SVG."""
        icons_dir = Path(__file__).parent.parent / "assets" / "icons"
        avatar_path = icons_dir / f"{icon_name}.svg"
        if avatar_path.exists():
            icon = QIcon(str(avatar_path))
            pix = icon.pixmap(QSize(96, 96))
            if not pix.isNull():
                self._avatar.setPixmap(pix)

    def _finalize_layout(self):
        """Finaliser le layout en ajoutant les boutons d'action."""
        self._right_col.addLayout(self._actions_layout)

    def _enter_edit_mode(self, editing: bool):
        """Basculer entre le mode visualisation et le mode édition."""
        self.editing_changed.emit(editing)

        # Afficher/masquer les widgets
        for label, edit, _error in self._fields.values():
            label.setVisible(not editing)
            edit.setVisible(editing)
            if editing:
                edit.setText(label.text())

        self._edit_btn.setVisible(not editing)
        self._save_btn.setVisible(editing)
        self._cancel_btn.setVisible(editing)
        self._delete_btn.setVisible(not editing and self._current_id is not None)

        if editing:
            self._validate_fields()

    @abstractmethod
    def _save_changes(self):
        """Sauvegarder les modifications (à implémenter dans les sous-classes)."""
        pass

    @abstractmethod
    def _on_delete_clicked(self):
        """Gérer la suppression (à implémenter dans les sous-classes)."""
        pass

    @abstractmethod
    def _validate_fields(self) -> bool:
        """Valider les champs (à implémenter dans les sous-classes)."""
        pass


class SearchWorker(QObject):
    """Worker qui exécute les recherches dans un thread séparé."""

    results_ready = Signal(object)
    error = Signal(str)

    def __init__(self, search_func):
        """Initialiser le worker avec une fonction de recherche.

        Args:
            search_func: Fonction callable(query: str, limit: int) -> list
        """
        super().__init__()
        self._search_func = search_func

    @Slot(str, int)
    def search(self, q: str, limit: int):
        try:
            rows = self._search_func(q, limit=limit)
            self.results_ready.emit(rows)
        except Exception as e:
            self.error.emit(str(e))
            self.results_ready.emit([])


class BaseListView(QWidget, metaclass=QABCMeta):
    """Classe de base pour les vues avec liste et détail (Customers, Articles, etc.).

    Fournit : recherche avec debounce, liste, détail, et gestion CRUD.
    """

    item_selected = Signal(object)
    search_requested = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Configuration du worker de recherche en arrière-plan
        self._search_thread = QThread(self)
        self._search_worker = SearchWorker(self._search_function)
        self._search_worker.moveToThread(self._search_thread)
        self._search_worker.results_ready.connect(self._on_search_results)
        self._search_worker.error.connect(lambda e: print(f"[search error] {e}"))
        self.search_requested.connect(self._search_worker.search)
        self._search_thread.start()

        # Timer pour debounce de la recherche
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._perform_search)

        layout = QHBoxLayout(self)

        # === Colonne gauche: recherche et liste ===
        left_layout = QVBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(self._search_placeholder())

        self._results_count_label = QLabel("")
        self._results_count_label.setStyleSheet("color: #666; font-size:11px; padding:4px 0;")

        self._results_list = QListWidget()
        self._results_list.setSelectionMode(QListWidget.SingleSelection)

        self._add_btn = QPushButton("Add")

        left_layout.addWidget(self.search_box)
        left_layout.addWidget(self._results_count_label)
        left_layout.addWidget(self._results_list, 1)
        left_layout.addWidget(self._add_btn)

        # === Colonne droite: détail (à créer dans les sous-classes) ===
        self._detail_widget = self._create_detail_widget()

        layout.addLayout(left_layout, 1)
        layout.addWidget(self._detail_widget, 2)

        # === Connexions des signaux ===
        self._detail_widget.item_saved.connect(self._on_saved)
        self._detail_widget.item_deleted.connect(self._on_deleted)
        self.search_box.textChanged.connect(self._on_search_text_changed)
        self._results_list.itemActivated.connect(self._on_item_activated)
        self._results_list.itemClicked.connect(self._on_item_activated)
        self._results_list.currentItemChanged.connect(lambda cur, prev: self._on_item_activated(cur) if cur else None)
        self._add_btn.clicked.connect(self._on_add_item)

        # Charger les données initiales après l'initialisation complète
        QTimer.singleShot(0, self.reload_items)

    @abstractmethod
    def _search_placeholder(self) -> str:
        """Retourner le placeholder pour le champ de recherche."""
        pass

    @abstractmethod
    def _search_function(self):
        """Retourner la fonction de recherche à utiliser."""
        pass

    @abstractmethod
    def _create_detail_widget(self) -> BaseDetailWidget:
        """Créer et retourner le widget de détail."""
        pass

    @abstractmethod
    def _get_all_items(self) -> list:
        """Récupérer tous les items depuis la base de données."""
        pass

    @abstractmethod
    def _format_list_item(self, item: Any) -> str:
        """Formater un item pour l'affichage dans la liste."""
        pass

    @abstractmethod
    def _on_saved(self, data: dict):
        """Gérer la sauvegarde d'un item."""
        pass

    @abstractmethod
    def _on_deleted(self, item_id: int | None):
        """Gérer la suppression d'un item."""
        pass

    def _on_search_text_changed(self, text: str):
        """Redémarrer le timer de debounce quand l'utilisateur tape."""
        if not text or not text.strip():
            self._search_timer.stop()
            self.reload_items()
        else:
            self._search_timer.start()

    def _perform_search(self):
        """Exécuter la recherche via le worker en arrière-plan."""
        q = self.search_box.text().strip()
        if not q:
            self.reload_items()
        else:
            self.search_requested.emit(q, 50)

    def _on_search_results(self, rows: list):
        """Gérer les résultats de recherche du worker."""
        max_shown = 50
        rows_limited = rows[:max_shown]

        self._results_list.clear()
        for item in rows_limited:
            disp = self._format_list_item(item)
            list_item = QListWidgetItem(disp)
            list_item.setData(Qt.ItemDataRole.UserRole, item)  # Stocker l'objet complet
            self._results_list.addItem(list_item)

        # Sélectionner le premier résultat
        if self._results_list.count() > 0:
            self._results_list.setCurrentRow(0)
            self._on_item_activated(self._results_list.item(0))

        # Mettre à jour le compteur
        try:
            total = len(self._get_all_items())
            shown = len(rows_limited)
            self._results_count_label.setText(f"{shown} / {total} résultats")
        except Exception:
            self._results_count_label.setText("")

    def reload_items(self, select_first: bool = True):
        """Recharger la liste des items depuis la base de données."""
        try:
            items = self._get_all_items()
        except Exception:
            items = []

        self._results_list.clear()
        for item in items:
            disp = self._format_list_item(item)
            list_item = QListWidgetItem(disp)
            list_item.setData(Qt.ItemDataRole.UserRole, item)  # Stocker l'objet complet
            self._results_list.addItem(list_item)

        total = len(items)
        shown = min(total, 50)
        self._results_count_label.setText(f"{shown} / {total} résultats")

        if select_first and self._results_list.count() > 0:
            first_item = self._results_list.item(0)
            self._results_list.setCurrentRow(0)
            if first_item:
                self._on_item_activated(first_item)

    @abstractmethod
    def _on_item_activated(self, item: QListWidgetItem):
        """Gérer la sélection d'un item dans la liste."""
        pass

    @abstractmethod
    def _on_add_item(self):
        """Créer un item vide et ouvrir l'éditeur."""
        pass

    def cleanup(self):
        """Nettoyer les ressources (thread de recherche)."""
        if hasattr(self, "_search_thread") and self._search_thread.isRunning():
            self._search_thread.quit()
            self._search_thread.wait(1000)
