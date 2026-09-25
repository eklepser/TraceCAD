from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QPushButton)
from footprint_editor.ui.panels.properties_panel import PropertiesPanel
from constants import Styles


PANEL_MIN_WIDTH = 160
PANEL_MAX_WIDTH = 320


class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(PANEL_MIN_WIDTH)
        self.setMaximumWidth(PANEL_MAX_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.tool_group_box = QGroupBox("Инструменты")
        grid = QGridLayout(self.tool_group_box)
        grid.setSpacing(4)

        def make_btn(symbol, tip, checkable=False, checked=False):
            btn = QPushButton(symbol)
            btn.setFixedSize(40, 40)
            btn.setToolTip(tip)
            if checkable:
                btn.setCheckable(True)
                btn.setChecked(checked)
            return btn

        self.btn_select = make_btn("■", "Выделение", checkable=True, checked=True)
        self.btn_select.setStyleSheet(Styles.TOOL_BUTTON_ACTIVE)

        self.btn_add_pad = make_btn("⬤", "Площадка", checkable=True)
        self.btn_add_line = make_btn("╱", "Линия", checkable=True)
        self.btn_add_circle = make_btn("◯", "Окружность", checkable=True)
        self.btn_add_arc = make_btn("◜", "Дуга", checkable=True)
        self.btn_add_text = make_btn("Т", "Текст", checkable=True)

        for btn in (self.btn_add_pad, self.btn_add_line, self.btn_add_circle,
                    self.btn_add_arc, self.btn_add_text):
            btn.setStyleSheet(Styles.TOOL_BUTTON_INACTIVE)

        self.btn_delete = QPushButton("🗑")
        self.btn_delete.setFixedSize(40, 40)
        self.btn_delete.setToolTip("Удалить")
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet(Styles.BUTTON_CANCEL)

        grid.addWidget(self.btn_select, 0, 0)
        grid.addWidget(self.btn_add_pad, 0, 1)
        grid.addWidget(self.btn_add_line, 0, 2)
        grid.addWidget(self.btn_add_circle, 1, 0)
        grid.addWidget(self.btn_add_arc, 1, 1)
        grid.addWidget(self.btn_add_text, 1, 2)
        grid.addWidget(self.btn_delete, 2, 0)

        layout.addWidget(self.tool_group_box)

        self.properties_panel = PropertiesPanel()
        layout.addWidget(self.properties_panel, stretch=1)

    def apply_theme(self):
        self.properties_panel.apply_theme()
        self.btn_delete.setStyleSheet(Styles.BUTTON_CANCEL)

    def update_tool_buttons(self, active_button):
        for btn in (self.btn_add_pad, self.btn_add_line, self.btn_add_circle,
                    self.btn_add_arc, self.btn_add_text, self.btn_select):
            btn.setStyleSheet(Styles.TOOL_BUTTON_ACTIVE if btn == active_button
                              else Styles.TOOL_BUTTON_INACTIVE)