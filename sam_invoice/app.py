import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QSize, QStringListModel, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QStyle,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

import sam_invoice.models.crud_customer as crud
from sam_invoice.ui.customer_detail import CustomerDetailWidget
from sam_invoice.ui.customers_view import CustomersView


class SearchWorker(QObject):
    """Worker that runs database searches in a background thread."""

    results_ready = Signal(object)
    error = Signal(str)

    @Slot(str, int)
    def search(self, q: str, limit: int):
        try:
            rows = crud.search_customers(q, limit=limit)
            # ensure alphabetical order by name as a safeguard
            rows = sorted(rows, key=lambda c: (getattr(c, "name", "") or "").lower())
            self.results_ready.emit(rows)
        except Exception as e:
            self.error.emit(str(e))
            try:
                self.results_ready.emit([])
            except Exception:
                pass


class MainWindow(QMainWindow):
    # signal used to request a background search (emitted from the UI thread)
    search_requested = Signal(str, int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sam Invoice")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        header = QLabel("Sam Invoice — Main")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size:18pt; font-weight:600; padding:8px;")
        main_layout.addWidget(header)

        # Tool bar with Home / Customers / Invoices actions
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        # On macOS, prefer a unified title bar and toolbar like native apps
        if sys.platform == "darwin":
            try:
                # QMainWindow provides setUnifiedTitleAndToolBarOnMac
                self.setUnifiedTitleAndToolBarOnMac(True)
            except Exception:
                pass
        # try to load bundled SVG icons (located inside the package),
        # fallback to standard icons if missing
        base = Path(__file__).parent / "assets" / "icons"
        if not base.exists():
            # helpful debug when running locally or in CI
            print(f"[sam_invoice] icons folder not found: {base}")

        def load_icon(name: str, fallback: QStyle.StandardPixmap):
            p = (base / f"{name}.svg").resolve()
            if p.exists():
                return QIcon(str(p))
            return self.style().standardIcon(fallback)

        home_icon = load_icon("home", QStyle.SP_DirHomeIcon)
        customers_icon = load_icon("customers", QStyle.SP_DirIcon)
        invoices_icon = load_icon("invoices", QStyle.SP_FileIcon)

        # actions (checkable so we can show active state)
        self.act_home = QAction(home_icon, "Home", self)
        self.act_home.setCheckable(True)
        self.act_customers = QAction(customers_icon, "Customers", self)
        self.act_customers.setCheckable(True)
        self.act_invoices = QAction(invoices_icon, "Invoices", self)
        self.act_invoices.setCheckable(True)

        # prepare active (colored) variants of the icons (light blue)
        def colorize_icon(icon: QIcon, color: QColor, size: QSize | None = None) -> QIcon:
            if size is None:
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

        active_color = QColor("#3b82f6")  # light blue
        home_icon_active = colorize_icon(home_icon, active_color)
        customers_icon_active = colorize_icon(customers_icon, active_color)
        invoices_icon_active = colorize_icon(invoices_icon, active_color)

        # store normal/active pairs for switching
        self._icon_pairs = {
            self.act_home: (home_icon, home_icon_active),
            self.act_customers: (customers_icon, customers_icon_active),
            self.act_invoices: (invoices_icon, invoices_icon_active),
        }

        # show text under icons for clarity
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.addAction(self.act_home)
        toolbar.addAction(self.act_customers)
        toolbar.addAction(self.act_invoices)

        # add toolbar to the main window (appears above central widget)
        self.addToolBar(toolbar)

        # Stacked area for views
        self.stack = QStackedWidget()
        # Home page placeholder
        home_widget = QWidget()
        home_layout = QVBoxLayout(home_widget)

        # Search autocomplete for customers
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Rechercher un client (nom, email)...")
        # model for completer
        self._completer_model = QStringListModel()
        self._completer = QCompleter(self._completer_model, self)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self.search_box.setCompleter(self._completer)

        # mapping display -> id
        self._customer_map = {}

        # timer used to debounce live DB searches while typing
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)  # ms
        self._search_timer.timeout.connect(self._perform_live_search)

        # connect live search on text change (debounced)
        self.search_box.textChanged.connect(self._on_search_text_changed)

        # Setup background search worker/thread to avoid blocking UI
        self._search_thread = QThread(self)
        self._search_worker = SearchWorker()
        self._search_worker.moveToThread(self._search_thread)
        # connect signal from worker to handler
        self._search_worker.results_ready.connect(self._on_search_results)
        self._search_worker.error.connect(lambda e: print(f"[sam_invoice] search worker error: {e}"))
        # wire the MainWindow.search_requested signal to the worker.search slot
        self.search_requested.connect(self._search_worker.search)
        self._search_thread.start()

        # create results list (left column) and detail (right column)
        self._results_list = QListWidget()
        self._results_list.setSelectionMode(QListWidget.SingleSelection)

        # placeholder where selected customer detail will be shown
        self._home_detail = CustomerDetailWidget()

        # two-column layout for home: left = search + results, right = detail
        content_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.search_box)
        left_layout.addWidget(self._results_list)
        content_layout.addLayout(left_layout, 1)
        content_layout.addWidget(self._home_detail, 2)
        # add the two-column content to the home layout
        home_layout.addLayout(content_layout)
        # current customer shown in home detail
        self._current_home_customer = None
        # listen to inline-save from home detail widget
        # Prefer Qt Signal, fall back to plain callback registration if needed.
        if hasattr(self._home_detail, "customer_saved"):
            try:
                self._home_detail.customer_saved.connect(self._on_home_saved)
            except Exception:
                # ignore and try fallback
                pass
        if hasattr(self._home_detail, "register_saved_callback"):
            try:
                self._home_detail.register_saved_callback(self._on_home_saved)
            except Exception:
                pass

        # When the detail widget enters edit mode, disable the search prompt.
        if hasattr(self._home_detail, "editing_changed"):
            try:
                self._home_detail.editing_changed.connect(lambda editing: self.search_box.setEnabled(not editing))
            except Exception:
                pass
        if hasattr(self._home_detail, "register_editing_callback"):
            try:
                self._home_detail.register_editing_callback(lambda editing: self.search_box.setEnabled(not editing))
            except Exception:
                pass

        # customers view (embedded)
        self.customers_view = CustomersView(parent=self)

        # invoices placeholder
        invoices_placeholder = QWidget()
        ph_layout = QVBoxLayout(invoices_placeholder)
        ph_label = QLabel("Invoices view (coming soon)")
        ph_label.setAlignment(Qt.AlignCenter)
        ph_layout.addWidget(ph_label)

        # add pages to the stack: home, customers, invoices
        self.stack.addWidget(home_widget)
        self.stack.addWidget(self.customers_view)
        self.stack.addWidget(invoices_placeholder)

        main_layout.addWidget(self.stack)

        # status label
        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status)

        # Display the currently applied Qt style for quick visual confirmation
        try:
            style_name = QApplication.instance().style().objectName()
        except Exception:
            style_name = "unknown"
        self.status.setText(f"Style: {style_name}")

        self.setCentralWidget(central_widget)

        # Connect toolbar actions and maintain single-active behavior
        self.act_home.triggered.connect(lambda: self._set_active(self.act_home) or self.on_home_clicked())
        self.act_customers.triggered.connect(
            lambda: self._set_active(self.act_customers) or self.on_customers_clicked()
        )
        self.act_invoices.triggered.connect(lambda: self._set_active(self.act_invoices) or self.on_invoices_clicked())
        # default active is Home
        self._set_active(self.act_home)

        # prepare completer signal and list selection
        self._completer.activated.connect(self._on_completer_activated)
        self._results_list.itemActivated.connect(lambda it: self._on_result_item_activated(it))
        self._results_list.itemClicked.connect(lambda it: self._on_result_item_activated(it))
        # load customers initially
        self._reload_customer_autocomplete()

    def _reload_customer_autocomplete(self):
        """Load customer suggestions into the completer."""
        try:
            customers = list(crud.get_customers())
        except Exception:
            customers = []
        # Ensure alphabetical order by name (case-insensitive) for the UI list
        try:
            customers = sorted(customers, key=lambda c: (getattr(c, "name", "") or "").lower())
        except Exception:
            pass
        display = []
        self._customer_map.clear()
        for c in customers:
            # display like: "Name <email> [id]" to make unique
            disp = f"{getattr(c, 'name', '')} <{getattr(c, 'email', '')}> [{getattr(c, 'id', '')}]"
            display.append(disp)
            self._customer_map[disp] = getattr(c, "id", None)
        self._completer_model.setStringList(display)
        # also populate the left-hand results list
        try:
            self._results_list.clear()
            for disp in display:
                self._results_list.addItem(disp)
        except Exception:
            # if results list doesn't exist (older layout), ignore
            pass

    def _on_search_text_changed(self, text: str) -> None:
        """Restart debounce timer when the user types in the main search box.

        If the text is empty we immediately reload the full autocomplete list.
        """
        if not text or not text.strip():
            # empty -> use full list immediately
            self._reload_customer_autocomplete()
            # ensure any pending timer is stopped
            try:
                self._search_timer.stop()
            except Exception:
                pass
            return
        # restart debounce timer
        try:
            self._search_timer.start()
        except Exception:
            # if timer failed for some reason, run search synchronously
            self._perform_live_search()

    def _perform_live_search(self) -> None:
        """Perform a DB-backed search and update completer + results list."""
        q = (self.search_box.text() or "").strip()
        if not q:
            self._reload_customer_autocomplete()
            return
        # request the background worker to perform the search (limit 100)
        try:
            self.search_requested.emit(q, 100)
        except Exception:
            # fallback to synchronous search if emitting fails
            try:
                rows = crud.search_customers(q, limit=100)
                rows = sorted(rows, key=lambda c: (getattr(c, "name", "") or "").lower())
            except Exception:
                rows = []
            self._on_search_results(rows)

    def _on_search_results(self, rows: list) -> None:
        """Handle search results emitted by the background worker and update UI."""
        display = []
        self._customer_map.clear()
        for c in rows:
            disp = f"{getattr(c, 'name', '')} <{getattr(c, 'email', '')}> [{getattr(c, 'id', '')}]"
            display.append(disp)
            self._customer_map[disp] = getattr(c, "id", None)

        try:
            self._completer_model.setStringList(display)
        except Exception:
            pass
        try:
            self._results_list.clear()
            for disp in display:
                self._results_list.addItem(disp)
        except Exception:
            pass

    def _on_completer_activated(self, text: str):
        cid = self._customer_map.get(text)
        if cid is None:
            return
        try:
            cust = crud.get_customer_by_id(int(cid))
        except Exception:
            cust = None
        self._home_detail.set_customer(cust)
        self._current_home_customer = cust
        # also switch to home page to ensure detail visible
        self.stack.setCurrentIndex(0)

    def _on_result_item_activated(self, item):
        # item can be QListWidgetItem or text
        try:
            text = item.text() if hasattr(item, "text") else str(item)
        except Exception:
            text = str(item)
        cid = self._customer_map.get(text)
        if cid is None:
            return
        try:
            cust = crud.get_customer_by_id(int(cid))
        except Exception:
            cust = None
        self._home_detail.set_customer(cust)
        self._current_home_customer = cust
        self.stack.setCurrentIndex(0)

    def closeEvent(self, event):
        """Ensure worker thread is stopped cleanly when the window closes."""
        try:
            if hasattr(self, "_search_thread") and self._search_thread.isRunning():
                self._search_thread.quit()
                self._search_thread.wait(1000)
        except Exception:
            pass
        super().closeEvent(event)

    def _on_home_saved(self, data: dict):
        """Handle inline-saved customer data from the detail widget."""
        if not data:
            return
        cid = data.get("id")
        if cid is None:
            return
        try:
            crud.update_customer(int(cid), name=data.get("name"), address=data.get("address"), email=data.get("email"))
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Failed to update customer: {e}")
            return
        # refresh views and autocomplete
        try:
            self.customers_view.refresh()
        except Exception:
            pass
        self._reload_customer_autocomplete()
        # reload current customer and update detail
        try:
            cust = crud.get_customer_by_id(int(cid))
        except Exception:
            cust = None
        self._current_home_customer = cust
        self._home_detail.set_customer(cust)

    def _set_active(self, action: QAction) -> None:
        """Set the given action as active (checked) and uncheck others."""
        for act in (self.act_home, self.act_customers, self.act_invoices):
            is_active = act is action
            act.setChecked(is_active)
            # swap icon to active/normal variant if available
            pair = self._icon_pairs.get(act)
            if pair:
                normal_icon, active_icon = pair
                act.setIcon(active_icon if is_active else normal_icon)

    @Slot()
    def on_customers_clicked(self):
        # Placeholder action — will be connected to actual view later
        # switch to customers view in the stacked widget (index 1)
        self.stack.setCurrentIndex(1)
        self.status.setText("Showing Customers")

    @Slot()
    def on_invoices_clicked(self):
        # switch to invoices placeholder view (index 2)
        self.stack.setCurrentIndex(2)
        self.status.setText("Showing Invoices")

    @Slot()
    def on_home_clicked(self):
        # switch to home page (index 0)
        self.stack.setCurrentIndex(0)
        self.status.setText("Home")


def main():
    # Avoid noisy Qt font-alias population messages by default; allow override via env var.
    os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts=false")

    app = QApplication(sys.argv)

    # Try to discover available styles for better debug/fallback logic.
    try:
        from PySide6.QtWidgets import QStyleFactory

        available = list(QStyleFactory.keys())
    except Exception:
        available = []

    # Respect CLI `-style` if provided (for example: `-style macOS`).
    requested_style = None
    for i, a in enumerate(sys.argv):
        if a == "-style" and i + 1 < len(sys.argv):
            requested_style = sys.argv[i + 1]
            break

    # If a style was explicitly requested, honor it when available,
    # otherwise fallback to 'macOS' if present, then 'Fusion'.
    if requested_style:
        if requested_style in available:
            app.setStyle(requested_style)
        else:
            fallback = "macOS" if "macOS" in available else "Fusion"
            if available:
                app.setStyle(fallback)
    else:
        # Default to macOS when available to match macOS Contacts look.
        if "macOS" in available:
            app.setStyle("macOS")
        else:
            pass

    # Determine the style class for potential fallback behavior.
    try:
        style_class = app.style().__class__.__name__
    except Exception:
        style_class = None

    # If the user requested 'macOS' but Qt fell back to QCommonStyle,
    # apply a gentle macOS-like palette so the app looks more native.
    try:
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
    except Exception:
        pass

    # Load a macOS-like QSS when requested or when we applied the macOS palette.
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
    window = MainWindow()
    # Start maximized to give a larger initial workspace
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
