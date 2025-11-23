"""Sam Invoice main application."""

import os
import signal
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from sam_invoice.models import database
from sam_invoice.style_manager import setup_application_style
from sam_invoice.ui.customer_view import CustomerView
from sam_invoice.ui.menu_bar import create_menu_bar
from sam_invoice.ui.products_view import ProductsView
from sam_invoice.ui.toolbar import create_toolbar, set_active_toolbar_action
from sam_invoice.ui.widget_helpers import create_placeholder


class MainWindow(QMainWindow):
    """Sam Invoice application main window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sam Invoice")

        # Initialize settings
        self.settings = QSettings("SamInvoice", "SamInvoice")

        # Load last opened database or use default
        last_db = self.settings.value("last_database", None)
        if last_db and Path(last_db).exists():
            self.current_db_path = Path(last_db)
            database.set_database_path(self.current_db_path)
        else:
            self.current_db_path = database.DEFAULT_DB_PATH

        self._update_window_title()

        # === Menu Bar ===
        create_menu_bar(self)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # === Toolbar ===
        toolbar = create_toolbar(self)
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
        invoices_placeholder = create_placeholder("Invoices (coming soon)")
        self.stack.addWidget(invoices_placeholder)

        main_layout.addWidget(self.stack)

        self.setCentralWidget(central_widget)

        # === Toolbar action connections ===
        self.act_home.triggered.connect(lambda: set_active_toolbar_action(self, self.act_home) or self._show_view(0))
        self.act_articles.triggered.connect(
            lambda: set_active_toolbar_action(self, self.act_articles) or self._show_view(1)
        )
        self.act_invoices.triggered.connect(
            lambda: set_active_toolbar_action(self, self.act_invoices) or self._show_view(2)
        )

        # Activate Home by default
        set_active_toolbar_action(self, self.act_home)

        # Restore window geometry and state
        self._restore_window_state()

    def _show_view(self, index: int):
        """Display a specific view in the stack."""
        self.stack.setCurrentIndex(index)

    def _update_window_title(self):
        """Update window title with current database name."""
        db_name = self.current_db_path.name
        self.setWindowTitle(f"Sam Invoice - {db_name}")

    def _reload_views(self):
        """Reload all views with new database."""
        # Reload customers view
        if hasattr(self._customer_view, "reload_items"):
            self._customer_view.reload_items()

        # Reload products view
        if hasattr(self._products_view, "reload_items"):
            self._products_view.reload_items()

    def _restore_window_state(self):
        """Restore window geometry and state from settings."""
        # Restore window geometry first
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size if no saved geometry
            self.resize(1200, 800)

        # Restore window state (toolbars, dockwidgets, etc.)
        window_state = self.settings.value("window/state")
        if window_state:
            self.restoreState(window_state)

        # Check if was in fullscreen
        was_fullscreen = self.settings.value("window/fullscreen", False, type=bool)
        if was_fullscreen:
            self.showFullScreen()
        else:
            # Check if was maximized (only if not fullscreen)
            was_maximized = self.settings.value("window/maximized", False, type=bool)
            if was_maximized:
                self.showMaximized()

        # Restore splitter sizes for customer view
        customer_splitter_state = self.settings.value("splitters/customer_view")
        if customer_splitter_state and hasattr(self._customer_view, "_splitter"):
            self._customer_view._splitter.restoreState(customer_splitter_state)

        # Restore splitter sizes for products view
        products_splitter_state = self.settings.value("splitters/products_view")
        if products_splitter_state and hasattr(self._products_view, "_splitter"):
            self._products_view._splitter.restoreState(products_splitter_state)

    def _save_window_state(self):
        """Save window geometry and state to settings."""
        # Save window geometry
        self.settings.setValue("window/geometry", self.saveGeometry())

        # Save window state
        self.settings.setValue("window/state", self.saveState())

        # Save if window is fullscreen
        self.settings.setValue("window/fullscreen", self.isFullScreen())

        # Save if window is maximized (only relevant if not fullscreen)
        self.settings.setValue("window/maximized", self.isMaximized())

        # Save splitter states
        if hasattr(self._customer_view, "_splitter"):
            self.settings.setValue("splitters/customer_view", self._customer_view._splitter.saveState())

        if hasattr(self._products_view, "_splitter"):
            self.settings.setValue("splitters/products_view", self._products_view._splitter.saveState())

    def closeEvent(self, event):
        """Clean up resources before closing the application."""
        # Save window state
        self._save_window_state()

        # Clean up threads in views
        if hasattr(self, "_customer_view"):
            self._customer_view.cleanup()
        if hasattr(self, "_products_view") and hasattr(self._products_view, "cleanup"):
            self._products_view.cleanup()
        super().closeEvent(event)


def main():
    """Main application entry point."""
    # Avoid verbose Qt messages
    os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts=false")

    # On macOS, set the process name before creating QApplication
    if sys.platform == "darwin":
        _set_macos_process_name()

    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Sam Invoice")
    app.setApplicationDisplayName("Sam Invoice")
    app.setOrganizationName("SamInvoice")
    app.setOrganizationDomain("sam-invoice.app")

    # Configure style and theme
    setup_application_style(app)

    # Create the window
    window = MainWindow()
    window.show()

    # Configure signal handling for clean shutdown
    _setup_signal_handlers(app)

    sys.exit(app.exec())


def _set_macos_process_name() -> None:
    """Set process name on macOS for proper app name in menu bar."""
    try:
        from Foundation import NSProcessInfo

        processInfo = NSProcessInfo.processInfo()
        processInfo.setProcessName_("Sam Invoice")
    except ImportError:
        # Foundation not available, try setting argv[0]
        if len(sys.argv) > 0:
            sys.argv[0] = "Sam Invoice"


def _setup_signal_handlers(app: QApplication) -> None:
    """Configure Ctrl-C handling for clean shutdown."""

    def sigint_handler(signum, frame):
        """Handler for Ctrl-C to cleanly close the application."""
        print("\nClosing application...")
        QApplication.quit()

    signal.signal(signal.SIGINT, sigint_handler)

    # Timer to allow Python to process signals during Qt event loop
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Just to wake up the event loop
    timer.start(500)  # Every 500ms


if __name__ == "__main__":
    main()
