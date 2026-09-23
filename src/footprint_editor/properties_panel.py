from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QLabel
from PySide6.QtCore import Qt
from footprint_editor.models import Pad, Line, PadShape

class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.no_selection_label = QLabel("Выберите примитив на холсте")
        self.main_layout.addWidget(self.no_selection_label)
        
        self.form_layout = QFormLayout()
        self.main_layout.addLayout(self.form_layout)
        
        self.current_object = None
        self._widgets = []

    def clear_panel(self):
        for widget, label in self._widgets:
            self.form_layout.removeRow(widget)
        self._widgets.clear()
        self.current_object = None
        
    def set_object(self, obj):
        self.clear_panel()
        self.no_selection_label.hide()
        self.current_object = obj
        
        if isinstance(obj, Pad):
            self._build_pad_ui(obj)
        elif isinstance(obj, Line):
            self._build_line_ui(obj)

    def _build_pad_ui(self, pad):
        self._add_spinbox("Ширина (мм):", pad.width, 0.1, 10.0, 0.01, self._on_pad_width_changed)
        self._add_spinbox("Высота (мм):", pad.height, 0.1, 10.0, 0.01, self._on_pad_height_changed)
        
        shape_combo = QComboBox()
        shape_combo.addItem("Прямоугольник", PadShape.RECT)
        shape_combo.addItem("Круг", PadShape.CIRCLE)
        shape_combo.addItem("Овал", PadShape.OVAL)
        shape_combo.setCurrentIndex([PadShape.RECT, PadShape.CIRCLE, PadShape.OVAL].index(pad.shape))
        shape_combo.currentIndexChanged.connect(self._on_pad_shape_changed)
        self.form_layout.addRow("Форма:", shape_combo)
        self._widgets.append((shape_combo, "Форма:"))
        
        self._add_spinbox("X (мм):", pad.x, -500.0, 500.0, 0.01, self._on_pad_x_changed)
        self._add_spinbox("Y (мм):", pad.y, -500.0, 500.0, 0.01, self._on_pad_y_changed)

    def _build_line_ui(self, line):
        self._add_spinbox("Толщина (мм):", line.width, 0.01, 5.0, 0.01, self._on_line_width_changed)
        self._add_spinbox("X1 (мм):", line.x1, -500.0, 500.0, 0.01, self._on_line_x1_changed)
        self._add_spinbox("Y1 (мм):", line.y1, -500.0, 500.0, 0.01, self._on_line_y1_changed)
        self._add_spinbox("X2 (мм):", line.x2, -500.0, 500.0, 0.01, self._on_line_x2_changed)
        self._add_spinbox("Y2 (мм):", line.y2, -500.0, 500.0, 0.01, self._on_line_y2_changed)

    def _add_spinbox(self, label, value, min_val, max_val, step, callback):
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(step)
        spin.setDecimals(4)
        spin.setValue(value)
        spin.valueChanged.connect(callback)
        self.form_layout.addRow(label, spin)
        self._widgets.append((spin, label))

    def _on_pad_width_changed(self, val):
        if self.current_object: self.current_object.width = val; self.current_object.graphics_item.update_geometry()
    def _on_pad_height_changed(self, val):
        if self.current_object: self.current_object.height = val; self.current_object.graphics_item.update_geometry()
    def _on_pad_shape_changed(self, index):
        if self.current_object: 
            self.current_object.shape = [PadShape.RECT, PadShape.CIRCLE, PadShape.OVAL][index]
            self.current_object.graphics_item.update_geometry()
    def _on_pad_x_changed(self, val):
        if self.current_object: self.current_object.x = val; self.current_object.graphics_item.update_geometry()
    def _on_pad_y_changed(self, val):
        if self.current_object: self.current_object.y = val; self.current_object.graphics_item.update_geometry()

    def _on_line_width_changed(self, val):
        if self.current_object: self.current_object.width = val; self.current_object.graphics_item.update_geometry()
    def _on_line_x1_changed(self, val):
        if self.current_object: self.current_object.x1 = val; self.current_object.graphics_item.update_geometry()
    def _on_line_y1_changed(self, val):
        if self.current_object: self.current_object.y1 = val; self.current_object.graphics_item.update_geometry()
    def _on_line_x2_changed(self, val):
        if self.current_object: self.current_object.x2 = val; self.current_object.graphics_item.update_geometry()
    def _on_line_y2_changed(self, val):
        if self.current_object: self.current_object.y2 = val; self.current_object.graphics_item.update_geometry()