from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                               QDoubleSpinBox, QPushButton)
from PySide6.QtCore import Signal
from constants import Styles
from footprint_editor.ui.dialogs.headerless_dialog import HeaderlessDialog


class ArcDialog(HeaderlessDialog):
    angle_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent, title="Дуга")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("Дуга")
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)

        row = QHBoxLayout()
        row.addWidget(QLabel("Угол (°):"))
        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(-359.0, 359.0)
        self.angle_spin.setSingleStep(15.0)
        self.angle_spin.setDecimals(1)
        self.angle_spin.setValue(90.0)
        self.angle_spin.setStyleSheet(Styles.INPUT_BG)
        self.angle_spin.valueChanged.connect(self.angle_changed.emit)
        row.addWidget(self.angle_spin, 1)
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

    def get_angle(self):
        return self.angle_spin.value()