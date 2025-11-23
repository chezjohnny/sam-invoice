"""Application style and theme management."""

import platform
import sys
from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory


def setup_application_style(app: QApplication) -> None:
    """Configure application style and theme.

    Args:
        app: The QApplication instance to configure
    """
    # Discover available styles
    available = list(QStyleFactory.keys())

    # Respect requested style from command line (-style macOS)
    requested_style = _get_requested_style()

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
    style_class = app.style().__class__.__name__ if app.style() else None

    # Apply macOS palette if using QCommonStyle
    if requested_style and requested_style.lower().startswith("mac") and style_class == "QCommonStyle":
        _apply_macos_palette(app)

    # Load and apply stylesheet
    _load_stylesheet(app, requested_style, style_class)


def _get_requested_style() -> str | None:
    """Extract requested style from command line arguments."""
    for i, arg in enumerate(sys.argv):
        if arg == "-style" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def _apply_macos_palette(app: QApplication) -> None:
    """Apply macOS-like color palette to the application."""
    mac_pal = QPalette()
    mac_pal.setColor(QPalette.ColorRole.Window, QColor("#ececec"))
    mac_pal.setColor(QPalette.ColorRole.Button, QColor("#ececec"))
    mac_pal.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    mac_pal.setColor(QPalette.ColorRole.Text, QColor("#000000"))
    mac_pal.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))
    mac_pal.setColor(QPalette.ColorRole.Highlight, QColor("#a5cdff"))
    app.setPalette(mac_pal)


def _load_stylesheet(app: QApplication, requested_style: str | None, style_class: str | None) -> None:
    """Load and apply QSS stylesheet if appropriate.

    Args:
        app: The QApplication instance
        requested_style: Style requested via command line
        style_class: Current style class name
    """
    try:
        qss_path = _find_stylesheet_path()

        # Apply macOS style if on macOS platform or if explicitly requested
        should_apply = (
            platform.system() == "Darwin"  # Always on macOS
            or (requested_style and requested_style.lower().startswith("mac"))
            or style_class == "QCommonStyle"
        )

        if qss_path and qss_path.exists() and should_apply:
            with qss_path.open("r", encoding="utf-8") as f:
                qss = f.read()
            if qss:
                app.setStyleSheet(qss)
    except Exception as e:
        print(f"Warning: Could not load stylesheet: {e}")


def _find_stylesheet_path() -> Path | None:
    """Find the path to the macos.qss stylesheet.

    Returns:
        Path to stylesheet if found, None otherwise
    """
    # Determine base path for bundled app vs development
    if getattr(sys, "frozen", False):
        # Running in a PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in normal Python environment
        base_path = Path(__file__).parent

    # Try bundled path first
    qss_path = base_path / "sam_invoice" / "assets" / "styles" / "macos.qss"
    if qss_path.exists():
        return qss_path

    # Try development path
    qss_path = base_path / "assets" / "styles" / "macos.qss"
    if qss_path.exists():
        return qss_path

    return None
