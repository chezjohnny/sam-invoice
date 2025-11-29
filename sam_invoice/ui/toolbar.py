"""Toolbar configuration for the main window."""

import sys

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QToolBar


def create_toolbar(window: QMainWindow) -> QToolBar:
    """Create and configure the main toolbar.

    Args:
        window: The main window to add toolbar to

    Returns:
        Configured QToolBar instance
    """
    toolbar = QToolBar("Main")
    toolbar.setObjectName("MainToolbar")  # Set objectName for state saving
    toolbar.setMovable(False)

    # Unified toolbar on macOS
    if sys.platform == "darwin":
        window.setUnifiedTitleAndToolBarOnMac(True)

    # Dark gray color for all icons
    icon_color = "#444444"

    # Create icons with qtawesome
    home_icon = qta.icon("fa5s.users", color=icon_color)
    products_icon = qta.icon("fa5s.wine-bottle", color=icon_color)
    invoices_icon = qta.icon("fa5s.file-invoice-dollar", color=icon_color)

    # Create actions
    window.act_home = QAction(home_icon, "Customers", window)
    window.act_home.setCheckable(True)
    window.act_products = QAction(products_icon, "Products", window)
    window.act_products.setCheckable(True)
    window.act_invoices = QAction(invoices_icon, "Invoices", window)
    window.act_invoices.setCheckable(True)

    # Store icons (no need for colored variants)
    window._icon_pairs = {
        window.act_home: (home_icon, home_icon),
        window.act_products: (products_icon, products_icon),
        window.act_invoices: (invoices_icon, invoices_icon),
    }

    # Add actions to toolbar
    toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    toolbar.addAction(window.act_home)
    toolbar.addAction(window.act_products)
    toolbar.addAction(window.act_invoices)

    return toolbar


def set_active_toolbar_action(window: QMainWindow, action: QAction) -> None:
    """Set a toolbar action as active and deactivate others.

    Args:
        window: The main window
        action: The action to set as active
    """
    for act in (window.act_home, window.act_products, window.act_invoices):
        is_active = act is action
        act.setChecked(is_active)

        # Change icon based on active/inactive state
        pair = window._icon_pairs.get(act)
        if pair:
            normal_icon, active_icon = pair
            act.setIcon(active_icon if is_active else normal_icon)
