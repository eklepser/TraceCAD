from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from constants import Styles
from footprint_editor.ui.dialogs.headerless_dialog import HeaderlessDialog


class CustomQuestionDialog(HeaderlessDialog):
    ResultSave = 1
    ResultDiscard = 2
    ResultCancel = 3

    def __init__(self, parent=None, title="", message="", 
                 btn_yes="Сохранить", btn_no="Не сохранять", btn_cancel="Отмена"):
        super().__init__(parent, title=title)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel(title)
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: #d8d8d8;")
        layout.addWidget(msg_label)

        btns = QHBoxLayout()
        btns.addStretch()

        self.btn_save = QPushButton(btn_yes)
        self.btn_save.setStyleSheet(Styles.BUTTON_OK)
        self.btn_save.clicked.connect(lambda: self.done(self.ResultSave))

        self.btn_discard = QPushButton(btn_no)
        self.btn_discard.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_discard.clicked.connect(lambda: self.done(self.ResultDiscard))

        self.btn_cancel = QPushButton(btn_cancel)
        self.btn_cancel.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_cancel.clicked.connect(lambda: self.done(self.ResultCancel))

        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_discard)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)