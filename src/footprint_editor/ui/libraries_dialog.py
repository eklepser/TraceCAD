from pathlib import Path

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QHeaderView,
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from constants import Styles


class LibrariesManagerDialog(QDialog):
    def __init__(self, library_paths, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление библиотеками")
        self.resize(700, 400)
        self.setStyleSheet(Styles.DIALOG_BG)

        self.library_paths = list(library_paths)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Имя", "Путь"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить...")
        self.btn_add.setStyleSheet(Styles.BUTTON_OK)
        self.btn_add.clicked.connect(self._add_library)

        self.btn_remove = QPushButton("Удалить")
        self.btn_remove.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_remove.clicked.connect(self._remove_selected)

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

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