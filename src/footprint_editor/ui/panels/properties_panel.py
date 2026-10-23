from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel,
                               QDoubleSpinBox, QComboBox, QLineEdit, QCheckBox,
                               QPushButton, QListView)
from PySide6.QtCore import Qt
from footprint_editor.core.models import (
    Pad, Line, Circle, Arc, Text, PadShape, PadType, TextType,
    default_layers_for_pad_type
)
from constants import Styles
from footprint_editor.ui.panels.layers_table import LayersTable


TYPE_NAMES_RU = {
    Pad: "Конт. площадка",
    Line: "Линия",
    Circle: "Окружность",
    Arc: "Дуга",
    Text: "Текст",
}

PAD_TYPE_NAMES = {
    PadType.STANDARD: "Стандарт",
    PadType.SMD: "SMD",
    PadType.CONN: "Conn",
}

PAD_TYPE_ORDER = [PadType.STANDARD, PadType.SMD, PadType.CONN]


CHECKBOX_QSS = (
    "QCheckBox { color: #a9b7c6; spacing: 8px; background: transparent; }"
    "QCheckBox::indicator { width: 14px; height: 14px;"
    " border: 1px solid #d8d8d8; background-color: #2b2b2b;"
    " border-radius: 2px; }"
    "QCheckBox::indicator:hover { border: 1px solid #ffffff; }"
    "QCheckBox::indicator:checked {"
    " border: 1px solid #ffffff; background-color: #365880; }"
)


class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(6)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.header_label = QLabel("")
        self.header_label.setStyleSheet(Styles.SECTION_LABEL)
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.form_widget = QWidget()
        self.form_widget.setObjectName("PropertiesTable")
        self.form_widget.setStyleSheet(self._form_widget_qss())
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setContentsMargins(8, 8, 8, 8)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.form_layout.setHorizontalSpacing(8)
        self.form_layout.setVerticalSpacing(4)

        self.buttons_widget = QWidget()
        btns = QHBoxLayout(self.buttons_widget)
        btns.setContentsMargins(0, 0, 0, 0)
        btns.setSpacing(6)

        self.btn_reset = QPushButton("Отменить")
        self.btn_reset.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_reset.clicked.connect(self._reset_changes)

        self.btn_apply = QPushButton("Применить")
        self.btn_apply.setStyleSheet(Styles.APPLY_BUTTON)
        self.btn_apply.clicked.connect(self._apply_changes)

        btns.addWidget(self.btn_reset)
        btns.addWidget(self.btn_apply)

        self.main_layout.addWidget(self.header_label)
        self.main_layout.addWidget(self.form_widget)
        self.main_layout.addWidget(self.buttons_widget)
        self.main_layout.addStretch()

        self.header_label.hide()
        self.form_widget.hide()
        self.buttons_widget.hide()

        self.current_object = None
        self._widgets = {}
        self._building = False

    def _form_widget_qss(self):
        return (
            "QWidget#PropertiesTable { background-color: #2b2b2b;"
            " border: 1px solid #555555; }"
            " QWidget#PropertiesTable QLabel { background: transparent; }"
            " QWidget#PropertiesTable QLineEdit,"
            " QWidget#PropertiesTable QDoubleSpinBox,"
            " QWidget#PropertiesTable QComboBox {"
            "   background: transparent; color: #ffffff;"
            "   border: none; border-bottom: 1px solid #555555;"
            "   padding: 2px 2px;"
            " }"
            " QWidget#PropertiesTable QLineEdit:focus,"
            " QWidget#PropertiesTable QDoubleSpinBox:focus,"
            " QWidget#PropertiesTable QComboBox:focus {"
            "   border-bottom: 1px solid #365880;"
            " }"
            " QWidget#PropertiesTable QLineEdit:hover,"
            " QWidget#PropertiesTable QDoubleSpinBox:hover,"
            " QWidget#PropertiesTable QComboBox:hover {"
            "   border-bottom: 1px solid #7a7a7a;"
            " }"
            " QWidget#PropertiesTable QComboBox::drop-down {"
            "   border: none; width: 14px; }"
            " QWidget#PropertiesTable QDoubleSpinBox::up-button,"
            " QWidget#PropertiesTable QDoubleSpinBox::down-button {"
            "   background: transparent; border: none; width: 12px; }"
        )

    def apply_theme(self):
        self.header_label.setStyleSheet(Styles.SECTION_LABEL)
        self.form_widget.setStyleSheet(self._form_widget_qss())
        self.btn_apply.setStyleSheet(Styles.APPLY_BUTTON)
        self.btn_reset.setStyleSheet(Styles.BUTTON_CANCEL)

    def clear_panel(self):
        self.setUpdatesEnabled(False)
        try:
            while self.form_layout.rowCount() > 0:
                self.form_layout.removeRow(0)
            self._widgets.clear()
            self.current_object = None
            self.header_label.hide()
            self.form_widget.hide()
            self.buttons_widget.hide()
            self.header_label.setText("")
        finally:
            self.setUpdatesEnabled(True)

    def set_object(self, obj):
        self.setUpdatesEnabled(False)
        try:
            self._building = True
            try:
                while self.form_layout.rowCount() > 0:
                    self.form_layout.removeRow(0)
                self._widgets.clear()
            finally:
                self._building = False

            self.current_object = obj

            type_name = TYPE_NAMES_RU.get(type(obj), "Объект")
            self.header_label.setText(f"{type_name} #{obj.uid}")

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

            self.header_label.show()
            self.form_widget.show()
            self.buttons_widget.show()
            self.main_layout.invalidate()
        finally:
            self.setUpdatesEnabled(True)
            self.updateGeometry()
            self.update()

    def refresh_values(self):
        obj = self.current_object
        if not obj or self._building:
            return

        self.setUpdatesEnabled(False)
        try:
            if isinstance(obj, Pad):
                self._widgets["x"].setValue(obj.x)
                self._widgets["y"].setValue(obj.y)
                self._widgets["width"].setValue(obj.width)
                self._widgets["height"].setValue(obj.height)
                self._widgets["drill"].setValue(obj.drill or 0.0)
            elif isinstance(obj, Line):
                self._widgets["x"].setValue(obj.x)
                self._widgets["y"].setValue(obj.y)
                self._widgets["x2"].setValue(obj.x2)
                self._widgets["y2"].setValue(obj.y2)
                self._widgets["width"].setValue(obj.width)
            elif isinstance(obj, Circle):
                self._widgets["x"].setValue(obj.x)
                self._widgets["y"].setValue(obj.y)
                self._widgets["diameter"].setValue(obj.radius * 2)
                self._widgets["width"].setValue(obj.width)
            elif isinstance(obj, Arc):
                self._widgets["x"].setValue(obj.x)
                self._widgets["y"].setValue(obj.y)
                self._widgets["sx"].setValue(obj.sx)
                self._widgets["sy"].setValue(obj.sy)
                self._widgets["angle"].setValue(obj.angle)
                self._widgets["width"].setValue(obj.width)
            elif isinstance(obj, Text):
                self._widgets["x"].setValue(obj.x)
                self._widgets["y"].setValue(obj.y)
                self._widgets["size"].setValue(obj.size)
                self._widgets["text"].setText(obj.text)
                self._widgets["visible"].setChecked(obj.visible)
        finally:
            self.setUpdatesEnabled(True)

    def _make_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("background: transparent; color: #a9b7c6;")
        label.setMinimumWidth(90)
        label.setWordWrap(False)
        return label

    def _add_row(self, label_text, field_widget, key):
        self.form_layout.addRow(self._make_label(label_text), field_widget)
        self._widgets[key] = field_widget

    def _add_layers_block(self, initial_layers, multi):
        header = QLabel("Слои:")
        header.setStyleSheet("background: transparent; color: #a9b7c6;")
        self.form_layout.addRow(header)

        layers_table = LayersTable(multi=multi)
        layers_table.set_layers(initial_layers)
        self.form_layout.addRow(layers_table)
        self._widgets["layers_table"] = layers_table
        return layers_table

    def _make_combo_view(self):
        view = QListView()
        view.setStyleSheet(
            "QListView { background-color: #2b2b2b; color: #a9b7c6;"
            " border: 1px solid #555555; outline: 0; }"
            "QListView::item { padding: 4px 8px; }"
            "QListView::item:selected {"
            "  background-color: #365880; color: white; }"
        )
        view.setMinimumWidth(140)
        view.setSpacing(0)
        return view

    def _make_combo(self, items, current_index=0):
        combo = QComboBox()
        for label, data in items:
            combo.addItem(label, data)
        combo.setCurrentIndex(current_index)
        combo.setView(self._make_combo_view())
        combo.setStyleSheet(
            "QComboBox { background: transparent; color: #ffffff;"
            " border: none; border-bottom: 1px solid #555555;"
            " padding: 2px 2px; }"
            " QComboBox:hover { border-bottom: 1px solid #7a7a7a; }"
            " QComboBox:focus { border-bottom: 1px solid #365880; }"
            " QComboBox::drop-down { border: none; width: 14px; }"
        )
        return combo

    def _build_pad_ui(self, pad):
        pad_type_combo = self._make_combo(
            [(PAD_TYPE_NAMES[pt], pt) for pt in PAD_TYPE_ORDER],
            PAD_TYPE_ORDER.index(pad.pad_type) if pad.pad_type in PAD_TYPE_ORDER else 0,
        )
        pad_type_combo.currentIndexChanged.connect(
            lambda _i, p=pad, c=pad_type_combo: self._on_pad_type_changed(p, c)
        )
        self._add_row("Тип:", pad_type_combo, "pad_type")

        self._add_spinbox("X, мм:", pad.x, -500.0, 500.0, "x")
        self._add_spinbox("Y, мм:", pad.y, -500.0, 500.0, "y")

        text_input = QLineEdit(pad.number)
        self._add_row("Номер:", text_input, "number")

        self._add_spinbox("Ширина, мм:", pad.width, 0.1, 50.0, "width")
        self._add_spinbox("Высота, мм:", pad.height, 0.1, 50.0, "height")
        self._add_spinbox("Отверстие, мм:", pad.drill or 0.0, 0.0, 50.0, "drill")

        shape_combo = self._make_combo(
            [("Круг", PadShape.CIRCLE), ("Квадрат", PadShape.RECT)],
            0 if pad.shape == PadShape.CIRCLE else 1,
        )
        self._add_row("Форма:", shape_combo, "shape")

        self._add_layers_block(pad.layers, multi=True)

    def _build_line_ui(self, line):
        self._add_spinbox("X1, мм:", line.x, -500.0, 500.0, "x")
        self._add_spinbox("Y1, мм:", line.y, -500.0, 500.0, "y")
        self._add_spinbox("X2, мм:", line.x2, -500.0, 500.0, "x2")
        self._add_spinbox("Y2, мм:", line.y2, -500.0, 500.0, "y2")
        self._add_spinbox("Толщина, мм:", line.width, 0.01, 5.0, "width")
        self._add_layers_block([line.layer], multi=False)

    def _build_circle_ui(self, circle):
        self._add_spinbox("Центр X, мм:", circle.x, -500.0, 500.0, "x")
        self._add_spinbox("Центр Y, мм:", circle.y, -500.0, 500.0, "y")
        self._add_spinbox("Диаметр, мм:", circle.radius * 2, 0.1, 20.0, "diameter")
        self._add_spinbox("Толщина, мм:", circle.width, 0.01, 5.0, "width")
        self._add_layers_block([circle.layer], multi=False)

    def _build_arc_ui(self, arc):
        self._add_spinbox("Центр X, мм:", arc.x, -500.0, 500.0, "x")
        self._add_spinbox("Центр Y, мм:", arc.y, -500.0, 500.0, "y")
        self._add_spinbox("Начало X, мм:", arc.sx, -500.0, 500.0, "sx")
        self._add_spinbox("Начало Y, мм:", arc.sy, -500.0, 500.0, "sy")
        self._add_spinbox("Угол, °:", arc.angle, -359.0, 359.0, "angle")
        self._add_spinbox("Толщина, мм:", arc.width, 0.01, 5.0, "width")
        self._add_layers_block([arc.layer], multi=False)

    def _build_text_ui(self, text):
        self._add_spinbox("X, мм:", text.x, -500.0, 500.0, "x")
        self._add_spinbox("Y, мм:", text.y, -500.0, 500.0, "y")
        self._add_spinbox("Размер, мм:", text.size, 0.05, 10.0, "size")

        text_input = QLineEdit(text.text)
        self._add_row("Текст:", text_input, "text")

        visible_check = QCheckBox()
        visible_check.setChecked(text.visible)
        visible_check.setStyleSheet(CHECKBOX_QSS)
        self._add_row("Видимый:", visible_check, "visible")

        self._add_layers_block([text.layer], multi=False)

    def _add_spinbox(self, label, value, min_val, max_val, key):
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(0.01)
        spin.setDecimals(4)
        spin.setValue(value)
        spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self._add_row(label, spin, key)

    def _on_pad_type_changed(self, pad, combo):
        new_type = combo.currentData()
        if new_type == pad.pad_type:
            return
        pad.pad_type = new_type
        pad.layers = default_layers_for_pad_type(new_type)
        layers_table = self._widgets.get("layers_table")
        if layers_table is not None:
            layers_table.set_layers(pad.layers)
        if pad.graphics_item is not None:
            pad.graphics_item.update()

    def _reset_changes(self):
        if self.current_object is not None:
            self.set_object(self.current_object)

    def _apply_changes(self):
        obj = self.current_object
        if not obj:
            return

        if isinstance(obj, Pad):
            self._apply_pad(obj)
        elif isinstance(obj, Line):
            self._apply_line(obj)
        elif isinstance(obj, Circle):
            self._apply_circle(obj)
        elif isinstance(obj, Arc):
            self._apply_arc(obj)
        elif isinstance(obj, Text):
            self._apply_text(obj)

        obj.graphics_item.update_geometry()

    def _apply_pad(self, obj):
        obj.x = self._widgets["x"].value()
        obj.y = self._widgets["y"].value()
        obj.number = self._widgets["number"].text()
        obj.width = self._widgets["width"].value()
        obj.height = self._widgets["height"].value()
        obj.drill = self._widgets["drill"].value()
        obj.shape = self._widgets["shape"].currentData()
        obj.pad_type = self._widgets["pad_type"].currentData()
        new_layers = self._widgets["layers_table"].selected_layers()
        if new_layers:
            obj.layers = new_layers
        obj.graphics_item.setPos(obj.x, obj.y)

    def _apply_line(self, obj):
        obj.x = self._widgets["x"].value()
        obj.y = self._widgets["y"].value()
        obj.x2 = self._widgets["x2"].value()
        obj.y2 = self._widgets["y2"].value()
        obj.width = self._widgets["width"].value()
        self._apply_single_layer(obj)

    def _apply_circle(self, obj):
        obj.x = self._widgets["x"].value()
        obj.y = self._widgets["y"].value()
        obj.radius = self._widgets["diameter"].value() / 2
        obj.width = self._widgets["width"].value()
        self._apply_single_layer(obj)

    def _apply_arc(self, obj):
        obj.x = self._widgets["x"].value()
        obj.y = self._widgets["y"].value()
        obj.sx = self._widgets["sx"].value()
        obj.sy = self._widgets["sy"].value()
        obj.angle = self._widgets["angle"].value()
        obj.width = self._widgets["width"].value()
        self._apply_single_layer(obj)

    def _apply_text(self, obj):
        obj.x = self._widgets["x"].value()
        obj.y = self._widgets["y"].value()
        obj.size = self._widgets["size"].value()
        text_value = self._widgets["text"].text()
        obj.text = text_value if text_value else "Text"
        obj.visible = self._widgets["visible"].isChecked()
        self._apply_single_layer(obj)

    def _apply_single_layer(self, obj):
        layers = self._widgets["layers_table"].selected_layers()
        if layers:
            obj.layer = layers[0]