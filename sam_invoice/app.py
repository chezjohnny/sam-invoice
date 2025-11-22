"""Application principale Sam Invoice."""

import os
import signal
import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QStyle,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from sam_invoice.ui.articles_view import ArticlesView
from sam_invoice.ui.customer_view import CustomerView


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application Sam Invoice."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sam Invoice")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # === En-tête ===
        header = QLabel("Sam Invoice")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size:18pt; font-weight:600; padding:8px;")
        main_layout.addWidget(header)

        # === Barre d'outils ===
        toolbar = self._create_toolbar()
        self.addToolBar(toolbar)

        # === Zone empilée pour les vues ===
        self.stack = QStackedWidget()

        # Vue Customers (Home)
        self._customer_view = CustomerView()
        self.stack.addWidget(self._customer_view)

        # Vue Articles
        self._articles_view = ArticlesView()
        self.stack.addWidget(self._articles_view)

        # Vue Invoices (placeholder)
        invoices_placeholder = self._create_placeholder("Invoices (coming soon)")
        self.stack.addWidget(invoices_placeholder)

        main_layout.addWidget(self.stack)

        # === Barre de status ===
        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status)

        try:
            style_name = QApplication.instance().style().objectName()
            self.status.setText(f"Style: {style_name}")
        except Exception:
            pass

        self.setCentralWidget(central_widget)

        # === Connexions des actions de la toolbar ===
        self.act_home.triggered.connect(lambda: self._set_active(self.act_home) or self._show_view(0, "Customers"))
        self.act_articles.triggered.connect(
            lambda: self._set_active(self.act_articles) or self._show_view(1, "Articles")
        )
        self.act_invoices.triggered.connect(
            lambda: self._set_active(self.act_invoices) or self._show_view(2, "Invoices")
        )

        # Activer Home par défaut
        self._set_active(self.act_home)

    def _create_toolbar(self) -> QToolBar:
        """Créer la barre d'outils avec les actions de navigation."""
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)

        # Unified toolbar sur macOS
        if sys.platform == "darwin":
            self.setUnifiedTitleAndToolBarOnMac(True)

        # Charger les icônes
        icons_dir = Path(__file__).parent / "assets" / "icons"
        home_icon = self._load_icon(icons_dir / "home.svg", QStyle.SP_DirHomeIcon)
        articles_icon = self._load_icon(icons_dir / "articles.svg", QStyle.SP_FileDialogDetailedView)
        invoices_icon = self._load_icon(icons_dir / "invoices.svg", QStyle.SP_FileIcon)

        # Créer les actions
        self.act_home = QAction(home_icon, "Customers", self)
        self.act_home.setCheckable(True)
        self.act_articles = QAction(articles_icon, "Articles", self)
        self.act_articles.setCheckable(True)
        self.act_invoices = QAction(invoices_icon, "Invoices", self)
        self.act_invoices.setCheckable(True)

        # Créer les variants colorés des icônes
        active_color = QColor("#3b82f6")
        self._icon_pairs = {
            self.act_home: (home_icon, self._colorize_icon(home_icon, active_color)),
            self.act_articles: (articles_icon, self._colorize_icon(articles_icon, active_color)),
            self.act_invoices: (invoices_icon, self._colorize_icon(invoices_icon, active_color)),
        }

        # Ajouter les actions à la toolbar
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.addAction(self.act_home)
        toolbar.addAction(self.act_articles)
        toolbar.addAction(self.act_invoices)

        return toolbar

    def _load_icon(self, path: Path, fallback: QStyle.StandardPixmap) -> QIcon:
        """Charger une icône depuis un fichier ou utiliser l'icône de fallback."""
        if path.exists():
            return QIcon(str(path))
        return self.style().standardIcon(fallback)

    def _colorize_icon(self, icon: QIcon, color: QColor) -> QIcon:
        """Créer une version colorée d'une icône."""
        size = QSize(48, 48)
        pix = icon.pixmap(size)
        if pix.isNull():
            return icon

        colored = QPixmap(pix.size())
        colored.fill(Qt.transparent)
        p = QPainter(colored)
        p.fillRect(colored.rect(), color)
        p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        p.drawPixmap(0, 0, pix)
        p.end()
        return QIcon(colored)

    def _create_placeholder(self, text: str) -> QWidget:
        """Créer un widget placeholder avec un texte centré."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return widget

    def _set_active(self, action: QAction):
        """Définir une action comme active et désactiver les autres."""
        for act in (self.act_home, self.act_articles, self.act_invoices):
            is_active = act is action
            act.setChecked(is_active)

            # Changer l'icône selon l'état actif/inactif
            pair = self._icon_pairs.get(act)
            if pair:
                normal_icon, active_icon = pair
                act.setIcon(active_icon if is_active else normal_icon)

    def _show_view(self, index: int, label: str):
        """Afficher une vue spécifique dans le stack."""
        self.stack.setCurrentIndex(index)
        self.status.setText(label)

    def closeEvent(self, event):
        """Nettoyer les ressources avant de fermer l'application."""
        # Nettoyer les threads dans les vues
        if hasattr(self, "_customer_view"):
            self._customer_view.cleanup()
        if hasattr(self, "_articles_view"):
            # Ajouter cleanup si ArticlesView a aussi un thread
            if hasattr(self._articles_view, "cleanup"):
                self._articles_view.cleanup()
        super().closeEvent(event)


def main():
    """Point d'entrée principal de l'application."""
    # Éviter les messages Qt verbeux
    os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts=false")

    app = QApplication(sys.argv)

    # Découvrir les styles disponibles
    try:
        from PySide6.QtWidgets import QStyleFactory

        available = list(QStyleFactory.keys())
    except Exception:
        available = []

    # Respecter le style demandé en ligne de commande (-style macOS)
    requested_style = None
    for i, a in enumerate(sys.argv):
        if a == "-style" and i + 1 < len(sys.argv):
            requested_style = sys.argv[i + 1]
            break

    # Appliquer le style
    if requested_style:
        if requested_style in available:
            app.setStyle(requested_style)
        else:
            fallback = "macOS" if "macOS" in available else "Fusion"
            if available:
                app.setStyle(fallback)
    else:
        # Par défaut macOS si disponible
        if "macOS" in available:
            app.setStyle("macOS")

    # Déterminer la classe de style
    try:
        style_class = app.style().__class__.__name__
    except Exception:
        style_class = None

    # Palette macOS si QCommonStyle
    if requested_style and requested_style.lower().startswith("mac") and style_class == "QCommonStyle":
        from PySide6.QtGui import QColor, QPalette

        mac_pal = QPalette()
        mac_pal.setColor(QPalette.ColorRole.Window, QColor("#ececec"))
        mac_pal.setColor(QPalette.ColorRole.Button, QColor("#ececec"))
        mac_pal.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
        mac_pal.setColor(QPalette.ColorRole.Text, QColor("#000000"))
        mac_pal.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))
        mac_pal.setColor(QPalette.ColorRole.Highlight, QColor("#a5cdff"))
        app.setPalette(mac_pal)

    # Charger le QSS macOS
    try:
        qss_path = Path(__file__).parent / "assets" / "styles" / "macos.qss"
        if qss_path.exists() and (
            (requested_style and requested_style.lower().startswith("mac")) or style_class == "QCommonStyle"
        ):
            with qss_path.open("r", encoding="utf-8") as f:
                qss = f.read()
            if qss:
                app.setStyleSheet(qss)
    except Exception:
        pass

    app.setApplicationName("Sam Invoice")

    # Créer la fenêtre
    window = MainWindow()
    window.showMaximized()

    # Configurer la gestion de Ctrl-C pour fermer proprement
    def sigint_handler(signum, frame):
        """Handler pour Ctrl-C qui ferme proprement l'application."""
        print("\nFermeture de l'application...")
        QApplication.quit()

    signal.signal(signal.SIGINT, sigint_handler)

    # Timer pour permettre à Python de traiter les signaux pendant la boucle Qt
    from PySide6.QtCore import QTimer

    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Juste pour réveiller la boucle d'événements
    timer.start(500)  # Toutes les 500ms

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
