"""
QGIS Plugin Template

A template for creating QGIS plugins with dockable panels.
This plugin provides a starting point for developing custom QGIS plugins.
"""

from .field_plan_creator import FieldPlanCreator


def classFactory(iface):
    """Load PluginTemplate class from file plugin_template.

    Args:
        iface: A QGIS interface instance.

    Returns:
        PluginTemplate: The plugin instance.
    """
    return FieldPlanCreator(iface)
