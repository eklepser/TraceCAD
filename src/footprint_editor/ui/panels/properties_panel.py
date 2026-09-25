from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout,
                               QDoubleSpinBox, QComboBox, QLineEdit, QCheckBox,
                               QPushButton)
from PySide6.QtCore import Qt
from footprint_editor.core.models import Pad, Line, Circle, Arc, Text, PadShape
from constants import Styles


class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.form_layout = QFormLayout()
        self.main_layout.addLayout(self.form_layout)

        self.btn_apply = QPushButton("Применить")
        self.btn_apply.setStyleSheet(Styles.APPLY_BUTTON)
        self.btn_apply.clicked.connect(self._apply_changes)
        self.main_layout.addWidget(self.btn_apply)

        self.current_object = None
        self._widgets = {}
        self.btn_apply.hide()

    def apply_theme(self):
        self.btn_apply.setStyleSheet(Styles.APPLY_BUTTON)

    def clear_panel(self):
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self._widgets.clear()
        self.current_object = None
        self.btn_apply.hide()

    def set_object(self, obj):
        self.clear_panel()
        self.current_object = obj
        self.btn_apply.show()
        if isinstance(obj, Pad):
            self._build_pad_ui(obj)
        elif isinstance(obj, Line):
            self._build_line_ui(obj)
        elif isinstance(obj, Circle):
            self._build_circle_ui(obj)
        elif isinstance(obj, Arc):
            self._build_arc_ui(obj)
        elif isinstance(obj, Text):
            self._build_text_ui(obj)

    def _build_pad_ui(self, pad):
        self._add_spinbox("X (мм):", pad.x, -500.0, 500.0, "x")
        self._add_spinbox("Y (мм):", pad.y, -500.0, 500.0, "y")

        text_input = QLineEdit(pad.number)
        self.form_layout.addRow("Номер:", text_input)
        self._widgets["number"] = text_input

        self._add_spinbox("Размер X (мм):", pad.width, 0.1, 50.0, "width")
        self._add_spinbox("Размер Y (мм):", pad.height, 0.1, 50.0, "height")
        self._add_spinbox("Отверстие (мм):", pad.drill or 0.0, 0.0, 50.0, "drill")

        shape_combo = QComboBox()
        shape_combo.addItem("Круг", PadShape.CIRCLE)
        shape_combo.addItem("Квадрат", PadShape.RECT)
        shape_combo.setCurrentIndex(0 if pad.shape == PadShape.CIRCLE else 1)
        self.form_layout.addRow("Форма:", shape_combo)
        self._widgets["shape"] = shape_combo

    def _build_line_ui(self, line):
        self._add_spinbox("X1 (мм):", line.x1, -500.0, 500.0, "x1")
        self._add_spinbox("Y1 (мм):", line.y1, -500.0, 500.0, "y1")
        self._add_spinbox("X2 (мм):", line.x2, -500.0, 500.0, "x2")
        self._add_spinbox("Y2 (мм):", line.y2, -500.0, 500.0, "y2")

    def _build_circle_ui(self, circle):
        self._add_spinbox("X (мм):", circle.x, -500.0, 500.0, "x")
        self._add_spinbox("Y (мм):", circle.y, -500.0, 500.0, "y")
        self._add_spinbox("Диаметр (мм):", circle.radius * 2, 0.1, 20.0, "diameter")

    def _build_arc_ui(self, arc):
        self._add_spinbox("Центр X (мм):", arc.cx, -500.0, 500.0, "cx")
        self._add_spinbox("Центр Y (мм):", arc.cy, -500.0, 500.0, "cy")
        self._add_spinbox("Старт X (мм):", arc.sx, -500.0, 500.0, "sx")
        self._add_spinbox("Старт Y (мм):", arc.sy, -500.0, 500.0, "sy")
        self._add_spinbox("Угол (°):", arc.angle, -359.0, 359.0, "angle")

    def _build_text_ui(self, text):
        self._add_spinbox("X (мм):", text.x, -500.0, 500.0, "x")
        self._add_spinbox("Y (мм):", text.y, -500.0, 500.0, "y")

        text_input = QLineEdit(text.text)
        self.form_layout.addRow("Текст:", text_input)
        self._widgets["text"] = text_input

        visible_check = QCheckBox()
        visible_check.setChecked(text.visible)
        self.form_layout.addRow("Видимый:", visible_check)
        self._widgets["visible"] = visible_check

    def _add_spinbox(self, label, value, min_val, max_val, key):
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(0.01)
        spin.setDecimals(4)
        spin.setValue(value)
        self.form_layout.addRow(label, spin)
        self._widgets[key] = spin

    def _apply_changes(self):
        obj = self.current_object
        if not obj:
            return

        if isinstance(obj, Pad):
            obj.x = self._widgets["x"].value()
            obj.y = self._widgets["y"].value()
            obj.number = self._widgets["number"].text()
            obj.width = self._widgets["width"].value()
            obj.height = self._widgets["height"].value()
            obj.drill = self._widgets["drill"].value()
            obj.shape = self._widgets["shape"].currentData()
        elif isinstance(obj, Line):
            obj.x1 = self._widgets["x1"].value()
            obj.y1 = self._widgets["y1"].value()
            obj.x2 = self._widgets["x2"].value()
            obj.y2 = self._widgets["y2"].value()
        elif isinstance(obj, Circle):
            obj.x = self._widgets["x"].value()
            obj.y = self._widgets["y"].value()
            obj.radius = self._widgets["diameter"].value() / 2
        elif isinstance(obj, Arc):
            obj.cx = self._widgets["cx"].value()
            obj.cy = self._widgets["cy"].value()
            obj.sx = self._widgets["sx"].value()
            obj.sy = self._widgets["sy"].value()
            obj.angle = self._widgets["angle"].value()
        elif isinstance(obj, Text):
            obj.x = self._widgets["x"].value()
            obj.y = self._widgets["y"].value()
            obj.text = self._widgets["text"].text()
            obj.visible = self._widgets["visible"].isChecked()

        obj.graphics_item.update_geometry()