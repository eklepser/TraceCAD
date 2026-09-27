from pathlib import Path

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QHeaderView,
                               QFileDialog, QMessageBox, QLabel)
from PySide6.QtCore import Qt
from constants import Styles
from footprint_editor.ui.dialogs.headerless_dialog import HeaderlessDialog


class LibrariesManagerDialog(HeaderlessDialog):
    def __init__(self, library_paths, parent=None):
        super().__init__(parent, title="Управление библиотеками")
        self.resize(700, 400)

        self.library_paths = list(library_paths)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("Управление библиотеками")
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Имя", "Путь"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #1e1e1e; color: #cfcfcf;"
            " gridline-color: #3c3f41; border: 1px solid #3c3f41; }"
            "QHeaderView::section { background-color: #2b2b2b; color: #a9b7c6;"
            " border: 0px; border-right: 1px solid #3c3f41; padding: 4px; }"
        )
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        self.btn_add = QPushButton("Добавить...")
        self.btn_add.setStyleSheet(Styles.BUTTON_OK)
        self.btn_add.clicked.connect(self._add_library)

        self.btn_remove = QPushButton("Удалить")
        self.btn_remove.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_remove.clicked.connect(self._remove_selected)

        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_remove)
        btns.addStretch()

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_close.clicked.connect(self.accept)
        btns.addWidget(self.btn_close)

        layout.addLayout(btns)

        self._refresh()

    def _refresh(self):
        self.table.setRowCount(0)
        for path in self.library_paths:
            row = self.table.rowCount()
            self.table.insertRow(row)
            name_item = QTableWidgetItem(Path(path).stem)
            name_item.setData(Qt.ItemDataRole.UserRole, path)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(path))

    def _add_library(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Добавить библиотеку KiCad", "",
            "KiCad Library (*.mod);;All Files (*)"
        )
        if path:
            if path in self.library_paths:
                QMessageBox.information(self, "Информация", "Эта библиотека уже добавлена.")
                return
            self.library_paths.append(path)
            self._refresh()

    def _remove_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            del self.library_paths[row]
            self._refresh()

    def get_library_paths(self):
        return list(self.library_paths)