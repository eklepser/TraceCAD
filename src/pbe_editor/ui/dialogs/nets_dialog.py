from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QHeaderView, QLabel)
from constants import Styles
from pbe_editor.ui.dialogs.headerless_dialog import HeaderlessDialog


class NetsDialog(HeaderlessDialog):
    def __init__(self, board, parent=None):
        super().__init__(parent, title="Связи на плате")
        self.resize(700, 450)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("Связи (nets)")
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Код", "Имя цепи", "Пины"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #1e1e1e; color: #cfcfcf;"
            " gridline-color: #3c3f41; border: 1px solid #3c3f41; }"
            "QHeaderView::section { background-color: #2b2b2b; color: #a9b7c6;"
            " border: 0px; border-right: 1px solid #3c3f41; padding: 4px; }"
        )
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_close.clicked.connect(self.accept)
        btns.addWidget(self.btn_close)
        layout.addLayout(btns)

        self._fill(board)

    def _fill(self, board):
        pin_index = {}
        for module in board.modules:
            for pad_number, pad_net in module.pad_nets.items():
                key = pad_net.net_code
                label = f"{module.reference}.{pad_number}"
                pin_index.setdefault(key, []).append(label)

        self.table.setRowCount(0)
        for code in sorted(board.nets.keys()):
            net = board.nets[code]
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(net.code)))
            self.table.setItem(row, 1, QTableWidgetItem(net.name))
            pins = ", ".join(pin_index.get(net.code, []))
            self.table.setItem(row, 2, QTableWidgetItem(pins))