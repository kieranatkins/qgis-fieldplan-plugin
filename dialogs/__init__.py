"""
Plugin Template Dialogs

This module contains the dialog and dock widget classes for the plugin template.
"""

from .polygon_dock import FPCPolygonDockWidget
from .point_dock import FPCPointDockWidget
from ._fieldplan import _calculate_bearing, _find_line_point_distance, _create_field_plan, _get_board_ids, _four_lines_intersect, _calculate_lines
from ._help_messages import HELP_DICT

__all__ = [
    "FPCPolygonDockWidget",
    "FPCPointDockWidget",
    "UpdateCheckerDialog"
]
