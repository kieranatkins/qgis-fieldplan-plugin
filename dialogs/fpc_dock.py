"""
Sample Dock Widget for Plugin Template

This module provides a sample dockable panel that demonstrates
how to create dock widgets for QGIS plugins.
"""
import os
import re
import math
from collections import defaultdict
from functools import partial

from qgis.PyQt.QtCore import Qt, QMetaType
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QGroupBox,
    QComboBox,
    QCheckBox,
    QFormLayout,
    QMessageBox,
    QProgressBar,
    QProgressBar,
    QTextEdit
)
from qgis.PyQt.QtGui import QIcon, QValidator, QDoubleValidator, QIntValidator, QColor
from qgis.core import (
    QgsProject, 
    QgsVectorLayer,
    QgsWkbTypes,
    QgsPointXY,
    Qgis,
    QgsGeometry,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsLayoutAligner,
)
from qgis.gui import QgsVScrollArea, QgsMapToolEmitPoint, QgsVertexMarker, QgsRubberBand, QgsMapLayerComboBox, QgsDockWidget

# handle both qt5 and qt6
try:
    from qgis.PyQt.QtSvgWidgets import QSvgWidget
except ImportError:
    from qgis.PyQt.QtSvg import QSvgWidget

from ._fieldplan import _calculate_bearing, _find_line_point_distance, _create_field_plan, _get_board_ids, _calculate_lines
from._help_messages import HELP_DICT

FIELDPLAN_LAYER_NAME = "Field plan"


class CSVDoubleValidator(QValidator):
    _complete_pattern = re.compile(
        r'^\s*-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)*\s*$'
    )

    _partial_pattern = re.compile(
        r'^\s*-?\d*(?:\.\d*)?(?:\s*,\s*-?\d*(?:\.\d*)?)*\s*$'
    )

    def validate(self, text, pos):
        if not text.strip():
            return (QValidator.State.Intermediate, text, pos)

        if self._complete_pattern.match(text):
            return (QValidator.State.Acceptable, text, pos)

        if self._partial_pattern.match(text):
            return (QValidator.State.Intermediate, text, pos)

        return (QValidator.State.Invalid, text, pos)

class CSVDoublePairValidator(QValidator):
    _complete_pattern = re.compile(
        r'^\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*$'
    )

    _partial_pattern = re.compile(
        r'^\s*-?\d*(?:\.\d*)?(?:\s*,\s*-?\d*(?:\.\d*)?)?\s*$'
    )

    def validate(self, text, pos):
        if not text.strip():
            return (QValidator.State.Intermediate, text, pos)

        if self._complete_pattern.match(text):
            return (QValidator.State.Acceptable, text, pos)

        if self._partial_pattern.match(text):
            return (QValidator.State.Intermediate, text, pos)

        return (QValidator.State.Invalid, text, pos)

class CSVIntValidator(QValidator):
    _complete_pattern = re.compile(
        r'^\s*-?\d+(?:\s*,\s*-?\d+)*\s*$'
    )

    _partial_pattern = re.compile(
        r'^\s*-?\d*(?:\s*,\s*-?\d*)*\s*$'
    )

    def validate(self, text, pos):
        if not text.strip():
            return (QValidator.State.Intermediate, text, pos)

        if self._complete_pattern.match(text):
            return (QValidator.State.Acceptable, text, pos)

        if self._partial_pattern.match(text):
            return (QValidator.State.Intermediate, text, pos)

        return (QValidator.State.Invalid, text, pos)

class FPCDockWidget(QgsDockWidget):
    """A sample dockable panel for demonstrating plugin functionality."""

    def __init__(self, iface, parent=None, icon_base=None):
        """Initialize the dock widget.

        Args:
            iface: QGIS interface instance.
            parent: Parent widget.
        """
        super().__init__("Field plan creator", parent)
        self.iface = iface
        self.icon_base = icon_base
        self.is_snap_updated = True

        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        self.fieldplan_layer = None
        self.guidance_layer = None
        self.alley_layer = None
        self.boundary_layer = None

        self._setup_ui()

    def _select_origin(self):
        origin_tool = QgsMapToolEmitPoint(self.canvas)

        def on_click(point, button):         
            self.origin_input.setText(f'{point.x()}, {point.y()}')
            self.canvas.unsetMapTool(origin_tool)

        origin_tool.canvasClicked.connect(on_click)
        self.canvas.setMapTool(origin_tool)

    def _select_bearing(self):
        bearing_tool = QgsMapToolEmitPoint(self.canvas)

        def on_click(point, button):
            self.bearing_point = point
            self.bearing_input.setText(f'{point.x()}, {point.y()}')
            self.canvas.unsetMapTool(bearing_tool)

        bearing_tool.canvasClicked.connect(on_click)
        self.canvas.setMapTool(bearing_tool)

    def _snap_choice_changed(self):
        self.is_snap_updated = False

    def _update_point_to_vector_layer(self, point, layer):
        closest_x = None
        closest_y = None
        closest_line_distance = math.inf

        # not sure why shapes are nested like this, but this is probably the safest way to deal with it?
        for feat in layer.getFeatures():
            geom = feat.geometry().as_numpy()
            for shape1 in geom:
                for shape2 in shape1:
                    for p1, p2 in zip(shape2, shape2[1:]):
                        dist, _x, _y = _find_line_point_distance(p1[0], p1[1], p2[0], p2[1], point.x(), point.y())
                        if dist < closest_line_distance:
                            closest_x, closest_y = _x, _y
                            closest_line_distance = dist

        return QgsPointXY(closest_x, closest_y)

    def _snap_to_shape_update(self):
        origin = self._get_origin()
        snap_layer = self.snap_combo.currentLayer()
        if snap_layer is None:
            return
        
        origin = self._update_point_to_vector_layer(origin, snap_layer)
        self.origin_input.setText(f'{origin.x()}, {origin.y()}')

        bearing = self._get_bearing()
        if type(bearing) is QgsPointXY:
            bearing = self._update_point_to_vector_layer(bearing, snap_layer)
            self.bearing_input.setText(f'{bearing.x()}, {bearing.y()}')

        self.is_snap_updated = True

    def _log(self, text):
        t = self.log_box.toPlainText()
        t = t + text + '\n'
        self.log_box.setText(t)

    def _setup_ui(self):
        """Set up the dock widget UI."""
        # Main widget
        self.canvas = self.iface.mapCanvas()
        main_widget = QWidget()
        scroll_area = QgsVScrollArea()
        scroll_area.setWidgetResizable(True)

        content = QWidget()

        # Main layout
        layout = QVBoxLayout(content)
        layout.setSpacing(15)

        scroll_area.setWidget(content)
        self.setWidget(scroll_area)

        # Diagram
        diagram = QSvgWidget(os.path.join(self.icon_base, "diagram.svg"))
        diagram.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        diagram.setMinimumHeight(512)
        
        ## Input section
        param_group_1 = QGroupBox("Site parameters")
        param_layout_1 = QFormLayout(param_group_1)

        self.help_btns = {}

        # origin
        origin_controls = QHBoxLayout()
        self.origin_marker = QgsVertexMarker(self.canvas)
        self.origin_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        self.origin_marker.setIconSize(18)
        self.origin_marker.setColor(QColor("purple"))
        self.origin_marker.hide()
        self.origin_input = QLineEdit()
        self.origin_input.textChanged.connect(self._update_markers)
        self.origin_input.setValidator(CSVDoublePairValidator())
        self.origin_btn = QPushButton()
        self.origin_btn.clicked.connect(self._select_origin)
        self.origin_btn.setIcon(QIcon(":/images/themes/default/cursors/mCapturePoint.svg"))
        self.help_btns['origin'] = QPushButton()
        origin_controls.addWidget(self.origin_input)
        origin_controls.addWidget(self.origin_btn)
        origin_controls.addWidget(self.help_btns['origin'])
        param_layout_1.addRow("Origin:", origin_controls)

        # bearing
        bearing_controls = QHBoxLayout()
        self.bearing_line = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.bearing_line.setWidth(3)
        self.bearing_line.setColor(QColor("purple"))
        self.bearing_line.hide()
        self.bearing_marker = QgsVertexMarker(self.canvas)
        self.bearing_marker.setIconType(QgsVertexMarker.ICON_BOX)
        self.bearing_marker.setIconSize(18)
        self.bearing_marker.setColor(QColor("purple"))
        self.bearing_marker.hide()
        self.bearing_input = QLineEdit()
        self.bearing_input.textChanged.connect(self._update_markers)
        self.bearing_input.setValidator(CSVDoublePairValidator())
        self.bearing_btn = QPushButton()
        self.bearing_btn.clicked.connect(self._select_bearing)
        self.bearing_btn.setIcon(QIcon(":/images/themes/default/cursors/mCapturePoint.svg"))
        self.help_btns['bearing'] = QPushButton()
        bearing_controls.addWidget(self.bearing_input)
        bearing_controls.addWidget(self.bearing_btn)
        bearing_controls.addWidget(self.help_btns['bearing'])
        param_layout_1.addRow("Bearing:", bearing_controls)

        # snap to shape
        snap_controls = QHBoxLayout()
        self.snap_combo = QgsMapLayerComboBox()
        self.snap_combo.setFilters(Qgis.LayerFilter.PolygonLayer)
        self.snap_combo.setAllowEmptyLayer(True)
        self.snap_combo.setLayer(None)
        self.snap_combo.activated.connect(self._snap_choice_changed)
        self.snap_update_btn = QPushButton("Update")
        self.snap_update_btn.setMaximumWidth(100)
        self.snap_update_btn.clicked.connect(self._snap_to_shape_update)
        self.help_btns['snap'] = QPushButton()
        snap_controls.addWidget(self.snap_combo)
        snap_controls.addWidget(self.snap_update_btn)
        snap_controls.addWidget(self.help_btns['snap'])
        param_layout_1.addRow("Snap to shape:", snap_controls)

        # field boundary
        field_boundary_controls = QHBoxLayout()
        self.field_boundary_combo = QgsMapLayerComboBox()
        self.field_boundary_combo.setFilters(Qgis.LayerFilter.PolygonLayer)
        self.field_boundary_combo.setAllowEmptyLayer(True)
        self.field_boundary_combo.setLayer(None)
        self.help_btns['field_boundary'] = QPushButton()
        field_boundary_controls.addWidget(self.field_boundary_combo)
        field_boundary_controls.addWidget(self.help_btns['field_boundary'])
        param_layout_1.addRow("Field boundary:", field_boundary_controls)

        # direction
        direction_controls = QHBoxLayout()
        self.direction_combo = QComboBox()
        self.direction_combo.addItem("Right")
        self.direction_combo.addItem("Left")
        self.help_btns['direction'] = QPushButton()
        direction_controls.addWidget(self.direction_combo)
        direction_controls.addWidget(self.help_btns['direction'])
        param_layout_1.addRow("Direction:", direction_controls)

        # margin
        margin_controls = QHBoxLayout()
        self.margin_input_x = QLineEdit()
        self.margin_input_x.setValidator(QDoubleValidator())
        self.margin_input_x.setText("0")
        self.margin_input_y = QLineEdit()
        self.margin_input_y.setValidator(QDoubleValidator())
        self.margin_input_y.setText("0")
        self.help_btns['margin'] = QPushButton()
        margin_controls.addWidget(QLabel("x"))
        margin_controls.addWidget(self.margin_input_x)
        margin_controls.addWidget(QLabel("y"))
        margin_controls.addWidget(self.margin_input_y)
        margin_controls.addWidget(self.help_btns['margin'])
        param_layout_1.addRow("Margin:", margin_controls)

        # grid number
        grid_number_controls = QHBoxLayout()
        self.grid_number_input = QLineEdit()
        val = QIntValidator()
        val.setBottom(1)
        self.grid_number_input.setValidator(val)
        self.grid_number_input.setText("1")
        self.help_btns['grid_number'] = QPushButton()
        grid_number_controls.addWidget(self.grid_number_input)
        grid_number_controls.addWidget(self.help_btns['grid_number'])
        param_layout_1.addRow("Grid number:", grid_number_controls)

        # grid gap
        grid_gap_controls = QHBoxLayout()
        self.grid_gap_input = QLineEdit()
        self.grid_gap_input.setValidator(CSVDoubleValidator())
        self.grid_gap_input.setText("0")
        self.help_btns['grid_gap'] = QPushButton()
        grid_gap_controls.addWidget(self.grid_gap_input)
        grid_gap_controls.addWidget(self.help_btns['grid_gap'])
        param_layout_1.addRow("Grid gap:", grid_gap_controls)

        # subplots
        subplots_controls = QHBoxLayout()
        self.subplot_input = QLineEdit("1")
        self.subplot_input.setValidator(QIntValidator())
        self.help_btns['subplots'] = QPushButton()
        subplots_controls.addWidget(self.subplot_input)
        subplots_controls.addWidget(self.help_btns['subplots'])
        param_layout_1.addRow('Subplots:', subplots_controls)

        # grid params
        param_group_2 = QGroupBox("Grid parameters")
        param_layout_2 = QFormLayout(param_group_2)

        self.grid_params = {}

        # do grid params that accept ints only first
        grid_int_param_names = ['Rows', 'Columns']
        for n in grid_int_param_names:
            key = n.lower()
            controls = QHBoxLayout()
            te = QLineEdit()
            te.setValidator(CSVIntValidator())
            btn = QPushButton()
            controls.addWidget(te)
            controls.addWidget(btn)
            param_layout_2.addRow(f'{n}:', controls)
            self.grid_params[key] = te
            self.help_btns[key] = btn

        # then grid params that accept doubles
        grid_float_param_names = ['1', '2', '3']
        for n in grid_float_param_names:
            key = n.lower()
            controls = QHBoxLayout()
            te = QLineEdit()
            te.setValidator(QDoubleValidator())
            btn = QPushButton()
            controls.addWidget(te)
            controls.addWidget(btn)
            param_layout_2.addRow(f'{n}:', controls)
            self.grid_params[key] = te
            self.help_btns[key] = btn

        # then grid params that accept CSV doubles
        grid_float_param_names = ['4', '5']
        for n in grid_float_param_names:
            key = n.lower()
            controls = QHBoxLayout()
            te = QLineEdit()
            te.setValidator(CSVDoubleValidator())
            btn = QPushButton()
            controls.addWidget(te)
            controls.addWidget(btn)
            param_layout_2.addRow(f'{n}:', controls)
            self.grid_params[key] = te
            self.help_btns[key] = btn

        # outputs
        param_group_3 = QGroupBox("Output options")
        param_layout_3 = QFormLayout(param_group_3)

        output_checkbox_names = [
            'Column serpentine ID',
            'Subplot serpentine ID',
            'Reverse subplot ID',
            'Return guidance lines',
            'Return alley lines',
            'Return grid boundaries',
        ]
        self.output_checkboxes = {}

        for n in output_checkbox_names:
            key = n.lower().replace(' ', '_')
            controls = QHBoxLayout()
            cb = QCheckBox(n)
            cb.setChecked(False)
            btn = QPushButton()
            controls.addWidget(cb)
            controls.addWidget(btn)
            param_layout_3.addRow('', controls)
            self.output_checkboxes[key] = cb
            self.help_btns[key] = btn

            # add guidance lines marign
            if key == 'return_grid_boundaries':
                controls = QHBoxLayout()
                controls_container = QWidget()
                controls_container.setLayout(controls)
                self.guidance_line_margin_input = QLineEdit()
                self.guidance_line_margin_input.setValidator(QDoubleValidator())
                self.guidance_line_margin_input.setText("0")
                btn = QPushButton()
                controls.addWidget(QLabel('Grid boundary margin:'))
                controls.addWidget(self.guidance_line_margin_input)
                controls.addWidget(btn)
                param_layout_3.addRow('', controls_container)
                controls_container.setVisible(False)
                self.help_btns['grid_boundary_margin'] = btn
                cb.toggled.connect(lambda: controls_container.setVisible(cb.isChecked()))

        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run_action)

        for key, btn in self.help_btns.items():
            btn.setIcon(QIcon(os.path.join(self.icon_base, "about.svg")))
            btn.setMaximumWidth(30)
            btn.setProperty("key", key)
            btn.clicked.connect(self._show_help)

        layout.addWidget(diagram)
        layout.addWidget(param_group_1)
        layout.addWidget(param_group_2)
        layout.addWidget(param_group_3)
        layout.addWidget(self.run_btn)

        # Stretch at the end
        layout.addStretch()

        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        layout.addWidget(self.progress)

        # Status label
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(150)
        self.log_box.setPlaceholderText("Log")

        layout.addWidget(self.log_box)

    def _initialize_layers(self):
        crs = QgsProject.instance().crs().authid()
        # setup each layer, will try to empty existing layer if pos, otherwise create new layer
        try:
            self.fieldplan_layer.dataProvider().truncate()
            self.fieldplan_layer.triggerRepaint()
        except (RuntimeError, AttributeError):
            self.fieldplan_layer = QgsVectorLayer(f"Polygon?crs={crs}", "Fieldplan", "memory")

        try:
            self.guidance_layer.dataProvider().truncate()
            self.guidance_layer.triggerRepaint()
        except (RuntimeError, AttributeError):
            self.guidance_layer = QgsVectorLayer(f"Linestring?crs={crs}", "Guidance lines", "memory")

        try:
            self.alley_layer.dataProvider().truncate()
            self.alley_layer.triggerRepaint()
        except (RuntimeError, AttributeError):
            self.alley_layer = QgsVectorLayer(f"Linestring?crs={crs}", "Alley lines", "memory")

        try:
            self.boundary_layer.dataProvider().truncate()
            self.boundary_layer.triggerRepaint()
        except (RuntimeError, AttributeError):
            self.boundary_layer = QgsVectorLayer(f"Linestring?crs={crs}", "Grid boundaries", "memory")

    def _show_help(self):
        btn = self.sender()
        key = btn.property("key")
        help = HELP_DICT[key]
        QMessageBox.information(self, key, help)

    def _get_origin(self):
        o_x, o_y = [float(val) for val in self.origin_input.text().split(',')]
        origin = QgsPointXY(o_x, o_y)
        return origin

    def _get_bearing(self):
        bearing = self.bearing_input.text().split(',')

        if len(bearing) == 1:
            bearing = float(bearing[0])
        elif len(bearing) == 2:
            bearing = QgsPointXY(float(bearing[0]), float(bearing[1]))
        else:
            raise ValueError("Bearing can either be a single degree value or two comma-separated northing and easting values")

        return bearing

    def _update_markers(self):
        try:
            origin = self._get_origin()
            self.origin_marker.setCenter(origin)
            self.origin_marker.show()

            bearing = self._get_bearing()
            if type(bearing) is float:
                bearing = self._calculate_bearing_endpoint(origin, 10, bearing)
                self.bearing_marker.hide()
            else:
                self.bearing_marker.setCenter(bearing)
                self.bearing_marker.show()

            self.bearing_line.reset(QgsWkbTypes.LineGeometry)
            self.bearing_line.addPoint(origin)
            self.bearing_line.addPoint(bearing)
            self.bearing_line.show()
        except (ValueError, TypeError):
            pass

    def _remove_markers(self):
        self.origin_marker.hide()
        self.bearing_marker.hide()
        self.bearing_line.hide()

    def _calculate_bearing_endpoint(self, origin, length, bearing):
        northing, easting = origin.x(), origin.y()

        bearing_rad = math.radians(bearing)
        end_northing = northing + length * math.sin(bearing_rad)
        end_easting = easting + length * math.cos(bearing_rad)

        endpoint = QgsPointXY(end_northing, end_easting)

        return endpoint
        
    def _process_parameters(self):
        params = {}
        try:
            # site parameters
            origin, bearing = self._get_origin(), self._get_bearing()
            params['origin'] = origin
            if type(bearing) is float:
                params['bearing'] = bearing
            else:
                params['bearing'] = _calculate_bearing(origin.x(), origin.y(), bearing.x(), bearing.y())
            params['field_boundary'] = self.field_boundary_combo.currentLayer()
            params['is_left'] = bool(self.direction_combo.currentIndex())
            margin_x = 0 if self.margin_input_x.text() == "" else float(self.margin_input_x.text())
            margin_y = 0 if self.margin_input_y.text() == "" else float(self.margin_input_y.text())
            params['margin'] = margin_x, margin_y
            params['grid_number'] = int(self.grid_number_input.text())
            n = params['grid_number']
            text = self.grid_gap_input.text().split(',')
            assert len(text) == 1 or len(text) == params['grid_number']-1, "Inconsistent number of values in \"grid gap\" for the \"grid number\""
            params['grid_gap'] = [float(v) for v in text] if len(text) > 1 else [float(text[0])] * n
            params['subplots'] = int(self.subplot_input.text())

            # grid parameters
            csv_grid_params = ['rows', 'columns', '4', '5']
            for k in csv_grid_params:
                v = self.grid_params[k]
                text = v.text().split(',')
                assert len(text) == 1 or len(text) == n, f"Inconsistent number of values in \"{k}\" for the \"grid number\""
                params[k] = [float(x) for x in text] if len(text) == n else [float(text[0])] * n

            # other grid params
            non_csv_grid_params = ['1', '2', '3']
            for k in non_csv_grid_params:
                v = self.grid_params[k].text()
                params[k] = float(v)

            # output parameters
            for k, v in self.output_checkboxes.items():
                params[k] = bool(v.isChecked())

            params['grid_boundary_margin'] = 0 if self.guidance_line_margin_input.text().strip() == "" else float(self.guidance_line_margin_input.text())

            assert params['subplots'] > 0
            assert all([r > 0 for r in params['rows']])
            assert all([c > 0 for c in params['columns']])

            return params

        except (ValueError, AssertionError) as e:
            # self.iface.messageBar().pushMessage('Alert', f'Fieldplan parameter error: {e}')
            QMessageBox.information(self, 'Fieldplan parameter error', str(e))

    def _run_action(self):
        # Get current values
        self.log_box.setPlainText("")
        params = self._process_parameters()
        self.progress.setValue(0)
        if params is None:
            return

        self._initialize_layers()

        provider = self.fieldplan_layer.dataProvider()
        fields = QgsFields()
        fields.append(QgsField("id", QMetaType.Type.Int))
        fields.append(QgsField("grid", QMetaType.Type.Int))
        fields.append(QgsField("row", QMetaType.Type.Int))
        fields.append(QgsField("col", QMetaType.Type.Int))
        fields.append(QgsField("plot", QMetaType.Type.Int))
        fields.append(QgsField("roc", QMetaType.Type.QString))
        provider.addAttributes(fields)
        self.fieldplan_layer.updateFields()

        self.progress.setValue(5)

        # build field plan
        # self.status_label.setText("Generating polygons...")
        params['bearing_radians'] = math.radians(params['bearing'] - 180)
        polygons, grid_ids, column_ids, row_ids, plot_ids = _create_field_plan(params)
        features = []
        for p, grid_id, col_id, row_id, plot_id in zip(polygons, grid_ids, column_ids, row_ids, plot_ids):
            feat = dict(polygon=p, 
                        grid=grid_id,
                        col=col_id,
                        row=row_id,
                        plot=plot_id)
            features.append(feat)
        self.progress.setValue(30)

        # Check all shapes fit within field boundary, only keep those that fit
        if params['field_boundary'] is not None:
            field_boundary = params['field_boundary']
            # self.status_label.setText('Removing shapes outside field boundary...') 
            
            # Build geometry engine and bbox to speed up intersection checks
            boundary_geom = QgsGeometry.unaryUnion(
                [feat.geometry() for feat in field_boundary.getFeatures()]
            )
            boundary_engine = QgsGeometry.createGeometryEngine(boundary_geom.constGet())
            boundary_engine.prepareGeometry()
            boundary_bbox = boundary_geom.boundingBox()

            outside_field_ids = []
            n_deleted = 0
            for i, feat in enumerate(features):
                polygon = [QgsPointXY(x,y) for x,y in feat['polygon']]
                polygon = QgsGeometry.fromPolygonXY([polygon])
                keep = True

                # Bounding box pre-check
                if not boundary_bbox.contains(polygon.boundingBox()):
                    keep = False
                elif not boundary_engine.contains(polygon.constGet()):
                    keep = False

                if not keep:
                    outside_field_ids.append(i)
                    n_deleted += 1

                prog_value = i / len(features)
                scaled = 30 + prog_value * (60 - 30)
                self.progress.setValue(int(scaled))
            
            # This portion very slow it seems, not 100% sure why
            remove_set = set()
            for i in outside_field_ids:
                ids = _get_board_ids(i, params['subplots'])
                remove_set.update(ids)
            features = [f for i, f in enumerate(features) if i not in remove_set]
            # self.status_label.setText(f'{n_deleted} shapes deleted outside the field boundary.')        

        self.progress.setValue(60) 

        # Calculate lines
        if params['return_guidance_lines'] or params['return_alley_lines'] or params['return_grid_boundaries']:
            # self.status_label.setText('Calculating lines...')
            gl_coords, gt_cols, al_coords, al_rows, al_grid, bl_coords, bl_grid = _calculate_lines(features, params['subplots'], params['grid_boundary_margin'], params['bearing_radians'])
            self.progress.setValue(65)

        # self.status_label.setText('Renumbering IDs...')
        ## Renumber IDs after deleted
        renumbered_id = 1
        subplots_serpentine_switch = False if params['reverse_subplot_id'] else True
        col_serpentine_switch = True

        # group records by col and iterate
        cols = defaultdict(list)
        for f in features:
            cols[f['col']].append(f)

        for i, col_id in enumerate(cols.keys()):
            col = cols[col_id]
            col = col if col_serpentine_switch else reversed(col)

            # group records by grid and iterate
            grids = defaultdict(list)
            for f in col:
                grids[f['grid']].append(f)
            
            for grid_id in grids.keys():
                grid = grids[grid_id]
                rows = defaultdict(list)

                # group records by row, then iterate over each plot
                for f in grid:
                    rows[f['row']].append(f)
                
                for row_id in rows.keys():
                    board = rows[row_id]
                    board = board if subplots_serpentine_switch else reversed(board)

                    for j, feat in enumerate(board, start=1):
                        feat['id'] = int(renumbered_id)
                        feat['grid'] = int(grid_id)
                        feat['row'] = int(row_id)
                        feat['col'] = int(col_id)
                        feat['plot'] = int(j)
                        renumbered_id += 1
                    
                    subplots_serpentine_switch = not subplots_serpentine_switch if params['subplot_serpentine_id'] else True

            prog_value = i / len(cols.keys())
            scaled = 65 + prog_value * (80 - 65)
            self.progress.setValue(60)

            col_serpentine_switch = not col_serpentine_switch if params['column_serpentine_id'] else True

        self.progress.setValue(60)

        num_col = 0
        num_row = 0
        self.fieldplan_layer.startEditing()
        
        for f in features:
            feat = QgsFeature()
            polygon = [QgsPointXY(x,y) for x,y in f['polygon']]
            feat.setGeometry(QgsGeometry.fromPolygonXY([polygon]))
            feat.setAttributes([f['id'], f['grid'], f['row'], f['col'], f['plot'], f'{f["row"]} / {f["col"]}'])
            provider.addFeature(feat)

            num_col = max(num_col, f['col'])
            num_row = max(num_row, f['row'])
        
        self._log(f'{len(features)} total features created with {num_col} columns, {num_row} rows and {len(features) // params['subplots']} plots.')
        self._log('Parameters:')
        for k, v in params.items():
            if type(v) == QgsPointXY:
                self._log(f'\t{k} = {v.x()}, {v.y()}')
            else:
                self._log(f'\t{k} = {v}')


        self.fieldplan_layer.commitChanges()
        self.fieldplan_layer.updateExtents()
        QgsProject.instance().addMapLayer(self.fieldplan_layer)

        if params['return_guidance_lines']:
            self.guidance_layer.startEditing()

            guidenace_provider = self.guidance_layer.dataProvider()
            guidance_fields = QgsFields()
            guidance_fields.append(QgsField("col", QMetaType.Type.Int))
            guidance_fields.append(QgsField("start_x", QMetaType.Type.Double))
            guidance_fields.append(QgsField("start_y", QMetaType.Type.Double))
            guidance_fields.append(QgsField("end_x", QMetaType.Type.Double))
            guidance_fields.append(QgsField("end_y", QMetaType.Type.Double))
            guidenace_provider.addAttributes(guidance_fields)
            self.guidance_layer.updateFields()

            for (x1, y1, x2, y2), col in zip(gl_coords, gt_cols):
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x1, y1), QgsPointXY(x2, y2)]))
                feat.setAttributes([col+1, x1, y1, x2, y2])
                guidenace_provider.addFeature(feat)
            
            self.guidance_layer.commitChanges()
            self.guidance_layer.updateExtents()
            QgsProject.instance().addMapLayer(self.guidance_layer)

        if params['return_alley_lines']:
            self.alley_layer.startEditing()

            alley_provider = self.alley_layer.dataProvider()
            alley_fields = QgsFields()
            alley_fields.append(QgsField("row", QMetaType.Type.Int))
            alley_fields.append(QgsField("grid", QMetaType.Type.Int))
            alley_fields.append(QgsField("start_x", QMetaType.Type.Double))
            alley_fields.append(QgsField("start_y", QMetaType.Type.Double))
            alley_fields.append(QgsField("end_x", QMetaType.Type.Double))
            alley_fields.append(QgsField("end_y", QMetaType.Type.Double))
            alley_provider.addAttributes(alley_fields)
            self.alley_layer.updateFields()

            for (x1, y1, x2, y2), row, grid in zip(al_coords, al_rows, al_grid):
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x1, y1), QgsPointXY(x2, y2)]))
                feat.setAttributes([row+1, grid+1, x1, y1, x2, y2])
                alley_provider.addFeature(feat)
            
            self.alley_layer.commitChanges()
            self.alley_layer.updateExtents()
            QgsProject.instance().addMapLayer(self.alley_layer)

        if params['return_grid_boundaries']:
            self.boundary_layer.startEditing()

            boundary_provider = self.boundary_layer.dataProvider()
            boundary_fields = QgsFields()
            boundary_fields.append(QgsField("grid", QMetaType.Type.Int))
            boundary_fields.append(QgsField("start_x", QMetaType.Type.Double))
            boundary_fields.append(QgsField("start_y", QMetaType.Type.Double))
            boundary_fields.append(QgsField("end_x", QMetaType.Type.Double))
            boundary_fields.append(QgsField("end_y", QMetaType.Type.Double))
            boundary_provider.addAttributes(boundary_fields)
            self.boundary_layer.updateFields()

            for (x1, y1, x2, y2), grid in zip(bl_coords, bl_grid):
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x1, y1), QgsPointXY(x2, y2)]))
                feat.setAttributes([grid, x1, y1, x2, y2])
                boundary_provider.addFeature(feat)
            
            self.boundary_layer.commitChanges()
            self.boundary_layer.updateExtents()
            QgsProject.instance().addMapLayer(self.boundary_layer)

        self.progress.setValue(100)

    def closeEvent(self, event):
        """Handle dock widget close event."""
        # Disconnect signals
        self._remove_markers()

        event.accept()

    def showEvent(self, event):
        self._update_markers()
        event.accept()
