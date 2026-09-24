from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QButtonGroup
from footprint_editor.properties_panel import PropertiesPanel

class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.tool_group_box = QGroupBox("Инструменты")
        tool_layout = QHBoxLayout(self.tool_group_box)
        
        self.btn_select = QPushButton("В")
        self.btn_select.setFixedSize(40, 40)
        self.btn_select.setToolTip("Выделение")
        self.btn_select.setCheckable(True)
        self.btn_select.setChecked(True)
        
        self.btn_add_pad = QPushButton("П")
        self.btn_add_pad.setFixedSize(40, 40)
        self.btn_add_pad.setToolTip("Площадка")
        self.btn_add_pad.setCheckable(True)
        
        self.btn_add_line = QPushButton("Л")
        self.btn_add_line.setFixedSize(40, 40)
        self.btn_add_line.setToolTip("Линия")
        self.btn_add_line.setCheckable(True)
        
        self.tool_button_group = QButtonGroup(self)
        self.tool_button_group.setExclusive(True)
        self.tool_button_group.addButton(self.btn_select)
        self.tool_button_group.addButton(self.btn_add_pad)
        self.tool_button_group.addButton(self.btn_add_line)
        
        tool_layout.addWidget(self.btn_select)
        tool_layout.addWidget(self.btn_add_pad)
        tool_layout.addWidget(self.btn_add_line)
        layout.addWidget(self.tool_group_box)
        
        self.actions_group_box = QGroupBox("Действия")
        actions_layout = QVBoxLayout(self.actions_group_box)
        
        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.setEnabled(False)
        actions_layout.addWidget(self.btn_delete)
        
        layout.addWidget(self.actions_group_box)
        
        self.properties_panel = PropertiesPanel()
        layout.addWidget(self.properties_panel, stretch=1)