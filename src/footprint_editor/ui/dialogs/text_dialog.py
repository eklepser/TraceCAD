from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QDoubleSpinBox, QCheckBox, QPushButton)
from PySide6.QtCore import Qt, Signal
from constants import Styles


class TextDialog(QDialog):
    text_changed = Signal(str)
    size_changed = Signal(float)
    visible_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet(Styles.DIALOG_BG)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Введите текст...")
        self.text_input.setStyleSheet(Styles.INPUT_BG)
        self.text_input.textChanged.connect(self.text_changed.emit)
        layout.addWidget(self.text_input)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Размер:"))
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(0.05, 10.0)
        self.size_spin.setSingleStep(0.1)
        self.size_spin.setDecimals(2)
        self.size_spin.setValue(1.0)
        self.size_spin.setStyleSheet(Styles.INPUT_BG)
        self.size_spin.valueChanged.connect(self.size_changed.emit)
        size_layout.addWidget(self.size_spin)
        layout.addLayout(size_layout)

        self.visible_check = QCheckBox("Видимый")
        self.visible_check.setChecked(True)
        self.visible_check.stateChanged.connect(
            lambda state: self.visible_changed.emit(state == Qt.CheckState.Checked.value)
        )
        layout.addWidget(self.visible_check)

        btns = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setFixedSize(60, 30)
        self.btn_ok.setStyleSheet(Styles.BUTTON_OK)
        self.btn_ok.clicked.connect(self.accept)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedSize(60, 30)
        self.btn_cancel.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_cancel.clicked.connect(self.reject)

        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        self.text_input.returnPressed.connect(self.accept)

    def get_text(self):
        return self.text_input.text()

    def get_size(self):
        return self.size_spin.value()

    def get_visible(self):
        return self.visible_check.isChecked()