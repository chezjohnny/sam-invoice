"""Menu bar configuration for the main window."""

from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from sam_invoice.models import database
from sam_invoice.ui.preferences_dialog import PreferencesDialog


def create_menu_bar(window: QMainWindow) -> None:
    """Create and configure the menu bar.

    Args:
        window: The main window to add menus to
    """
    menubar = window.menuBar()

    # File menu
    _create_file_menu(menubar, window)

    # Edit menu
    _create_edit_menu(menubar, window)


def _create_file_menu(menubar, window: QMainWindow) -> None:
    """Create File menu with database operations."""
    file_menu = menubar.addMenu("&File")

    # New database action
    new_action = QAction("&New Database...", window)
    new_action.setShortcut("Ctrl+N")
    new_action.triggered.connect(lambda: _new_database(window))
    file_menu.addAction(new_action)

    # Open database action
    open_action = QAction("&Open Database...", window)
    open_action.setShortcut("Ctrl+O")
    open_action.triggered.connect(lambda: _open_database(window))
    file_menu.addAction(open_action)

    file_menu.addSeparator()

    # Recent files menu
    window.recent_menu = file_menu.addMenu("Open &Recent")
    update_recent_files_menu(window)

    file_menu.addSeparator()

    # Quit action
    quit_action = QAction("&Quit", window)
    quit_action.setShortcut("Ctrl+Q")
    quit_action.triggered.connect(window.close)
    file_menu.addAction(quit_action)


def _create_edit_menu(menubar, window: QMainWindow) -> None:
    """Create Edit menu with preferences."""
    edit_menu = menubar.addMenu("&Edit")

    # Preferences action
    prefs_action = QAction("&Preferences...", window)
    prefs_action.setShortcut("Ctrl+,")
    prefs_action.triggered.connect(lambda: _open_preferences(window))
    edit_menu.addAction(prefs_action)


def _new_database(window: QMainWindow) -> None:
    """Create a new database file."""
    file_path, _ = QFileDialog.getSaveFileName(
        window, "Create New Database", str(Path.home()), "SQLite Database (*.db);;All Files (*)"
    )

    if file_path:
        db_path = Path(file_path)
        # Ensure .db extension
        if not db_path.suffix:
            db_path = db_path.with_suffix(".db")

        # Remove file if it already exists
        if db_path.exists():
            reply = QMessageBox.question(
                window,
                "File Exists",
                f"The file {db_path.name} already exists. Do you want to replace it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.No:
                return

            db_path.unlink()

        # Create new database
        database.set_database_path(db_path)
        database.init_db()

        # Update current database and reload
        window.current_db_path = db_path
        _add_to_recent_files(window, db_path)
        window._update_window_title()
        window._reload_views()


def _open_database(window: QMainWindow) -> None:
    """Open an existing database file."""
    file_path, _ = QFileDialog.getOpenFileName(
        window, "Open Database", str(Path.home()), "SQLite Database (*.db);;All Files (*)"
    )

    if file_path:
        db_path = Path(file_path)
        if db_path.exists():
            database.set_database_path(db_path)
            window.current_db_path = db_path
            _add_to_recent_files(window, db_path)
            window._update_window_title()
            window._reload_views()


def _open_recent_database(window: QMainWindow, db_path: Path) -> None:
    """Open a database from recent files list."""
    if db_path.exists():
        database.set_database_path(db_path)
        window.current_db_path = db_path
        _add_to_recent_files(window, db_path)
        window._update_window_title()
        window._reload_views()
    else:
        QMessageBox.warning(window, "File Not Found", f"The database file {db_path} no longer exists.")
        _remove_from_recent_files(window, db_path)
        update_recent_files_menu(window)


def _add_to_recent_files(window: QMainWindow, db_path: Path) -> None:
    """Add a database to recent files list (max 5)."""
    recent = window.settings.value("recent_files", [])
    if not isinstance(recent, list):
        recent = []

    # Remove if already exists
    recent = [str(p) for p in recent if str(p) != str(db_path)]
    # Add to front
    recent.insert(0, str(db_path))
    # Keep only 5 most recent
    recent = recent[:5]

    window.settings.setValue("recent_files", recent)
    window.settings.setValue("last_database", str(db_path))
    update_recent_files_menu(window)


def _remove_from_recent_files(window: QMainWindow, db_path: Path) -> None:
    """Remove a database from recent files list."""
    recent = window.settings.value("recent_files", [])
    if not isinstance(recent, list):
        recent = []

    recent = [str(p) for p in recent if str(p) != str(db_path)]
    window.settings.setValue("recent_files", recent)


def _open_preferences(window: QMainWindow) -> None:
    """Open the preferences dialog."""
    dialog = PreferencesDialog(window)
    dialog.exec()


def update_recent_files_menu(window: QMainWindow) -> None:
    """Update the recent files submenu."""
    window.recent_menu.clear()

    recent = window.settings.value("recent_files", [])
    if not isinstance(recent, list):
        recent = []

    if not recent:
        no_recent = QAction("No Recent Files", window)
        no_recent.setEnabled(False)
        window.recent_menu.addAction(no_recent)
        return

    for file_path in recent:
        db_path = Path(file_path)
        action = QAction(db_path.name, window)
        action.setToolTip(str(db_path))
        action.triggered.connect(lambda checked=False, p=db_path: _open_recent_database(window, p))
        window.recent_menu.addAction(action)
