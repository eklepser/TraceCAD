from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel,
                               QDoubleSpinBox, QLineEdit, QComboBox, QListView,
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt

from constants import Styles
from pbe_editor.graphics.module_item import BoardModuleGraphicsItem
from pbe_editor.graphics.ratsnest_item import RatsnestGraphicsItem


class BoardPropertiesPanel(QWidget):
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
        self.pins_table.setStyleSheet(
            "QTableWidget { background-color: #1e1e1e; color: #cfcfcf;"
            " gridline-color: #3c3f41; border: 1px solid #3c3f41; }"
            "QHeaderView::section { background-color: #2b2b2b; color: #a9b7c6;"
            " border: 0px; border-right: 1px solid #3c3f41; padding: 4px; }"
        )
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

        self.main_layout.addWidget(self.header_label)
        self.main_layout.addWidget(self.form_widget)
        self.main_layout.addWidget(self.pins_label)
        self.main_layout.addWidget(self.pins_table)
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
        self.pins_table.setStyleSheet(
            "QTableWidget { background-color: #1e1e1e; color: #cfcfcf;"
            " gridline-color: #3c3f41; border: 1px solid #3c3f41; }"
            "QHeaderView::section { background-color: #2b2b2b; color: #a9b7c6;"
            " border: 0px; border-right: 1px solid #3c3f41; padding: 4px; }"
        )

    def clear_panel(self):
        self.setUpdatesEnabled(False)
        try:
            while self.form_layout.rowCount() > 0:
                self.form_layout.removeRow(0)
            self._widgets.clear()
            self.current_object = None
            self.header_label.hide()
            self.form_widget.hide()
            self.pins_label.hide()
            self.pins_table.hide()
            self.buttons_widget.hide()
            self.header_label.setText("")
            self.pins_table.setRowCount(0)
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
                self.pins_table.setRowCount(0)
            finally:
                self._building = False

            self.current_object = obj

            if isinstance(obj, BoardModuleGraphicsItem):
                module = obj.module
                self.header_label.setText(f"Модуль {module.reference}")
                self._build_module_ui(module)
                self.pins_label.show()
                self.pins_table.show()
                self.buttons_widget.show()
            elif isinstance(obj, RatsnestGraphicsItem):
                self.header_label.setText(f"Связь #{obj.net_code}")
                self._build_ratsnest_ui(obj)
                self.pins_label.hide()
                self.pins_table.hide()
                self.buttons_widget.hide()
            else:
                self.header_label.hide()
                self.form_widget.hide()
                self.pins_label.hide()
                self.pins_table.hide()
                self.buttons_widget.hide()
                self.current_object = None
                return

            self.header_label.show()
            self.form_widget.show()
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
            if isinstance(obj, BoardModuleGraphicsItem):
                module = obj.module
                self._widgets["x"].setValue(module.x)
                self._widgets["y"].setValue(module.y)
                self._widgets["angle"].setValue(module.angle)
                self._widgets["name"].setText(module.reference)
                self._widgets["value"].setText(module.value)
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

    def _add_spinbox(self, label, value, min_val, max_val, key, step=0.01, decimals=4, readonly=False):
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(step)
        spin.setDecimals(decimals)
        spin.setValue(value)
        spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        spin.setReadOnly(readonly)
        self._add_row(label, spin, key)

    def _make_combo(self, items, current_index=0):
        combo = QComboBox()
        for label, data in items:
            combo.addItem(label, data)
        combo.setCurrentIndex(current_index)
        view = QListView()
        view.setStyleSheet(
            "QListView { background-color: #2b2b2b; color: #a9b7c6;"
            " border: 1px solid #555555; outline: 0; }"
            "QListView::item { padding: 4px 8px; }"
            "QListView::item:selected {"
            "  background-color: #365880; color: white; }"
        )
        view.setMinimumWidth(140)
        combo.setView(view)
        combo.setStyleSheet(
            "QComboBox { background: transparent; color: #ffffff;"
            " border: none; border-bottom: 1px solid #555555;"
            " padding: 2px 2px; }"
            " QComboBox:hover { border-bottom: 1px solid #7a7a7a; }"
            " QComboBox:focus { border-bottom: 1px solid #365880; }"
            " QComboBox::drop-down { border: none; width: 14px; }"
        )
        return combo

    def _build_module_ui(self, module):
        self._add_spinbox("X, мм:", module.x, -10000.0, 10000.0, "x")
        self._add_spinbox("Y, мм:", module.y, -10000.0, 10000.0, "y")
        self._add_spinbox("Угол, °:", module.angle, -359.0, 359.0, "angle",
                          step=1.0, decimals=1)

        name_input = QLineEdit(module.reference)
        self._add_row("Имя:", name_input, "name")

        val_input = QLineEdit(module.value)
        self._add_row("Значение:", val_input, "value")

        layer_combo = self._make_combo(
            [("F.Cu", "F.Cu"), ("B.Cu", "B.Cu")],
            0 if module.layer == "F.Cu" else 1,
        )
        self._add_row("Слой:", layer_combo, "layer")

        fp_input = QLineEdit(module.footprint.name)
        fp_input.setReadOnly(True)
        self._add_row("Корпус:", fp_input, "footprint")

        self._fill_pins_table(module)

    def _fill_pins_table(self, module):
        nets = module.pad_nets
        self.pins_table.setRowCount(0)
        for pad in module.footprint.pads:
            row = self.pins_table.rowCount()
            self.pins_table.insertRow(row)
            pad_item = QTableWidgetItem(f"{module.reference}.{pad.number}")
            self.pins_table.setItem(row, 0, pad_item)

            pad_net = nets.get(pad.number)
            net_name = pad_net.net_name if pad_net else ""
            net_code = str(pad_net.net_code) if pad_net else ""

            self.pins_table.setItem(row, 1, QTableWidgetItem(net_name))
            self.pins_table.setItem(row, 2, QTableWidgetItem(net_code))

    def _build_ratsnest_ui(self, item):
        code_input = QLineEdit(str(item.net_code))
        code_input.setReadOnly(True)
        self._add_row("Код цепи:", code_input, "net_code")

        name_input = QLineEdit(item.net_name)
        name_input.setReadOnly(True)
        self._add_row("Имя цепи:", name_input, "net_name")

        a_input = QLineEdit(item.label_a)
        a_input.setReadOnly(True)
        self._add_row("Пин A:", a_input, "label_a")

        b_input = QLineEdit(item.label_b)
        b_input.setReadOnly(True)
        self._add_row("Пин B:", b_input, "label_b")

        if item.is_gnd:
            power_text = "GND"
        elif item.is_power:
            power_text = "Питание"
        else:
            power_text = "Нет"
        power_input = QLineEdit(power_text)
        power_input.setReadOnly(True)
        self._add_row("Тип цепи:", power_input, "is_power")

    def _reset_changes(self):
        if self.current_object is not None:
            self.set_object(self.current_object)

    def _apply_changes(self):
        obj = self.current_object
        if not obj:
            return

        if isinstance(obj, BoardModuleGraphicsItem):
            self._apply_module(obj)

    def _apply_module(self, item):
        module = item.module
        module.x = self._widgets["x"].value()
        module.y = self._widgets["y"].value()
        module.angle = self._widgets["angle"].value()
        module.reference = self._widgets["name"].text()
        module.value = self._widgets["value"].text()
        module.layer = self._widgets["layer"].currentData()

        item.setPos(module.x, module.y)
        item.setRotation(module.angle)
        item.prepareGeometryChange()
        item.update()

        if hasattr(item.canvas, 'ratsnest_update_requested'):
            item.canvas.ratsnest_update_requested.emit()