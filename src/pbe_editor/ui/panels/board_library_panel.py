from pathlib import Path

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from constants import Styles
from pbe_editor.ui.dialogs.libraries_dialog import LibrariesManagerDialog


PANEL_MIN_WIDTH = 160
PANEL_MAX_WIDTH = 320

ADD_BUTTON_STYLE = (
    "QPushButton { background-color: #365880; color: white;"
    " font-size: 14px; font-weight: bold;"
    " border: none; padding: 0px; }"
    " QPushButton:hover { background-color: #2a4a6b; }"
)


class BoardLibraryPanel(QWidget):
    add_library_requested = Signal()
    library_selected = Signal(str)
    module_add_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(PANEL_MIN_WIDTH)
        self.setMaximumWidth(PANEL_MAX_WIDTH)
        self._paths = []
        self._modules = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Библиотеки")
        title.setStyleSheet(Styles.SECTION_LABEL)
        header.addWidget(title)
        header.addStretch()
        self.btn_manage = QPushButton("📚")
        self.btn_manage.setFixedSize(24, 24)
        self.btn_manage.setToolTip("Подключенные библиотеки")
        self.btn_manage.setStyleSheet(ADD_BUTTON_STYLE)
        self.btn_manage.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_manage.clicked.connect(self._on_manage_clicked)
        header.addWidget(self.btn_manage)
        self.btn_add_library = QPushButton("+")
        self.btn_add_library.setFixedSize(24, 24)
        self.btn_add_library.setToolTip("Добавить библиотеку")
        self.btn_add_library.setStyleSheet(ADD_BUTTON_STYLE)
        self.btn_add_library.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_library.clicked.connect(self.add_library_requested.emit)
        header.addWidget(self.btn_add_library)
        layout.addLayout(header)

        self.library_list_widget = QListWidget()
        self.library_list_widget.setStyleSheet(Styles.LIST_BG)
        self.library_list_widget.itemClicked.connect(self._on_library_clicked)
        layout.addWidget(self.library_list_widget, 1)

        header2 = QHBoxLayout()
        header2.setContentsMargins(0, 0, 0, 0)
        title2 = QLabel("Корпуса")
        title2.setStyleSheet(Styles.SECTION_LABEL)
        header2.addWidget(title2)
        header2.addStretch()
        layout.addLayout(header2)

        self.module_list_widget = QListWidget()
        self.module_list_widget.setStyleSheet(Styles.LIST_BG)
        self.module_list_widget.itemDoubleClicked.connect(self._on_module_double_clicked)
        layout.addWidget(self.module_list_widget, 1)

    def _on_manage_clicked(self):
        dlg = LibrariesManagerDialog(self._paths, self)
        if dlg.exec() == LibrariesManagerDialog.Accepted:
            self._paths = dlg.get_library_paths()
            self.add_library_requested.emit()

    def apply_theme(self):
        self.btn_add_library.setStyleSheet(ADD_BUTTON_STYLE)
        self.btn_manage.setStyleSheet(ADD_BUTTON_STYLE)
        self.library_list_widget.setStyleSheet(Styles.LIST_BG)
        self.module_list_widget.setStyleSheet(Styles.LIST_BG)

    def _on_library_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.library_selected.emit(path)

    def _on_module_double_clicked(self, item):
        name = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self.module_add_requested.emit(name)

    def set_libraries(self, paths):
        self._paths = list(paths)
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

    def highlight_library(self, path):
        if not path:
            self.library_list_widget.clearSelection()
            return
        for i in range(self.library_list_widget.count()):
            item = self.library_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                self.library_list_widget.setCurrentItem(item)
                return

    def highlight_module(self, name):
        if not name:
            self.module_list_widget.clearSelection()
            return
        for i in range(self.module_list_widget.count()):
            item = self.module_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == name:
                self.module_list_widget.setCurrentItem(item)
                return