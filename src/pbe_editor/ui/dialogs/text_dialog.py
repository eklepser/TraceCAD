from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QCheckBox, QPushButton)
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Qt, Signal
from constants import Styles
from pbe_editor.ui.dialogs.headerless_dialog import HeaderlessDialog


class TextDialog(HeaderlessDialog):
    text_changed = Signal(str)
    size_changed = Signal(float)
    visible_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent, title="Текст")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("Текст")
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Введите текст...")
        self.text_input.setStyleSheet(Styles.INPUT_BG)
        self.text_input.setMinimumWidth(300)
        self.text_input.setMinimumHeight(28)
        self.text_input.textChanged.connect(self.text_changed.emit)
        layout.addWidget(self.text_input)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Размер:"))
        self.size_edit = QLineEdit("1.00")
        validator = QDoubleValidator(0.05, 10.0, 2, self.size_edit)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.size_edit.setValidator(validator)
        self.size_edit.setStyleSheet(Styles.INPUT_BG)
        self.size_edit.setMinimumWidth(140)
        self.size_edit.setMinimumHeight(28)
        self.size_edit.textChanged.connect(self._on_size_text_changed)
        size_row.addWidget(self.size_edit, 1)
        layout.addLayout(size_row)

        self.visible_check = QCheckBox("Видимый")
        self.visible_check.setChecked(True)
        self.visible_check.setStyleSheet(
            "QCheckBox { color: #a9b7c6; spacing: 8px; }"
            "QCheckBox::indicator { width: 14px; height: 14px;"
            " border: 1px solid #d8d8d8; background-color: #2b2b2b;"
            " border-radius: 2px; }"
            "QCheckBox::indicator:checked {"
            " border: 1px solid #ffffff; background-color: #365880; }"
        )
        self.visible_check.stateChanged.connect(
            lambda state: self.visible_changed.emit(state == Qt.CheckState.Checked.value)
        )
        layout.addWidget(self.visible_check)

        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setStyleSheet(Styles.BUTTON_OK)
        self.btn_ok.clicked.connect(self.accept)

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_cancel.clicked.connect(self.reject)

        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        self.text_input.returnPressed.connect(self.accept)

    def _on_size_text_changed(self, text):
        try:
            value = float(text.replace(',', '.'))
        except ValueError:
            return
        self.size_changed.emit(value)

    def get_text(self):
        return self.text_input.text()

    def get_size(self):
        try:
            return float(self.size_edit.text().replace(',', '.'))
        except ValueError:
            return 1.0

    def get_visible(self):
        return self.visible_check.isChecked()