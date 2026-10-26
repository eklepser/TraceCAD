from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QComboBox, QListView,
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                               QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
                               QCheckBox, QAbstractItemView, QSizePolicy)
from PySide6.QtGui import QColor, QPixmap, QIcon
from PySide6.QtCore import Qt, Signal

from constants import Styles
from constants.board_settings import DRAWABLE_LAYERS, LAYER_NAMES_RU
from common.ui.qss import (
    CHECKBOX_QSS, COMBO_VIEW_QSS, TABLE_QSS,
    form_widget_qss, inline_combo_qss,
)
from common.ui.widgets.numeric_line_edit import NumericLineEdit
from pbe_editor.graphics.module_item import BoardModuleGraphicsItem
from pbe_editor.graphics.board_line_item import (
    BoardLineGraphicsItem, BoardCircleGraphicsItem, BoardArcGraphicsItem,
    BoardTextGraphicsItem,
)
from pbe_editor.graphics.ratsnest_item import RatsnestGraphicsItem


def _layer_label(name):
    ru = LAYER_NAMES_RU.get(name)
    return f"{name} ({ru})" if ru else name


class BoardPropertiesPanel(QWidget):
    line_layer_selected = Signal(str)
    module_selected = Signal(object)

    MODE_OBJECT = "object"
    MODE_LINE_LAYER = "line_layer"
    MODE_MODULE_PICKER = "module_picker"

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
        self.form_widget.setStyleSheet(form_widget_qss())
        self.form_widget.setSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Preferred)
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setContentsMargins(8, 8, 8, 8)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.form_layout.setHorizontalSpacing(8)
        self.form_layout.setVerticalSpacing(4)

        self.pins_label = QLabel("Связанные пины:")
        self.pins_label.setStyleSheet("background: transparent; color: #a9b7c6;")
        self.pins_table = QTableWidget(0, 3)
        self.pins_table.setHorizontalHeaderLabels(["Пин", "Цепь", "Код"])
        self.pins_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.pins_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.pins_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.pins_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.pins_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pins_table.verticalHeader().setVisible(False)
        self.pins_table.setStyleSheet(TABLE_QSS)
        self.pins_table.setMinimumHeight(140)
        self.pins_label.hide()
        self.pins_table.hide()

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

        self.line_layers_widget = QWidget()
        ll_layout = QVBoxLayout(self.line_layers_widget)
        ll_layout.setContentsMargins(0, 0, 0, 0)
        ll_layout.setSpacing(4)
        self.line_layers_list = QListWidget()
        self.line_layers_list.setStyleSheet(Styles.LIST_BG)
        self.line_layers_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.line_layers_list.itemClicked.connect(self._on_layer_clicked)
        ll_layout.addWidget(self.line_layers_list)

        self.module_picker_widget = QWidget()
        mp_layout = QVBoxLayout(self.module_picker_widget)
        mp_layout.setContentsMargins(0, 0, 0, 0)
        mp_layout.setSpacing(4)
        self.module_tree = QTreeWidget()
        self.module_tree.setHeaderHidden(True)
        self.module_tree.setStyleSheet(
            "QTreeWidget { background-color: #2b2b2b; color: #a9b7c6;"
            " border: 1px solid #555555; }"
            "QTreeWidget::item:selected { background-color: #365880; color: white; }"
            "QTreeWidget::item:hover { background-color: #3c3f41; }"
        )
        self.module_tree.itemClicked.connect(self._on_module_tree_clicked)
        mp_layout.addWidget(self.module_tree)
        self.libraries_for_picker = {}

        self.main_layout.addWidget(self.header_label)
        self.main_layout.addWidget(self.form_widget)
        self.main_layout.addWidget(self.pins_label)
        self.main_layout.addWidget(self.pins_table)
        self.main_layout.addWidget(self.line_layers_widget)
        self.main_layout.addWidget(self.module_picker_widget)
        self.main_layout.addWidget(self.buttons_widget)
        self.main_layout.addStretch()

        self.header_label.hide()
        self.form_widget.hide()
        self.pins_label.hide()
        self.pins_table.hide()
        self.buttons_widget.hide()
        self.line_layers_widget.hide()
        self.module_picker_widget.hide()

        self.current_object = None
        self._widgets = {}
        self._building = False
        self._mode = self.MODE_OBJECT

    def apply_theme(self):
        self.header_label.setStyleSheet(Styles.SECTION_LABEL)
        self.form_widget.setStyleSheet(form_widget_qss())
        self.btn_apply.setStyleSheet(Styles.APPLY_BUTTON)
        self.btn_reset.setStyleSheet(Styles.BUTTON_CANCEL)
        self.line_layers_list.setStyleSheet(Styles.LIST_BG)
        self.module_tree.setStyleSheet(
            "QTreeWidget { background-color: #2b2b2b; color: #a9b7c6;"
            " border: 1px solid #555555; }"
            "QTreeWidget::item:selected { background-color: #365880; color: white; }"
            "QTreeWidget::item:hover { background-color: #3c3f41; }"
        )

    def show_line_layer_picker(self, current_layer):
        self._set_mode(self.MODE_LINE_LAYER)
        self.header_label.setText("Слой линии")
        self.header_label.show()
        self.line_layers_list.clear()
        selected_item = None
        for name, color in DRAWABLE_LAYERS:
            item = QListWidgetItem(_layer_label(name))
            item.setData(Qt.ItemDataRole.UserRole, name)
            pix = QPixmap(14, 14)
            pix.fill(QColor(*color))
            item.setIcon(QIcon(pix))
            self.line_layers_list.addItem(item)
            if name == current_layer:
                selected_item = item
        if selected_item is not None:
            self.line_layers_list.setCurrentItem(selected_item)
            self.line_layers_list.scrollToItem(selected_item)
        self.line_layers_widget.show()
        self.form_widget.hide()
        self.pins_label.hide()
        self.pins_table.hide()
        self.buttons_widget.hide()
        self.module_picker_widget.hide()

    def show_module_picker(self, libraries):
        self._set_mode(self.MODE_MODULE_PICKER)
        self.header_label.setText("Добавить модуль")
        self.header_label.show()
        self.libraries_for_picker = libraries
        self.module_tree.clear()
        for lib_path, modules in libraries.items():
            lib_item = QTreeWidgetItem([lib_path])
            lib_item.setData(0, Qt.ItemDataRole.UserRole, ("lib", None))
            self.module_tree.addTopLevelItem(lib_item)
            for name, fp in sorted(modules.items()):
                child = QTreeWidgetItem([name])
                child.setData(0, Qt.ItemDataRole.UserRole, ("module", fp))
                lib_item.addChild(child)
        self.module_tree.expandAll()
        self.module_picker_widget.show()
        self.form_widget.hide()
        self.pins_label.hide()
        self.pins_table.hide()
        self.buttons_widget.hide()
        self.line_layers_widget.hide()

    def show_object(self, obj):
        self._set_mode(self.MODE_OBJECT)
        self.setUpdatesEnabled(False)
        try:
            self._building = True
            try:
                while self.form_layout.rowCount() > 0:
                    self.form_layout.removeRow(0)
                self._widgets.clear()
                self.pins_table.setRowCount(0)
            finally:
                self._building = False
            self.current_object = obj
            if isinstance(obj, BoardModuleGraphicsItem):
                self.header_label.setText(f"Модуль {obj.module.reference}")
                self._build_module_ui(obj.module)
                self.pins_label.show()
                self.pins_table.show()
                self.buttons_widget.show()
            elif isinstance(obj, BoardLineGraphicsItem):
                self.header_label.setText(f"Линия {obj.model.layer}")
                self._build_line_ui(obj.model)
                self.pins_label.hide()
                self.pins_table.hide()
                self.buttons_widget.show()
            elif isinstance(obj, BoardCircleGraphicsItem):
                self.header_label.setText(f"Окружность {obj.model.layer}")
                self._build_circle_ui(obj.model)
                self.pins_label.hide()
                self.pins_table.hide()
                self.buttons_widget.show()
            elif isinstance(obj, BoardArcGraphicsItem):
                self.header_label.setText(f"Дуга {obj.model.layer}")
                self._build_arc_ui(obj.model)
                self.pins_label.hide()
                self.pins_table.hide()
                self.buttons_widget.show()
            elif isinstance(obj, BoardTextGraphicsItem):
                self.header_label.setText(f"Текст {obj.model.layer}")
                self._build_text_ui(obj.model)
                self.pins_label.hide()
                self.pins_table.hide()
                self.buttons_widget.show()
            elif isinstance(obj, RatsnestGraphicsItem):
                self.header_label.setText(f"Связь #{obj.net_code}")
                self._build_ratsnest_ui(obj)
                self.pins_label.hide()
                self.pins_table.hide()
                self.buttons_widget.hide()
            else:
                self.clear_panel()
                return
            self.header_label.show()
            self.form_widget.show()
            self.line_layers_widget.hide()
            self.module_picker_widget.hide()
            self.main_layout.invalidate()
        finally:
            self.setUpdatesEnabled(True)
            self.updateGeometry()
            self.update()

    def clear_panel(self):
        self.current_object = None
        self._set_mode(self.MODE_OBJECT)
        self.header_label.hide()
        self.form_widget.hide()
        self.pins_label.hide()
        self.pins_table.hide()
        self.buttons_widget.hide()
        self.line_layers_widget.hide()
        self.module_picker_widget.hide()
        self.header_label.setText("")
        self.pins_table.setRowCount(0)
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self._widgets.clear()

    def _set_mode(self, mode):
        self._mode = mode
        if mode == self.MODE_OBJECT:
            self.line_layers_widget.hide()
            self.module_picker_widget.hide()
        elif mode == self.MODE_LINE_LAYER:
            self.module_picker_widget.hide()
        elif mode == self.MODE_MODULE_PICKER:
            self.line_layers_widget.hide()

    def _on_layer_clicked(self, item):
        name = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self.line_layer_selected.emit(name)

    def _on_module_tree_clicked(self, item, column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        kind, payload = data
        if kind == "module" and payload is not None:
            self.module_selected.emit(payload)

    def refresh_values(self):
        obj = self.current_object
        if not obj or self._building or self._mode != self.MODE_OBJECT:
            return
        self.setUpdatesEnabled(False)
        try:
            if isinstance(obj, BoardModuleGraphicsItem):
                m = obj.module
                self._widgets["x"].setValue(m.x)
                self._widgets["y"].setValue(m.y)
                self._widgets["angle"].setValue(m.angle)
                self._widgets["name"].setText(m.reference)
                self._widgets["value"].setText(m.value)
            elif isinstance(obj, BoardLineGraphicsItem):
                l = obj.model
                self._widgets["x1"].setValue(l.x1)
                self._widgets["y1"].setValue(l.y1)
                self._widgets["x2"].setValue(l.x2)
                self._widgets["y2"].setValue(l.y2)
                self._widgets["width"].setValue(l.width)
            elif isinstance(obj, BoardCircleGraphicsItem):
                c = obj.model
                self._widgets["x"].setValue(c.x)
                self._widgets["y"].setValue(c.y)
                self._widgets["radius"].setValue(c.radius)
                self._widgets["width"].setValue(c.width)
            elif isinstance(obj, BoardArcGraphicsItem):
                a = obj.model
                self._widgets["x"].setValue(a.x)
                self._widgets["y"].setValue(a.y)
                self._widgets["sx"].setValue(a.sx)
                self._widgets["sy"].setValue(a.sy)
                self._widgets["angle"].setValue(a.angle)
                self._widgets["width"].setValue(a.width)
        finally:
            self.setUpdatesEnabled(True)

    def _make_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("background: transparent; color: #a9b7c6;")
        label.setMinimumWidth(90)
        return label

    def _add_row(self, label_text, field_widget, key):
        self.form_layout.addRow(self._make_label(label_text), field_widget)
        self._widgets[key] = field_widget

    def _add_spinbox(self, label, value, min_val, max_val, key, step=0.01, decimals=4, readonly=False):
        le = NumericLineEdit(value, decimals, min_val, max_val)
        le.setReadOnly(readonly)
        self._add_row(label, le, key)

    def _make_combo(self, items, current_index=0):
        combo = QComboBox()
        for label, data in items:
            combo.addItem(label, data)
        combo.setCurrentIndex(current_index)
        view = QListView()
        view.setStyleSheet(COMBO_VIEW_QSS)
        combo.setView(view)
        combo.setMinimumWidth(100)
        combo.setMinimumHeight(24)
        combo.setStyleSheet(inline_combo_qss())
        return combo

    def _line_layer_combo(self, layer):
        choices = [(_layer_label(n), n) for n, _ in DRAWABLE_LAYERS]
        idx = 0
        for i, (_, data) in enumerate(choices):
            if data == layer:
                idx = i
                break
        return self._make_combo(choices, idx)

    def _build_module_ui(self, module):
        self._add_spinbox("X, мм:", module.x, -100000.0, 100000.0, "x")
        self._add_spinbox("Y, мм:", module.y, -100000.0, 100000.0, "y")
        self._add_spinbox("Угол, °:", module.angle, -359.0, 359.0, "angle", decimals=1)
        name_input = QLineEdit(module.reference)
        name_input.setMinimumWidth(100)
        name_input.setMinimumHeight(24)
        self._add_row("Имя:", name_input, "name")
        val_input = QLineEdit(module.value)
        val_input.setMinimumWidth(100)
        val_input.setMinimumHeight(24)
        self._add_row("Значение:", val_input, "value")
        self._add_row("Слой:", self._make_combo(
            [("F.Cu", "F.Cu"), ("B.Cu", "B.Cu")],
            0 if module.layer == "F.Cu" else 1,
        ), "layer")
        fp_input = QLineEdit(module.footprint.name)
        fp_input.setReadOnly(True)
        fp_input.setMinimumWidth(100)
        fp_input.setMinimumHeight(24)
        self._add_row("Корпус:", fp_input, "footprint")
        self._fill_pins_table(module)

    def _fill_pins_table(self, module):
        nets = module.pad_nets
        self.pins_table.setRowCount(0)
        for pad in module.footprint.pads:
            row = self.pins_table.rowCount()
            self.pins_table.insertRow(row)
            self.pins_table.setItem(row, 0, QTableWidgetItem(f"{module.reference}.{pad.number}"))
            pad_net = nets.get(pad.number)
            self.pins_table.setItem(row, 1, QTableWidgetItem(pad_net.net_name if pad_net else ""))
            self.pins_table.setItem(row, 2, QTableWidgetItem(str(pad_net.net_code) if pad_net else ""))

    def _build_line_ui(self, line):
        self._add_spinbox("X1, мм:", line.x1, -100000.0, 100000.0, "x1")
        self._add_spinbox("Y1, мм:", line.y1, -100000.0, 100000.0, "y1")
        self._add_spinbox("X2, мм:", line.x2, -100000.0, 100000.0, "x2")
        self._add_spinbox("Y2, мм:", line.y2, -100000.0, 100000.0, "y2")
        self._add_spinbox("Толщина, мм:", line.width, 0.01, 5.0, "width")
        self._add_row("Слой:", self._line_layer_combo(line.layer), "layer")

    def _build_circle_ui(self, circle):
        self._add_spinbox("Центр X, мм:", circle.x, -100000.0, 100000.0, "x")
        self._add_spinbox("Центр Y, мм:", circle.y, -100000.0, 100000.0, "y")
        self._add_spinbox("Радиус, мм:", circle.radius, 0.01, 10000.0, "radius")
        self._add_spinbox("Толщина, мм:", circle.width, 0.01, 5.0, "width")
        self._add_row("Слой:", self._line_layer_combo(circle.layer), "layer")

    def _build_arc_ui(self, arc):
        self._add_spinbox("Центр X, мм:", arc.x, -100000.0, 100000.0, "x")
        self._add_spinbox("Центр Y, мм:", arc.y, -100000.0, 100000.0, "y")
        self._add_spinbox("Начало X, мм:", arc.sx, -100000.0, 100000.0, "sx")
        self._add_spinbox("Начало Y, мм:", arc.sy, -100000.0, 100000.0, "sy")
        self._add_spinbox("Угол, °:", arc.angle, -359.0, 359.0, "angle")
        self._add_spinbox("Толщина, мм:", arc.width, 0.01, 5.0, "width")
        self._add_row("Слой:", self._line_layer_combo(arc.layer), "layer")

    def _build_text_ui(self, text):
        self._add_spinbox("X, мм:", text.x, -100000.0, 100000.0, "x")
        self._add_spinbox("Y, мм:", text.y, -100000.0, 100000.0, "y")
        self._add_spinbox("Размер, мм:", text.size, 0.05, 50.0, "size")
        text_input = QLineEdit(text.text)
        text_input.setMinimumWidth(100)
        text_input.setMinimumHeight(24)
        self._add_row("Текст:", text_input, "text")
        visible = QCheckBox(); visible.setChecked(text.visible); visible.setStyleSheet(CHECKBOX_QSS)
        self._add_row("Видимый:", visible, "visible")
        self._add_row("Слой:", self._line_layer_combo(text.layer), "layer")

    def _build_ratsnest_ui(self, item):
        code_input = QLineEdit(str(item.net_code)); code_input.setReadOnly(True)
        code_input.setMinimumWidth(100); code_input.setMinimumHeight(24)
        self._add_row("Код цепи:", code_input, "net_code")
        name_input = QLineEdit(item.net_name); name_input.setReadOnly(True)
        name_input.setMinimumWidth(100); name_input.setMinimumHeight(24)
        self._add_row("Имя цепи:", name_input, "net_name")
        a_input = QLineEdit(item.label_a); a_input.setReadOnly(True)
        a_input.setMinimumWidth(100); a_input.setMinimumHeight(24)
        self._add_row("Пин A:", a_input, "label_a")
        b_input = QLineEdit(item.label_b); b_input.setReadOnly(True)
        b_input.setMinimumWidth(100); b_input.setMinimumHeight(24)
        self._add_row("Пин B:", b_input, "label_b")
        if item.is_gnd:
            power_text = "GND"
        elif item.is_power:
            power_text = "Питание"
        else:
            power_text = "Нет"
        p_input = QLineEdit(power_text); p_input.setReadOnly(True)
        p_input.setMinimumWidth(100); p_input.setMinimumHeight(24)
        self._add_row("Тип цепи:", p_input, "is_power")

    def _reset_changes(self):
        if self.current_object is not None:
            self.show_object(self.current_object)

    def _apply_changes(self):
        obj = self.current_object
        if not obj:
            return
        if isinstance(obj, BoardModuleGraphicsItem):
            m = obj.module
            m.x = self._widgets["x"].value()
            m.y = self._widgets["y"].value()
            m.angle = self._widgets["angle"].value()
            m.reference = self._widgets["name"].text()
            m.value = self._widgets["value"].text()
            m.layer = self._widgets["layer"].currentData()
            obj.setPos(m.x, m.y)
            obj.setRotation(m.angle)
            obj.prepareGeometryChange()
            obj.update()
            if hasattr(obj.canvas, 'ratsnest_update_requested'):
                obj.canvas.ratsnest_update_requested.emit()
        elif isinstance(obj, BoardLineGraphicsItem):
            l = obj.model
            l.x1 = self._widgets["x1"].value()
            l.y1 = self._widgets["y1"].value()
            l.x2 = self._widgets["x2"].value()
            l.y2 = self._widgets["y2"].value()
            l.width = self._widgets["width"].value()
            l.layer = self._widgets["layer"].currentData()
            obj.setPos(l.x1, l.y1)
            obj.prepareGeometryChange(); obj.update()
        elif isinstance(obj, BoardCircleGraphicsItem):
            c = obj.model
            c.x = self._widgets["x"].value()
            c.y = self._widgets["y"].value()
            c.radius = self._widgets["radius"].value()
            c.width = self._widgets["width"].value()
            c.layer = self._widgets["layer"].currentData()
            obj.setPos(c.x, c.y)
            obj.prepareGeometryChange(); obj.update()
        elif isinstance(obj, BoardArcGraphicsItem):
            a = obj.model
            a.x = self._widgets["x"].value()
            a.y = self._widgets["y"].value()
            a.sx = self._widgets["sx"].value()
            a.sy = self._widgets["sy"].value()
            a.angle = self._widgets["angle"].value()
            a.width = self._widgets["width"].value()
            a.layer = self._widgets["layer"].currentData()
            obj.setPos(a.x, a.y)
            obj.prepareGeometryChange(); obj.update()
        elif isinstance(obj, BoardTextGraphicsItem):
            t = obj.model
            t.x = self._widgets["x"].value()
            t.y = self._widgets["y"].value()
            t.size = self._widgets["size"].value()
            t.text = self._widgets["text"].text() or "Text"
            t.visible = self._widgets["visible"].isChecked()
            t.layer = self._widgets["layer"].currentData()
            obj.setPos(t.x, t.y)
            obj.prepareGeometryChange(); obj.update()