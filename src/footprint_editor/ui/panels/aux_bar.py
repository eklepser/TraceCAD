from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal, Qt
from constants import Styles


BUTTON_SIZE = 40


class AuxBar(QWidget):
    undo_requested = Signal()
    redo_requested = Signal()
    select_requested = Signal()
    delete_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self.btn_undo = self._make_button("↶", "Отменить (Ctrl+Z)")
        self.btn_undo.clicked.connect(self.undo_requested.emit)
        layout.addWidget(self.btn_undo)

        self.btn_redo = self._make_button("↷", "Повторить (Ctrl+Shift+Z)")
        self.btn_redo.clicked.connect(self.redo_requested.emit)
        layout.addWidget(self.btn_redo)

        self.btn_select = self._make_button("■", "Выделение (Esc)", checkable=True)
        self.btn_select.clicked.connect(self.select_requested.emit)
        layout.addWidget(self.btn_select)

        self.btn_delete = self._make_button("🗑", "Удалить (Del)")
        self.btn_delete.clicked.connect(self.delete_requested.emit)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

        self.setObjectName("AuxBar")
        self.setStyleSheet(Styles.AUX_BAR)
        self.set_select_active(True)
        self.set_delete_enabled(False)

    def _make_button(self, symbol, tip, checkable=False):
        btn = QPushButton(symbol)
        btn.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        btn.setToolTip(tip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if checkable:
            btn.setCheckable(True)
        return btn

    def apply_theme(self):
        self.setStyleSheet(Styles.AUX_BAR)
        self._refresh()

    def set_undo_enabled(self, enabled):
        self.btn_undo.setEnabled(enabled)
        self.btn_undo.setStyleSheet(
            Styles.TOOL_BUTTON_INACTIVE if enabled else Styles.BUTTON_DISABLED
        )

    def set_redo_enabled(self, enabled):
        self.btn_redo.setEnabled(enabled)
        self.btn_redo.setStyleSheet(
            Styles.TOOL_BUTTON_INACTIVE if enabled else Styles.BUTTON_DISABLED
        )

    def set_select_active(self, active):
        self.btn_select.setChecked(active)
        self.btn_select.setStyleSheet(
            Styles.TOOL_BUTTON_ACTIVE if active else Styles.TOOL_BUTTON_INACTIVE
        )

    def set_delete_enabled(self, enabled):
        self.btn_delete.setEnabled(enabled)
        self.btn_delete.setStyleSheet(
            Styles.TOOL_BUTTON_INACTIVE if enabled else Styles.BUTTON_DISABLED
        )

    def _refresh(self):
        self.set_undo_enabled(self.btn_undo.isEnabled())
        self.set_redo_enabled(self.btn_redo.isEnabled())
        self.set_select_active(self.btn_select.isChecked())
        self.set_delete_enabled(self.btn_delete.isEnabled())