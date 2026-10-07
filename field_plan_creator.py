"""
QGIS Plugin Template - Main Plugin Class

This module contains the main plugin class that manages the QGIS interface
integration, menu items, toolbar buttons, and dockable panels.
"""

import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolBar, QMessageBox

class FieldPlanCreator:
    """Plugin Template implementation class for QGIS."""

    def __init__(self, iface):
        """Constructor.

        Args:
            iface: An interface instance that provides the hook to QGIS.
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.toolbar = None

        # Dock widgets (lazy loaded)
        self._dock = None
        self._settings_dock = None

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_toolbar=True,
        status_tip=None,
        checkable=False,
        parent=None,
    ):
        """Add a toolbar icon to the toolbar.

        Args:
            icon_path: Path to the icon for this action.
            text: Text that appears in the menu for this action.
            callback: Function to be called when the action is triggered.
            enabled_flag: A flag indicating if the action should be enabled.
            add_to_menu: Flag indicating whether action should be added to menu.
            add_to_toolbar: Flag indicating whether action should be added to toolbar.
            status_tip: Optional text to show in status bar when mouse hovers over action.
            checkable: Whether the action is checkable (toggle).
            parent: Parent widget for the new action.

        Returns:
            The action that was created.
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(checkable)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Create toolbar
        self.toolbar = QToolBar("Plugin Template Toolbar")
        self.toolbar.setObjectName("PluginTemplateToolbar")
        self.iface.addToolBar(self.toolbar)

        # Get icon paths
        icon_base = os.path.join(self.plugin_dir, "icons")
        self.icon_base = icon_base

        # Main panel icon - use custom icon or fallback to QGIS default
        main_icon = os.path.join(icon_base, "icon.png")
        if not os.path.exists(main_icon):
            main_icon = ":/images/themes/default/mActionAddRasterLayer.svg"

        # Add Sample Panel action (checkable for dock toggle)
        self.action = self.add_action(
            main_icon,
            "Field plan creator",
            self.toggle_dock,
            status_tip="Toggle field plan creator",
            checkable=True,
            parent=self.iface.mainWindow(),
        )

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        # Remove dock widgets
        if self._dock:
            self.iface.removeDockWidget(self._dock)
            self._dock.deleteLater()
            self._dock = None

        # Remove actions from menu
        for action in self.actions:
            self.iface.removePluginMenu("&Plugin Template", action)

        # Remove toolbar
        if self.toolbar:
            del self.toolbar

    def toggle_dock(self):
        """Toggle the Sample dock widget visibility."""
        if self._dock is None:
            try:
                from .dialogs.fpc_dock import FPCDockWidget

                self._dock = FPCDockWidget(
                    self.iface, 
                    self.iface.mainWindow(),
                    self.icon_base
                )
                self._dock.setObjectName("FieldPlanCreatorFPCDockWidget")
                self._dock.visibilityChanged.connect(
                    self._on_sample_visibility_changed
                )
                self.iface.addDockWidget(
                    Qt.DockWidgetArea.RightDockWidgetArea, self._dock
                )
                self._dock.show()
                self._dock.raise_()
                return

            except Exception as e:
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    "Error",
                    f"Failed to create field plan creator panel:\n{str(e)}",
                )
                self.action.setChecked(False)
                return

        # Toggle visibility
        if self._dock.isVisible():
            self._dock.hide()
        else:
            self._dock.show()
            self._dock.raise_()

    def _on_sample_visibility_changed(self, visible):
        """Handle Sample dock visibility change."""
        self.action.setChecked(visible)
