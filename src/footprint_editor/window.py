from PySide6.QtWidgets import (QMainWindow, QDockWidget, QWidget, QVBoxLayout, 
                               QLabel, QToolBar, QStatusBar, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from footprint_editor.models import Footprint
from footprint_editor.canvas import FootprintCanvas

class FootprintEditorWindow(QMainWindow):
    def __init__(self, footprint=None):
        super().__init__()
        
        self.footprint = footprint or Footprint(name="New_Footprint")
        self.setWindowTitle(f"TraceCAD - Редактор корпусов: {self.footprint.name}")
        self.resize(1200, 800)
        
        self.canvas = FootprintCanvas(self)
        self.setCentralWidget(self.canvas)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        
        self._init_docks()
        self._init_toolbars()
        self._init_statusbar()

    def _init_docks(self):
        self.properties_dock = QDockWidget("Свойства объекта", self)
        self.properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        props_widget = QWidget()
        props_widget.setStyleSheet("background-color: #3c3f41; color: white;")
        props_layout = QVBoxLayout(props_widget)
        props_layout.addWidget(QLabel("Выберите примитив на холсте"))
        props_layout.addStretch()
        self.properties_dock.setWidget(props_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)

    def _init_toolbars(self):
        toolbar = QToolBar("Инструменты", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        self.act_select = QAction("Выделение", self)
        self.act_add_pad = QAction("Площадка", self)
        self.act_add_line = QAction("Линия", self)
        
        toolbar.addAction(self.act_select)
        toolbar.addSeparator()
        toolbar.addAction(self.act_add_pad)
        toolbar.addAction(self.act_add_line)
        
        toolbar.addSeparator()
        
        grid_label = QLabel(" Шаг сетки (мм): ")
        toolbar.addWidget(grid_label)
        
        self.grid_combo = QComboBox()
        grid_steps = ["2.54", "1.27", "0.635", "0.3175", "0.15875", "0.079375"]
        self.grid_combo.addItems(grid_steps)
        self.grid_combo.setCurrentText("1.27")
        self.grid_combo.currentTextChanged.connect(self._on_grid_changed)
        toolbar.addWidget(self.grid_combo)
        
        toolbar.addSeparator()
        
        self.zoom_label = QLabel(" 100% ")
        toolbar.addWidget(self.zoom_label)

    def _init_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово. Средняя кнопка мыши - панорама, Колесо - зум.")

    def _on_grid_changed(self, text):
        self.canvas.set_grid_size(float(text))

    def _update_zoom_label(self, zoom):
        self.zoom_label.setText(f" {int(zoom * 100)}% ")