from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QPushButton)
from footprint_editor.ui.properties_panel import PropertiesPanel
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
        tool_layout = QGridLayout(self.tool_group_box)
        tool_layout.setSpacing(4)

        self.btn_select = QPushButton("■")
        self.btn_select.setFixedSize(40, 40)
        self.btn_select.setToolTip("Выделение")
        self.btn_select.setCheckable(True)
        self.btn_select.setChecked(True)
        self.btn_select.setStyleSheet(Styles.TOOL_BUTTON_ACTIVE)

        self.btn_add_pad = QPushButton("⬤")
        self.btn_add_pad.setFixedSize(40, 40)
        self.btn_add_pad.setToolTip("Площадка")
        self.btn_add_pad.setCheckable(True)
        self.btn_add_pad.setStyleSheet(Styles.TOOL_BUTTON_INACTIVE)

        self.btn_add_line = QPushButton("╱")
        self.btn_add_line.setFixedSize(40, 40)
        self.btn_add_line.setToolTip("Линия")
        self.btn_add_line.setCheckable(True)
        self.btn_add_line.setStyleSheet(Styles.TOOL_BUTTON_INACTIVE)

        self.btn_add_circle = QPushButton("◯")
        self.btn_add_circle.setFixedSize(40, 40)
        self.btn_add_circle.setToolTip("Окружность")
        self.btn_add_circle.setCheckable(True)
        self.btn_add_circle.setStyleSheet(Styles.TOOL_BUTTON_INACTIVE)

        self.btn_add_arc = QPushButton("◜")
        self.btn_add_arc.setFixedSize(40, 40)
        self.btn_add_arc.setToolTip("Дуга")
        self.btn_add_arc.setCheckable(True)
        self.btn_add_arc.setStyleSheet(Styles.TOOL_BUTTON_INACTIVE)

        self.btn_add_text = QPushButton("Т")
        self.btn_add_text.setFixedSize(40, 40)
        self.btn_add_text.setToolTip("Текст")
        self.btn_add_text.setCheckable(True)
        self.btn_add_text.setStyleSheet(Styles.TOOL_BUTTON_INACTIVE)

        self.btn_delete = QPushButton("🗑")
        self.btn_delete.setFixedSize(40, 40)
        self.btn_delete.setToolTip("Удалить")
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet(Styles.BUTTON_CANCEL)

        tool_layout.addWidget(self.btn_select, 0, 0)
        tool_layout.addWidget(self.btn_add_pad, 0, 1)
        tool_layout.addWidget(self.btn_add_line, 0, 2)
        tool_layout.addWidget(self.btn_add_circle, 1, 0)
        tool_layout.addWidget(self.btn_add_arc, 1, 1)
        tool_layout.addWidget(self.btn_add_text, 1, 2)
        tool_layout.addWidget(self.btn_delete, 2, 0)

        layout.addWidget(self.tool_group_box)

        self.properties_panel = PropertiesPanel()
        layout.addWidget(self.properties_panel, stretch=1)

    def apply_theme(self):
        self.properties_panel.apply_theme()
        self.btn_delete.setStyleSheet(Styles.BUTTON_CANCEL)

    def update_tool_buttons(self, active_button):
        buttons = [self.btn_add_pad, self.btn_add_line, self.btn_add_circle,
                   self.btn_add_arc, self.btn_add_text, self.btn_select]
        for btn in buttons:
            if btn == active_button:
                btn.setStyleSheet(Styles.TOOL_BUTTON_ACTIVE)
            else:
                btn.setStyleSheet(Styles.TOOL_BUTTON_INACTIVE)