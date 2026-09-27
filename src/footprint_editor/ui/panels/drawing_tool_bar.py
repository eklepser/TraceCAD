from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal, Qt
from constants import Styles, Tool


TOOL_BUTTONS = [
    (Tool.ADD_LINE, "╱", "Линия (1)"),
    (Tool.ADD_PAD, "⬤", "Площадка (2)"),
    (Tool.ADD_CIRCLE, "◯", "Окружность (3)"),
    (Tool.ADD_ARC, "◜", "Дуга (4)"),
    (Tool.ADD_TEXT, "Т", "Текст (5)"),
]


BUTTON_SIZE = 40


class DrawingToolBar(QWidget):
    tool_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self.buttons = {}
        self._active = Tool.ADD_LINE

        for tool, symbol, tip in TOOL_BUTTONS:
            btn = QPushButton(symbol)
            btn.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
            btn.setToolTip(tip)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, t=tool: self._on_clicked(t))
            layout.addWidget(btn)
            self.buttons[tool] = btn

        layout.addStretch()
        self.setObjectName("DrawingToolBar")
        self.setStyleSheet(
            "QWidget#DrawingToolBar { background-color: #2b2b2b;"
            " border-top: 1px solid #1e1e1e; }"
        )
        self._update_styles()

    def _on_clicked(self, tool):
        self.set_active(tool)
        self.tool_selected.emit(tool)

    def set_active(self, tool):
        self._active = tool
        self._update_styles()

    def _update_styles(self):
        for tool, btn in self.buttons.items():
            btn.setChecked(tool == self._active)
            btn.setStyleSheet(Styles.TOOL_BUTTON_ACTIVE if tool == self._active
                              else Styles.TOOL_BUTTON_INACTIVE)

    def apply_theme(self):
        self._update_styles()