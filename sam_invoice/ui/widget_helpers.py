"""Helper widgets and utilities for UI components."""

import qtawesome as qta
from PySide6.QtCore import QObject, QSize, Qt, Signal, Slot
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ClickableLabel(QLabel):
    """Label that emits a signal on double-click."""

    double_clicked = Signal()

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


class SearchWorker(QObject):
    """Worker that executes searches in a separate thread."""

    results_ready = Signal(object)
    error = Signal(str)

    def __init__(self, search_func):
        """Initialize the worker with a search function.

        Args:
            search_func: Callable function(query: str, limit: int) -> list
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


def create_icon_button(icon_name: str, tooltip: str, color: str = "#444444") -> QPushButton:
    """Create a standard icon-only button.

    Args:
        icon_name: Font Awesome icon name (e.g., "fa5s.edit")
        tooltip: Button tooltip text
        color: Icon color (default: "#444444")

    Returns:
        QPushButton configured with icon and fixed size
    """
    btn = QPushButton()
    btn.setIcon(qta.icon(icon_name, color=color))
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(32, 32)
    btn.setToolTip(tooltip)
    return btn


def create_placeholder(text: str) -> QWidget:
    """Create a placeholder widget with centered text.

    Args:
        text: Text to display in the center

    Returns:
        QWidget with centered label
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    return widget
