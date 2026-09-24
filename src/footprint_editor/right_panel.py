from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QButtonGroup

class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.tool_group_box = QGroupBox("Инструменты")
        tool_layout = QHBoxLayout(self.tool_group_box)
        
        self.btn_add_pad = QPushButton("⬤")
        self.btn_add_pad.setFixedSize(40, 40)
        self.btn_add_pad.setToolTip("Площадка")
        self.btn_add_pad.setCheckable(True)
        self.btn_add_pad.setStyleSheet("font-size: 20px;")
        
        self.btn_add_line = QPushButton("╱")
        self.btn_add_line.setFixedSize(40, 40)
        self.btn_add_line.setToolTip("Линия")
        self.btn_add_line.setCheckable(True)
        self.btn_add_line.setStyleSheet("font-size: 20px;")

        self.btn_add_circle = QPushButton("◯")
        self.btn_add_circle.setFixedSize(40, 40)
        self.btn_add_circle.setToolTip("Окружность")
        self.btn_add_circle.setCheckable(True)
        self.btn_add_circle.setStyleSheet("font-size: 20px;")
        
        tool_layout.addWidget(self.btn_add_pad)
        tool_layout.addWidget(self.btn_add_line)
        tool_layout.addWidget(self.btn_add_circle)
        layout.addWidget(self.tool_group_box)
        
        self.actions_group_box = QGroupBox("Действия")
        actions_layout = QVBoxLayout(self.actions_group_box)
        
        self.btn_select = QPushButton("✥")
        self.btn_select.setFixedSize(40, 40)
        self.btn_select.setToolTip("Выделение")
        self.btn_select.setCheckable(True)
        self.btn_select.setChecked(True)
        self.btn_select.setStyleSheet("font-size: 20px;")
        actions_layout.addWidget(self.btn_select)
        
        self.btn_delete = QPushButton("🗑")
        self.btn_delete.setFixedSize(40, 40)
        self.btn_delete.setToolTip("Удалить")
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet("font-size: 20px;")
        actions_layout.addWidget(self.btn_delete)
        
        layout.addWidget(self.actions_group_box)
        layout.addStretch()