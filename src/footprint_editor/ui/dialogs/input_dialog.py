from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton)
from constants import Styles
from common.ui.dialogs.headerless_dialog import HeaderlessDialog


class InputDialog(HeaderlessDialog):
    def __init__(self, parent=None, title="Ввод", label="Значение:",
                 placeholder="", initial=""):
        super().__init__(parent, title=title)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel(title)
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)

        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        self.input = QLineEdit(initial)
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet(Styles.INPUT_BG)
        row.addWidget(self.input, 1)
        layout.addLayout(row)

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

        self.input.returnPressed.connect(self.accept)

    def get_text(self):
        return self.input.text()