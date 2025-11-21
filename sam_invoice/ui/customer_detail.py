from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class ClickableLabel(QLabel):
    """A QLabel that emits a signal on double-click for in-place editing."""

    double_clicked = Signal()

    def mouseDoubleClickEvent(self, event):
        try:
            self.double_clicked.emit()
        finally:
            super().mouseDoubleClickEvent(event)


class CustomerDetailWidget(QWidget):
    """Improved detail widget with large avatar and prominent name.

    Supports inline editing and emits `customer_saved` with a dict when saved.
    """

    customer_saved = Signal(object)
    editing_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_id = None

        # Large avatar/icon on the left
        self._avatar = QLabel()
        self._avatar.setFixedSize(96, 96)
        self._avatar.setAlignment(Qt.AlignCenter)

        # Name with larger font (label + editor)
        self._name = ClickableLabel("")
        name_font = QFont()
        name_font.setPointSize(16)
        name_font.setBold(True)
        self._name.setFont(name_font)
        self._name_edit = QLineEdit()
        self._name_edit.setVisible(False)

        # Secondary details (label + editor)
        self._address = ClickableLabel("")
        self._email = ClickableLabel("")
        self._address.setWordWrap(True)
        self._email.setWordWrap(True)
        self._address.setStyleSheet("color: #444444;")
        self._email.setStyleSheet("color: #444444;")

        self._address_edit = QLineEdit()
        self._address_edit.setVisible(False)
        self._email_edit = QLineEdit()
        self._email_edit.setVisible(False)

        # use a horizontal header area for avatar + name/details
        header_layout = QHBoxLayout()
        header_left = QVBoxLayout()
        header_left.addWidget(self._avatar, alignment=Qt.AlignLeft)
        header_layout.addLayout(header_left)

        header_right = QVBoxLayout()
        header_right.addWidget(self._name)
        header_right.addWidget(self._name_edit)
        header_right.addWidget(self._email)
        header_right.addWidget(self._email_edit)
        header_layout.addLayout(header_right)

        # small action row (Edit -> Save / Cancel)
        self._edit_btn = QPushButton("Edit")
        self._save_btn = QPushButton("Save")
        self._cancel_btn = QPushButton("Cancel")
        self._save_btn.setVisible(False)
        self._cancel_btn.setVisible(False)
        self._edit_btn.setEnabled(False)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        actions_layout.addWidget(self._edit_btn)
        actions_layout.addWidget(self._save_btn)
        actions_layout.addWidget(self._cancel_btn)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self._address)
        main_layout.addWidget(self._address_edit)
        main_layout.addStretch()
        main_layout.addLayout(actions_layout)

        # try to prepare an avatar icon from package assets
        icons_dir = Path(__file__).parent.parent / "assets" / "icons"
        avatar_path = icons_dir / "customers.svg"
        if avatar_path.exists():
            icon = QIcon(str(avatar_path))
            pix = icon.pixmap(QSize(96, 96))
            if not pix.isNull():
                self._avatar.setPixmap(pix)

        # animation effect
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)

        # connections
        self._edit_btn.clicked.connect(lambda: self._enter_edit_mode(True))
        self._cancel_btn.clicked.connect(lambda: self._enter_edit_mode(False))
        self._save_btn.clicked.connect(self._save_changes)

        # enable in-place editing by double-clicking labels
        try:
            self._name.double_clicked.connect(lambda: self._enter_edit_mode(True))
            self._address.double_clicked.connect(lambda: self._enter_edit_mode(True))
            self._email.double_clicked.connect(lambda: self._enter_edit_mode(True))
        except Exception:
            pass

        # hide the Edit button when using in-place editing
        self._edit_btn.setVisible(False)

        # fallback callback (in case Signals are not available or fail)
        self._saved_callback = None
        # fallback for editing state changes
        self._editing_callback = None

    def register_saved_callback(self, cb):
        """Register a plain-Python callback as fallback for saved events.

        The callback will be called with a single argument: the data dict.
        """
        self._saved_callback = cb

    def register_editing_callback(self, cb):
        """Register a plain-Python callback as fallback when editing starts/stops.

        The callback will be called with a single bool argument: True when entering
        edit mode, False when leaving it.
        """
        self._editing_callback = cb

    def _animate(self, start: float, end: float, duration: int = 220):
        anim = QPropertyAnimation(self._effect, b"opacity", self)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()

    def _enter_edit_mode(self, editing: bool):
        # notify listeners about editing state change (Signal preferred)
        try:
            self.editing_changed.emit(editing)
        except Exception:
            if self._editing_callback:
                try:
                    self._editing_callback(editing)
                except Exception:
                    pass

        # animate fade out -> toggle -> fade in
        self._animate(1.0, 0.0, duration=120)
        # toggle widgets after a short delay (animation still running but quick)
        self._name.setVisible(not editing)
        self._name_edit.setVisible(editing)
        self._email.setVisible(not editing)
        self._email_edit.setVisible(editing)
        self._address.setVisible(not editing)
        self._address_edit.setVisible(editing)
        self._edit_btn.setVisible(not editing)
        self._save_btn.setVisible(editing)
        self._cancel_btn.setVisible(editing)
        # populate editors with current text when entering
        if editing:
            self._name_edit.setText(self._name.text())
            self._email_edit.setText(self._email.text())
            self._address_edit.setText(self._address.text())
        self._animate(0.0, 1.0, duration=220)

    def _save_changes(self):
        # build data and emit
        data = {
            "id": self._current_id,
            "name": self._name_edit.text().strip(),
            "address": self._address_edit.text().strip(),
            "email": self._email_edit.text().strip(),
        }
        # emit PySide signal if available
        try:
            self.customer_saved.emit(data)
        except Exception:
            # fallback to plain callback if provided
            if self._saved_callback:
                try:
                    self._saved_callback(data)
                except Exception:
                    pass
        self._enter_edit_mode(False)

    def set_customer(self, cust):
        self._current_id = getattr(cust, "id", None) if cust else None
        if not cust:
            self._name.setText("")
            self._address.setText("")
            self._email.setText("")
            self._edit_btn.setEnabled(False)
            return
        self._name.setText(getattr(cust, "name", ""))
        self._address.setText(getattr(cust, "address", ""))
        self._email.setText(getattr(cust, "email", ""))
        self._edit_btn.setEnabled(True)

    def edit_button(self):
        return self._edit_btn
