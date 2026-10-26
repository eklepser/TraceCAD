from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from constants import Styles


PANEL_MIN_WIDTH = 160
PANEL_MAX_WIDTH = 320


class BoardLibraryPanel(QWidget):
    module_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(PANEL_MIN_WIDTH)
        self.setMaximumWidth(PANEL_MAX_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Элементы на плате")
        title.setStyleSheet(Styles.SECTION_LABEL)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.module_list_widget = QListWidget()
        self.module_list_widget.setStyleSheet(Styles.LIST_BG)
        self.module_list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.module_list_widget, 1)

    def apply_theme(self):
        self.module_list_widget.setStyleSheet(Styles.LIST_BG)

    def _on_item_clicked(self, item):
        uid = item.data(Qt.ItemDataRole.UserRole)
        if uid is not None:
            self.module_selected.emit(int(uid))

    def set_modules(self, modules):
        self.module_list_widget.clear()
        for m in sorted(modules, key=lambda x: x.reference):
            label = f"{m.reference}  [{m.footprint.name}]"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, m.uid)
            item.setToolTip(f"{m.reference} = {m.value}")
            self.module_list_widget.addItem(item)

    def highlight_module(self, uid):
        if uid is None:
            self.module_list_widget.clearSelection()
            return
        for i in range(self.module_list_widget.count()):
            item = self.module_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == uid:
                self.module_list_widget.setCurrentItem(item)
                return
        self.module_list_widget.clearSelection()