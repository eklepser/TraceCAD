from PySide6.QtWidgets import QWidget, QVBoxLayout
from footprint_editor.ui.panels.properties_panel import PropertiesPanel
from constants import Styles


PANEL_MIN_WIDTH = 200
PANEL_MAX_WIDTH = 320


class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(PANEL_MIN_WIDTH)
        self.setMaximumWidth(PANEL_MAX_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.properties_panel = PropertiesPanel()
        layout.addWidget(self.properties_panel, stretch=1)

    def apply_theme(self):
        self.properties_panel.apply_theme()