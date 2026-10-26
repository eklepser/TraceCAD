from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton)
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Signal
from constants import Styles
from common.ui.dialogs.headerless_dialog import HeaderlessDialog


class ArcDialog(HeaderlessDialog):
    angle_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent, title="Дуга")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("Дуга")
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)

        row = QHBoxLayout()
        row.addWidget(QLabel("Угол (°):"))
        self.angle_edit = QLineEdit("90.0")
        validator = QDoubleValidator(-359.0, 359.0, 1, self.angle_edit)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.angle_edit.setValidator(validator)
        self.angle_edit.setStyleSheet(Styles.INPUT_BG)
        self.angle_edit.setMinimumWidth(140)
        self.angle_edit.setMinimumHeight(28)
        self.angle_edit.textChanged.connect(self._on_angle_text_changed)
        row.addWidget(self.angle_edit, 1)
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

    def _on_angle_text_changed(self, text):
        try:
            value = float(text.replace(',', '.'))
        except ValueError:
            return
        self.angle_changed.emit(value)

    def get_angle(self):
        try:
            return float(self.angle_edit.text().replace(',', '.'))
        except ValueError:
            return 90.0