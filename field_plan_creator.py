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
        self._polygon_dock = None
        self._point_dock = None

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
        polygon_icon = os.path.join(icon_base, "icon.png")
        if not os.path.exists(polygon_icon):
            polygon_icon = ":/images/themes/default/mActionAddRasterLayer.svg"

        points_icon = os.path.join(icon_base, "icon_points.png")
        if not os.path.exists(points_icon):
            points_icon = ":/images/themes/default/mActionAddRasterLayer.svg"

        # Add Sample Panel action (checkable for dock toggle)
        self.polygon_action = self.add_action(
            polygon_icon,
            "Field plan creator (polygons)",
            self.toggle_polygon_dock,
            status_tip="Toggle field plan creator (polygons)",
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        self.point_action = self.add_action(
            points_icon,
            "Field plan creator (points)",
            self.toggle_point_dock,
            status_tip="Toggle field plan creator (points)",
            checkable=True,
            parent=self.iface.mainWindow(),
        )

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        # Remove dock widgets
        if self._polygon_dock:
            self.iface.removeDockWidget(self._polygon_dock)
            self._polygon_dock.deleteLater()
            self._polygon_dock = None

        if self._point_dock:
            self.iface.removeDockWidget(self._point_dock)
            self._point_dock.deleteLater()
            self._point_dock = None

        # Remove actions from menu
        for action in self.actions:
            self.iface.removePluginMenu("&Plugin Template", action)

        # Remove toolbar
        if self.toolbar:
            del self.toolbar

    def toggle_polygon_dock(self):
        """Toggle the Sample dock widget visibility."""
        if self._polygon_dock is None:
            try:
                from .dialogs.polygon_dock import FPCPolygonDockWidget

                self._polygon_dock = FPCPolygonDockWidget(
                    self.iface, 
                    self.iface.mainWindow(),
                    self.icon_base
                )
                self._polygon_dock.setObjectName("FieldPlanCreatorPolygonFPCDockWidget")
                self._polygon_dock.visibilityChanged.connect(
                    self._on_polygon_visibility_changed
                )
                self.iface.addDockWidget(
                    Qt.DockWidgetArea.RightDockWidgetArea, self._polygon_dock
                )
                self._polygon_dock.show()
                self._polygon_dock.raise_()
                return

            except Exception as e:
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    "Error",
                    f"Failed to create field plan creator panel:\n{str(e)}",
                )
                self.polygon_action.setChecked(False)
                return

        # Toggle visibility
        if self._polygon_dock.isVisible():
            self._polygon_dock.hide()
        else:
            self._polygon_dock.show()
            self._polygon_dock.raise_()

    def toggle_point_dock(self):
        """Toggle the Sample dock widget visibility."""
        if self._point_dock is None:
            try:
                from .dialogs.point_dock import FPCPointDockWidget

                self._point_dock = FPCPointDockWidget(
                    self.iface, 
                    self.iface.mainWindow(),
                    self.icon_base
                )
                self._point_dock.setObjectName("FieldPlanCreatorPolygonFPCDockWidget")
                self._point_dock.visibilityChanged.connect(
                    self._on_point_visibility_changed
                )
                self.iface.addDockWidget(
                    Qt.DockWidgetArea.RightDockWidgetArea, self._point_dock
                )
                self._point_dock.show()
                self._point_dock.raise_()
                return

            except Exception as e:
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    "Error",
                    f"Failed to create field plan creator panel:\n{str(e)}",
                )
                self.point_action.setChecked(False)
                return

        # Toggle visibility
        if self._point_dock.isVisible():
            self._point_dock.hide()
        else:
            self._point_dock.show()
            self._point_dock.raise_()

    def _on_polygon_visibility_changed(self, visible):
        """Handle Sample dock visibility change."""
        self.polygon_action.setChecked(visible)

    def _on_point_visibility_changed(self, visible):
        """Handle Sample dock visibility change."""
        self.point_action.setChecked(visible)
