"""Sam Invoice main application."""

import os
import signal
import sys
from pathlib import Path

import qtawesome as qta
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

from sam_invoice.ui.customer_view import CustomerView
from sam_invoice.ui.products_view import ProductsView


class MainWindow(QMainWindow):
    """Sam Invoice application main window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sam Invoice")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # === Toolbar ===
        toolbar = self._create_toolbar()
        self.addToolBar(toolbar)

        # === Stacked area for views ===
        self.stack = QStackedWidget()

        # Customers view (Home)
        self._customer_view = CustomerView()
        self.stack.addWidget(self._customer_view)

        # Products view
        self._products_view = ProductsView()
        self.stack.addWidget(self._products_view)

        # Invoices view (placeholder)
        invoices_placeholder = self._create_placeholder("Invoices (coming soon)")
        self.stack.addWidget(invoices_placeholder)

        main_layout.addWidget(self.stack)

        # === Status bar ===
        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status)

        try:
            style_name = QApplication.instance().style().objectName()
            self.status.setText(f"Style: {style_name}")
        except Exception:
            pass

        self.setCentralWidget(central_widget)

        # === Toolbar action connections ===
        self.act_home.triggered.connect(lambda: self._set_active(self.act_home) or self._show_view(0, "Customers"))
        self.act_articles.triggered.connect(
            lambda: self._set_active(self.act_articles) or self._show_view(1, "Products")
        )
        self.act_invoices.triggered.connect(
            lambda: self._set_active(self.act_invoices) or self._show_view(2, "Invoices")
        )

        # Activate Home by default
        self._set_active(self.act_home)

    def _create_toolbar(self) -> QToolBar:
        """Créer la barre d'outils avec les actions de navigation."""
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)

        # Unified toolbar on macOS
        if sys.platform == "darwin":
            self.setUnifiedTitleAndToolBarOnMac(True)

        # Dark gray color for all icons
        icon_color = "#444444"

        # Create icons with qtawesome
        home_icon = qta.icon("fa5s.users", color=icon_color)
        articles_icon = qta.icon("fa5s.wine-bottle", color=icon_color)
        invoices_icon = qta.icon("fa5s.file-invoice-dollar", color=icon_color)

        # Create actions
        self.act_home = QAction(home_icon, "Customers", self)
        self.act_home.setCheckable(True)
        self.act_articles = QAction(articles_icon, "Products", self)
        self.act_articles.setCheckable(True)
        self.act_invoices = QAction(invoices_icon, "Invoices", self)
        self.act_invoices.setCheckable(True)

        # Store icons (no need for colored variants)
        self._icon_pairs = {
            self.act_home: (home_icon, home_icon),
            self.act_articles: (articles_icon, articles_icon),
            self.act_invoices: (invoices_icon, invoices_icon),
        }

        # Add actions to toolbar
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
        """Set an action as active and deactivate others."""
        for act in (self.act_home, self.act_articles, self.act_invoices):
            is_active = act is action
            act.setChecked(is_active)

            # Change icon based on active/inactive state
            pair = self._icon_pairs.get(act)
            if pair:
                normal_icon, active_icon = pair
                act.setIcon(active_icon if is_active else normal_icon)

    def _show_view(self, index: int, label: str):
        """Display a specific view in the stack."""
        self.stack.setCurrentIndex(index)
        self.status.setText(label)

    def closeEvent(self, event):
        """Clean up resources before closing the application."""
        # Clean up threads in views
        if hasattr(self, "_customer_view"):
            self._customer_view.cleanup()
        if hasattr(self, "_products_view"):
            # Add cleanup if ProductsView also has a thread
            if hasattr(self._products_view, "cleanup"):
                self._products_view.cleanup()
        super().closeEvent(event)


def main():
    """Main application entry point."""
    # Avoid verbose Qt messages
    os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts=false")

    app = QApplication(sys.argv)

    # Discover available styles
    try:
        from PySide6.QtWidgets import QStyleFactory

        available = list(QStyleFactory.keys())
    except Exception:
        available = []

    # Respect requested style from command line (-style macOS)
    requested_style = None
    for i, a in enumerate(sys.argv):
        if a == "-style" and i + 1 < len(sys.argv):
            requested_style = sys.argv[i + 1]
            break

    # Apply style
    if requested_style:
        if requested_style in available:
            app.setStyle(requested_style)
        else:
            fallback = "macOS" if "macOS" in available else "Fusion"
            if available:
                app.setStyle(fallback)
    else:
        # Default to macOS if available
        if "macOS" in available:
            app.setStyle("macOS")

    # Determine style class
    try:
        style_class = app.style().__class__.__name__
    except Exception:
        style_class = None

    # macOS palette if QCommonStyle
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

    # Load macOS QSS
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
