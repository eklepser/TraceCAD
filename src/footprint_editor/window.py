from PySide6.QtWidgets import (QMainWindow, QDockWidget, QWidget, QVBoxLayout, 
                               QLabel, QToolBar, QStatusBar, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeyEvent
from constants import Tool, PAN_KEYS
from footprint_editor.models import Footprint, Pad, PadShape, PadType, Line
from footprint_editor.canvas import FootprintCanvas
from footprint_editor.pad_graphics import PadGraphicsItem
from footprint_editor.line_graphics import LineGraphicsItem
from footprint_editor.properties_panel import PropertiesPanel

class FootprintEditorWindow(QMainWindow):
    def __init__(self, footprint=None):
        super().__init__()
        
        self.footprint = footprint or Footprint(name="New_Footprint")
        self.setWindowTitle(f"TraceCAD - Редактор корпусов: {self.footprint.name}")
        self.resize(1200, 800)
        
        self.current_tool = Tool.SELECT
        self.graphics_items = {}
        self.line_start_point = None
        
        self.canvas = FootprintCanvas(self)
        self.setCentralWidget(self.canvas)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.canvas.canvas_clicked.connect(self._on_canvas_clicked)
        self.canvas.finish_drawing.connect(self._finish_drawing)
        self.canvas.scene.selectionChanged.connect(self._on_selection_changed)
        
        self._init_docks()
        self._init_toolbars()
        self._init_statusbar()

    def _init_docks(self):
        self.properties_dock = QDockWidget("Свойства объекта", self)
        self.properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.properties_panel = PropertiesPanel()
        self.properties_panel.setStyleSheet("background-color: #3c3f41; color: white;")
        
        self.properties_dock.setWidget(self.properties_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)

    def _init_toolbars(self):
        toolbar = QToolBar("Инструменты", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        self.act_select = QAction("Выделение", self)
        self.act_select.setCheckable(True)
        self.act_select.setChecked(True)
        
        self.act_add_pad = QAction("Площадка", self)
        self.act_add_pad.setCheckable(True)
        
        self.act_add_line = QAction("Линия", self)
        self.act_add_line.setCheckable(True)
        
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_group.addAction(self.act_select)
        self.tool_group.addAction(self.act_add_pad)
        self.tool_group.addAction(self.act_add_line)
        
        self.tool_group.triggered.connect(self._on_tool_changed)
        
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
        self.status_bar.showMessage("Готово. WASD - панорама, Колесо - зум. ПКМ/Esc - отмена.")

    def _on_tool_changed(self, action):
        if action == self.act_select:
            self.current_tool = Tool.SELECT
        elif action == self.act_add_pad:
            self.current_tool = Tool.ADD_PAD
        elif action == self.act_add_line:
            self.current_tool = Tool.ADD_LINE
            
        self.line_start_point = None
        self.status_bar.showMessage(f"Инструмент: {self.current_tool}")

    def _finish_drawing(self):
        self.line_start_point = None

    def _on_grid_changed(self, text):
        self.canvas.set_grid_size(float(text))

    def _update_zoom_label(self, zoom):
        self.zoom_label.setText(f" {int(zoom * 100)}% ")

    def _on_canvas_clicked(self, x, y):
        if self.current_tool == Tool.ADD_PAD:
            new_pad = Pad(number="1", shape=PadShape.CIRCLE, pad_type=PadType.SMD, x=x, y=y, width=1.5, height=1.5)
            self.footprint.pads.append(new_pad)
            graphics_item = PadGraphicsItem(new_pad)
            self.canvas.scene.addItem(graphics_item)
            self.graphics_items[new_pad.uid] = graphics_item
            
        elif self.current_tool == Tool.ADD_LINE:
            if self.line_start_point is None:
                self.line_start_point = (x, y)
            else:
                start_x, start_y = self.line_start_point
                new_line = Line(start_x, start_y, x, y)
                self.footprint.lines.append(new_line)
                
                final_item = LineGraphicsItem(new_line)
                self.canvas.scene.addItem(final_item)
                self.graphics_items[new_line.uid] = final_item
                
                self.line_start_point = (x, y)

    def _on_selection_changed(self):
        selected_items = self.canvas.scene.selectedItems()
        if not selected_items:
            self.properties_panel.clear_panel()
            self.properties_panel.no_selection_label.show()
            return
            
        item = selected_items[0]
        if isinstance(item, PadGraphicsItem):
            self.properties_panel.set_object(item.pad)
        elif isinstance(item, LineGraphicsItem) and not item.is_preview:
            self.properties_panel.set_object(item.line_model)
        else:
            self.properties_panel.clear_panel()
            self.properties_panel.no_selection_label.show()

    def keyPressEvent(self, event: QKeyEvent):
        vk = event.nativeVirtualKey()
        if vk in PAN_KEYS:
            self.canvas.pressed_keys.add(vk)
            if not self.canvas.pan_timer.isActive():
                self.canvas.pan_timer.start()
            event.accept()
        elif vk == 0x1B:
            self._finish_drawing()
            self.act_select.setChecked(True)
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        vk = event.nativeVirtualKey()
        if vk in PAN_KEYS:
            self.canvas.pressed_keys.discard(vk)
            if not self.canvas.pressed_keys:
                self.canvas.pan_timer.stop()
            event.accept()
        else:
            super().keyReleaseEvent(event)