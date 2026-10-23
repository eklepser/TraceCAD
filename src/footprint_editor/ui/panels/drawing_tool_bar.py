from pathlib import Path
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, Qt, QSize
from constants import Styles, Tool


ICONS_DIR = Path(__file__).resolve().parent.parent.parent / "resources" / "icons"

TOOL_BUTTONS = [
    (Tool.ADD_LINE, "line", "╱", "Линия (1)"),
    (Tool.ADD_PAD, "pad", "⬤", "Площадка (2)"),
    (Tool.ADD_CIRCLE, "circle", "◯", "Окружность (3)"),
    (Tool.ADD_ARC, "arc", "◜", "Дуга (4)"),
    (Tool.ADD_TEXT, "text", "Т", "Текст (5)"),
]

BUTTON_SIZE = 40


def _load_icon(name):
    path = ICONS_DIR / f"{name}.svg"
    if path.exists():
        return QIcon(str(path))
    return QIcon()


class DrawingToolBar(QWidget):
    tool_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self.buttons = {}
        self._active = Tool.ADD_LINE

        for tool, icon_name, fallback, tip in TOOL_BUTTONS:
            btn = QPushButton()
            icon = _load_icon(icon_name)
            if not icon.isNull():
                btn.setIcon(icon)
                btn.setIconSize(QSize(24, 24))
            else:
                btn.setText(fallback)
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
        if tool is None:
            self._active = None
        else:
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