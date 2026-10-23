from pathlib import Path

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidget, QListWidgetItem, QMenu)
from PySide6.QtCore import Qt, Signal
from constants import Styles


LEFT_PANEL_MIN_WIDTH = 160
LEFT_PANEL_MAX_WIDTH = 320

ADD_BUTTON_STYLE = (
    "QPushButton { background-color: #365880; color: white;"
    " font-size: 14px; font-weight: bold;"
    " border: none; padding: 0px; }"
    " QPushButton:hover { background-color: #2a4a6b; }"
)


class LibraryPanel(QWidget):
    add_library_requested = Signal()
    add_module_requested = Signal()
    library_selected = Signal(str)
    module_selected = Signal(str)
    module_rename_requested = Signal(str)
    module_delete_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(LEFT_PANEL_MIN_WIDTH)
        self.setMaximumWidth(LEFT_PANEL_MAX_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.btn_add_library, lib_header = self._make_header("Библиотеки", "Добавить библиотеку")
        self.btn_add_library.clicked.connect(self.add_library_requested.emit)
        layout.addLayout(lib_header)

        self.library_list_widget = QListWidget()
        self.library_list_widget.setStyleSheet(Styles.LIST_BG)
        self.library_list_widget.itemClicked.connect(self._on_library_clicked)
        layout.addWidget(self.library_list_widget, 1)

        self.btn_add_module, mod_header = self._make_header("Корпуса", "Добавить корпус")
        self.btn_add_module.clicked.connect(self.add_module_requested.emit)
        layout.addLayout(mod_header)

        self.module_list_widget = QListWidget()
        self.module_list_widget.setStyleSheet(Styles.LIST_BG)
        self.module_list_widget.itemClicked.connect(self._on_module_clicked)
        self.module_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.module_list_widget.customContextMenuRequested.connect(self._on_module_context_menu)
        layout.addWidget(self.module_list_widget, 1)

    def _make_header(self, title, tooltip):
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setStyleSheet(Styles.SECTION_LABEL)
        header.addWidget(label)
        header.addStretch()

        btn = QPushButton("+")
        btn.setFixedSize(24, 24)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(ADD_BUTTON_STYLE)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header.addWidget(btn)
        return btn, header

    def apply_theme(self):
        self.btn_add_library.setStyleSheet(ADD_BUTTON_STYLE)
        self.btn_add_module.setStyleSheet(ADD_BUTTON_STYLE)
        self.library_list_widget.setStyleSheet(Styles.LIST_BG)
        self.module_list_widget.setStyleSheet(Styles.LIST_BG)

    def _on_library_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.library_selected.emit(path)

    def _on_module_clicked(self, item):
        name = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self.module_selected.emit(name)

    def _on_module_context_menu(self, pos):
        item = self.module_list_widget.itemAt(pos)
        if not item:
            return

        name = item.data(Qt.ItemDataRole.UserRole)
        if not name:
            return

        menu = QMenu(self)
        menu.setStyleSheet(Styles.MAIN_WINDOW)

        act_rename = menu.addAction("Переименовать...")
        act_delete = menu.addAction("Удалить")

        action = menu.exec(self.module_list_widget.mapToGlobal(pos))
        if action == act_rename:
            self.module_rename_requested.emit(name)
        elif action == act_delete:
            self.module_delete_requested.emit(name)

    def set_libraries(self, paths):
        self.library_list_widget.clear()
        for path in paths:
            item = QListWidgetItem(Path(path).stem)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.library_list_widget.addItem(item)

    def set_modules(self, names):
        self.module_list_widget.clear()
        for name in sorted(names):
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setToolTip(name)
            self.module_list_widget.addItem(item)

    def mark_unsaved(self, unsaved_names):
        for i in range(self.module_list_widget.count()):
            item = self.module_list_widget.item(i)
            name = item.data(Qt.ItemDataRole.UserRole)
            item.setText(f"{name} *" if name in unsaved_names else name)

    def highlight_library(self, path):
        if not path:
            self.library_list_widget.clearSelection()
            return
        for i in range(self.library_list_widget.count()):
            item = self.library_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                self.library_list_widget.setCurrentItem(item)
                return
        self.library_list_widget.clearSelection()

    def highlight_module(self, name):
        if not name:
            self.module_list_widget.clearSelection()
            return
        for i in range(self.module_list_widget.count()):
            item = self.module_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == name:
                self.module_list_widget.setCurrentItem(item)
                return
        self.module_list_widget.clearSelection()