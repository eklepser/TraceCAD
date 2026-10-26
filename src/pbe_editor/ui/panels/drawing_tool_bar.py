from pathlib import Path
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, Qt
from constants import Styles


class BoardTool:
    SELECT = "select"
    ADD_LINE = "add_line"
    ADD_CIRCLE = "add_circle"
    ADD_ARC = "add_arc"
    ADD_TEXT = "add_text"
    ADD_MODULE = "add_module"
    ADD_NET = "add_net"


TOOL_BUTTONS = [
    (BoardTool.ADD_LINE, "╱", "Линия (1)"),
    (BoardTool.ADD_CIRCLE, "◯", "Окружность (2)"),
    (BoardTool.ADD_ARC, "◜", "Дуга (3)"),
    (BoardTool.ADD_TEXT, "Т", "Текст (4)"),
    (BoardTool.ADD_MODULE, "⬛", "Добавить модуль (5)"),
    (BoardTool.ADD_NET, "→", "Соединить выводы (6)"),
]

ICONS_DIR = Path(__file__).resolve().parent.parent.parent / "resources" / "icons"
BUTTON_SIZE = 40


def _load_icon(name):
    path = ICONS_DIR / f"{name}.svg"
    if path.exists():
        return QIcon(str(path))
    return QIcon()


class BoardDrawingToolBar(QWidget):
    tool_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self.buttons = {}
        self._active = None

        for tool, fallback, tip in TOOL_BUTTONS:
            btn = QPushButton(fallback)
            btn.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
            btn.setToolTip(tip)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, t=tool: self._on_clicked(t))
            layout.addWidget(btn)
            self.buttons[tool] = btn

        layout.addStretch()
        self.setObjectName("BoardDrawingToolBar")
        self.setStyleSheet(
            "QWidget#BoardDrawingToolBar { background-color: #2b2b2b;"
            " border-top: 1px solid #1e1e1e; }"
        )
        self._update_styles()

    def _on_clicked(self, tool):
        self.set_active(tool)
        self.tool_selected.emit(tool)

    def set_active(self, tool):
        self._active = tool
        self._update_styles()

    def clear_active(self):
        self._active = None
        self._update_styles()

    def _update_styles(self):
        for tool, btn in self.buttons.items():
            is_active = (self._active == tool)
            btn.setChecked(is_active)
            btn.setStyleSheet(Styles.TOOL_BUTTON_ACTIVE if is_active
                              else Styles.TOOL_BUTTON_INACTIVE)

    def apply_theme(self):
        self._update_styles()