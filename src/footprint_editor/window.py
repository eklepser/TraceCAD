from PySide6.QtWidgets import (QMainWindow, QDockWidget, QWidget, QVBoxLayout, 
                               QLabel, QToolBar, QStatusBar, QComboBox, QApplication)
from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QKeyEvent
from constants import Tool, PAN_KEYS
from footprint_editor.models import Footprint, Pad, PadShape, PadType, Line
from footprint_editor.canvas import FootprintCanvas
from footprint_editor.pad_graphics import PadGraphicsItem
from footprint_editor.line_graphics import LineGraphicsItem
from footprint_editor.right_panel import RightPanel

class GlobalKeyFilter(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            return self.window.handle_global_key(event)
        return super().eventFilter(obj, event)

class FootprintEditorWindow(QMainWindow):
    def __init__(self, footprint=None):
        super().__init__()
        
        self.footprint = footprint or Footprint(name="New_Footprint")
        self.setWindowTitle(f"TraceCAD - Редактор корпусов: {self.footprint.name}")
        self.resize(1000, 700)
        
        self.current_tool = Tool.SELECT
        self.graphics_items = {}
        self.line_start_point = None
        
        self.canvas = FootprintCanvas(self)
        self.setCentralWidget(self.canvas)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.canvas.canvas_clicked.connect(self._on_canvas_clicked)
        self.canvas.mouse_moved.connect(self._on_mouse_moved)
        self.canvas.finish_drawing.connect(self._finish_drawing)
        self.canvas.scene.selectionChanged.connect(self._on_selection_changed)
        
        self.key_filter = GlobalKeyFilter(self)
        QApplication.instance().installEventFilter(self.key_filter)
        
        self._init_docks()
        self._init_toolbars()
        self._init_statusbar()
        self._connect_right_panel()

    def _init_docks(self):
        self.properties_dock = QDockWidget("Панель инструментов", self)
        self.properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.right_panel = RightPanel()
        self.right_panel.setStyleSheet("background-color: #3c3f41; color: white;")
        
        self.properties_dock.setWidget(self.right_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)

    def _connect_right_panel(self):
        self.right_panel.btn_select.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_select))
        self.right_panel.btn_add_pad.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_pad))
        self.right_panel.btn_add_line.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_line))
        self.right_panel.btn_delete.clicked.connect(self._delete_selected)

    def _init_toolbars(self):
        toolbar = QToolBar("Настройки вида", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
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
        
        self.coords_label = QLabel("X: 0.0000, Y: 0.0000")
        self.status_bar.addPermanentWidget(self.coords_label)
        
        self.status_bar.showMessage("Готово. F1/F2 - шаг сетки, Del - удалить.")

    def _on_tool_button_clicked(self, button):
        if button == self.right_panel.btn_select:
            self.current_tool = Tool.SELECT
        elif button == self.right_panel.btn_add_pad:
            self.current_tool = Tool.ADD_PAD
        elif button == self.right_panel.btn_add_line:
            self.current_tool = Tool.ADD_LINE
            
        self.line_start_point = None
        self.canvas.clear_ghost_line()
        
        if self.current_tool == Tool.SELECT:
            self.canvas.set_show_snap(False)
            self.canvas.set_interaction_enabled(True)
        else:
            self.canvas.set_show_snap(True)
            self.canvas.set_interaction_enabled(False)
            
        self.status_bar.showMessage(f"Инструмент: {self.current_tool}")

    def _finish_drawing(self):
        self.line_start_point = None
        self.canvas.clear_ghost_line()

    def _on_grid_changed(self, text):
        self.canvas.set_grid_size(float(text))
        self.canvas.setFocus()

    def _change_grid_step(self, direction):
        current_index = self.grid_combo.currentIndex()
        new_index = current_index + direction
        if 0 <= new_index < self.grid_combo.count():
            self.grid_combo.setCurrentIndex(new_index)
            self._on_grid_changed(self.grid_combo.currentText())

    def _update_zoom_label(self, zoom):
        self.zoom_label.setText(f" {int(zoom * 100)}% ")

    def _on_canvas_clicked(self, x, y):
        if self.current_tool == Tool.ADD_PAD:
            new_pad = Pad(number="1", shape=PadShape.CIRCLE, pad_type=PadType.SMD, x=x, y=y, width=1.5, height=1.5)
            self.footprint.pads.append(new_pad)
            graphics_item = PadGraphicsItem(new_pad, self.canvas)
            self.canvas.scene.addItem(graphics_item)
            self.graphics_items[new_pad.uid] = graphics_item
            self.canvas.set_interaction_enabled(False)
            
        elif self.current_tool == Tool.ADD_LINE:
            if self.line_start_point is None:
                self.line_start_point = (x, y)
            else:
                start_x, start_y = self.line_start_point
                new_line = Line(start_x, start_y, x, y)
                self.footprint.lines.append(new_line)
                
                final_item = LineGraphicsItem(new_line, self.canvas)
                self.canvas.scene.addItem(final_item)
                self.graphics_items[new_line.uid] = final_item
                self.canvas.set_interaction_enabled(False)
                
                self.line_start_point = (x, y)

    def _on_mouse_moved(self, x, y):
        self.coords_label.setText(f"X: {x:.4f}, Y: {y:.4f}")
        
        if self.current_tool == Tool.ADD_LINE and self.line_start_point:
            self.canvas.set_ghost_line(self.line_start_point[0], self.line_start_point[1], x, y)
        else:
            self.canvas.clear_ghost_line()

    def _on_selection_changed(self):
        selected_items = self.canvas.scene.selectedItems()
        has_selection = len(selected_items) > 0
        self.right_panel.btn_delete.setEnabled(has_selection)
        
        if not has_selection:
            self.right_panel.properties_panel.clear_panel()
            self.right_panel.properties_panel.no_selection_label.show()
            return
            
        item = selected_items[0]
        if isinstance(item, PadGraphicsItem):
            self.right_panel.properties_panel.set_object(item.pad)
        elif isinstance(item, LineGraphicsItem):
            self.right_panel.properties_panel.set_object(item.line_model)
        else:
            self.right_panel.properties_panel.clear_panel()
            self.right_panel.properties_panel.no_selection_label.show()

    def _delete_selected(self):
        selected_items = self.canvas.scene.selectedItems()
        for item in selected_items:
            if isinstance(item, PadGraphicsItem):
                if item.pad in self.footprint.pads:
                    self.footprint.pads.remove(item.pad)
                self.graphics_items.pop(item.pad.uid, None)
                self.canvas.scene.removeItem(item)
            elif isinstance(item, LineGraphicsItem) and not item.is_preview:
                if item.line_model in self.footprint.lines:
                    self.footprint.lines.remove(item.line_model)
                self.graphics_items.pop(item.line_model.uid, None)
                self.canvas.scene.removeItem(item)
                
        self.right_panel.properties_panel.clear_panel()
        self.right_panel.properties_panel.no_selection_label.show()
        self.right_panel.btn_delete.setEnabled(False)

    def handle_global_key(self, event):
        vk = event.nativeVirtualKey()
        
        if event.type() == QEvent.Type.KeyPress:
            if vk in PAN_KEYS:
                self.canvas.pressed_keys.add(vk)
                if not self.canvas.pan_timer.isActive():
                    self.canvas.pan_timer.start()
                return True
            elif vk == 0x1B:
                self._finish_drawing()
                self.canvas.scene.clearSelection()
                self.right_panel.btn_select.setChecked(True)
                self._on_tool_button_clicked(self.right_panel.btn_select)
                return True
            elif vk == 0x2E:
                self._delete_selected()
                return True
            elif vk == 0x70:
                self._change_grid_step(-1)
                return True
            elif vk == 0x71:
                self._change_grid_step(1)
                return True
                
        elif event.type() == QEvent.Type.KeyRelease:
            if vk in PAN_KEYS:
                self.canvas.pressed_keys.discard(vk)
                if not self.canvas.pressed_keys:
                    self.canvas.pan_timer.stop()
                return True
                
        return False