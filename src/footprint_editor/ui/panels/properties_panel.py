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
    "QCheckBox::indicator:hover { border: 1px solid }"
    "QCheckBox::indicator:checked {"
    " border: 1px solid #ffffff; background-color: #2b2b2b; }"
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
        self.header_label.hide()
        self.main_layout.addWidget(self.header_label)

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
        self.main_layout.addWidget(self.form_widget)

        btns = QHBoxLayout()
        btns.setSpacing(6)

        self.btn_reset = QPushButton("Отменить")
        self.btn_reset.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_reset.clicked.connect(self._reset_changes)

        self.btn_apply = QPushButton("Применить")
        self.btn_apply.setStyleSheet(Styles.APPLY_BUTTON)
        self.btn_apply.clicked.connect(self._apply_changes)

        btns.addWidget(self.btn_reset)
        btns.addWidget(self.btn_apply)
        self.main_layout.addLayout(btns)
        self.main_layout.addStretch()

        self.current_object = None
        self._widgets = {}
        self.form_widget.hide()
        self.btn_apply.hide()
        self.btn_reset.hide()

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
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self._widgets.clear()
        self.current_object = None
        self.form_widget.hide()
        self.btn_apply.hide()
        self.btn_reset.hide()
        self.header_label.hide()
        self.header_label.setText("")

    def set_object(self, obj):
        self.clear_panel()
        self.current_object = obj
        self.form_widget.show()
        self.btn_apply.show()
        self.btn_reset.show()

        type_name = TYPE_NAMES_RU.get(type(obj), "Объект")
        self.header_label.setText(f"{type_name} #{obj.uid}")
        self.header_label.show()

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
        # Заголовок "Слои:" отдельной строкой
        header = QLabel("Слои:")
        header.setStyleSheet("background: transparent; color: #a9b7c6;")
        self.form_layout.addRow(header)

        # Сама таблица — на следующей строке, растянута по всей ширине формы
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

    def _make_pad_type_combo(self, current_type):
        combo = QComboBox()
        for ptype in PAD_TYPE_ORDER:
            combo.addItem(PAD_TYPE_NAMES[ptype], ptype)
        idx = PAD_TYPE_ORDER.index(current_type) if current_type in PAD_TYPE_ORDER else 0
        combo.setCurrentIndex(idx)
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
        pad_type_combo = self._make_pad_type_combo(pad.pad_type)
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

        shape_combo = QComboBox()
        shape_combo.addItem("Круг", PadShape.CIRCLE)
        shape_combo.addItem("Квадрат", PadShape.RECT)
        shape_combo.setCurrentIndex(0 if pad.shape == PadShape.CIRCLE else 1)
        shape_combo.setView(self._make_combo_view())
        shape_combo.setStyleSheet(
            "QComboBox { background: transparent; color: #ffffff;"
            " border: none; border-bottom: 1px solid #555555;"
            " padding: 2px 2px; }"
            " QComboBox:hover { border-bottom: 1px solid #7a7a7a; }"
            " QComboBox:focus { border-bottom: 1px solid #365880; }"
            " QComboBox::drop-down { border: none; width: 14px; }"
        )
        self._add_row("Форма:", shape_combo, "shape")

        self._add_layers_block(pad.layers, multi=True)

    def _build_line_ui(self, line):
        self._add_spinbox("X1, мм:", line.x1, -500.0, 500.0, "x1")
        self._add_spinbox("Y1, мм:", line.y1, -500.0, 500.0, "y1")
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
        self._add_spinbox("Центр X, мм:", arc.cx, -500.0, 500.0, "cx")
        self._add_spinbox("Центр Y, мм:", arc.cy, -500.0, 500.0, "cy")
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
        elif isinstance(obj, Line):
            obj.x1 = self._widgets["x1"].value()
            obj.y1 = self._widgets["y1"].value()
            obj.x2 = self._widgets["x2"].value()
            obj.y2 = self._widgets["y2"].value()
            obj.width = self._widgets["width"].value()
            layers = self._widgets["layers_table"].selected_layers()
            if layers:
                obj.layer = layers[0]
        elif isinstance(obj, Circle):
            obj.x = self._widgets["x"].value()
            obj.y = self._widgets["y"].value()
            obj.radius = self._widgets["diameter"].value() / 2
            obj.width = self._widgets["width"].value()
            layers = self._widgets["layers_table"].selected_layers()
            if layers:
                obj.layer = layers[0]
        elif isinstance(obj, Arc):
            obj.cx = self._widgets["cx"].value()
            obj.cy = self._widgets["cy"].value()
            obj.sx = self._widgets["sx"].value()
            obj.sy = self._widgets["sy"].value()
            obj.angle = self._widgets["angle"].value()
            obj.width = self._widgets["width"].value()
            layers = self._widgets["layers_table"].selected_layers()
            if layers:
                obj.layer = layers[0]
        elif isinstance(obj, Text):
            obj.x = self._widgets["x"].value()
            obj.y = self._widgets["y"].value()
            obj.size = self._widgets["size"].value()
            text_value = self._widgets["text"].text()
            obj.text = text_value if text_value else "Text"
            obj.visible = self._widgets["visible"].isChecked()
            layers = self._widgets["layers_table"].selected_layers()
            if layers:
                obj.layer = layers[0]

        obj.graphics_item.update_geometry()