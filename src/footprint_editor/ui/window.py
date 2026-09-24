import copy
import uuid
import math
from PySide6.QtWidgets import (QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QToolBar, QStatusBar, QComboBox, QApplication, QGraphicsView, 
                               QDialog, QLineEdit, QDoubleSpinBox, QCheckBox, QPushButton, QMenuBar, QMenu)
from PySide6.QtCore import Qt, QEvent, QObject, QPointF, Signal
from PySide6.QtGui import QKeyEvent, QAction
from constants import Tool, PAN_KEYS, Steps, Styles, VK_ESCAPE, VK_DELETE, VK_F1, VK_F2, VK_C, VK_V
from footprint_editor.core.models import Footprint, Pad, PadShape, PadType, Line, Circle, Text
from footprint_editor.core.manager import FootprintManager
from footprint_editor.ui.canvas import FootprintCanvas
from footprint_editor.graphics.pad_item import PadGraphicsItem
from footprint_editor.graphics.line_item import LineGraphicsItem
from footprint_editor.graphics.circle_item import CircleGraphicsItem
from footprint_editor.graphics.text_item import TextGraphicsItem
from footprint_editor.ui.right_panel import RightPanel

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
        self.size_spin.setRange(0.1, 10.0)
        self.size_spin.setSingleStep(0.1)
        self.size_spin.setDecimals(1)
        self.size_spin.setValue(1.0)
        self.size_spin.setStyleSheet(Styles.INPUT_BG)
        self.size_spin.valueChanged.connect(self.size_changed.emit)
        size_layout.addWidget(self.size_spin)
        layout.addLayout(size_layout)
        
        self.visible_check = QCheckBox("Видимый")
        self.visible_check.setChecked(True)
        self.visible_check.setStyleSheet("color: #a9b7c6;")
        self.visible_check.stateChanged.connect(lambda state: self.visible_changed.emit(state == Qt.CheckState.Checked.value))
        layout.addWidget(self.visible_check)
        
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setFixedSize(60, 30)
        self.btn_ok.setStyleSheet(Styles.BUTTON_OK)
        self.btn_ok.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedSize(60, 30)
        self.btn_cancel.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        self.text_input.returnPressed.connect(self.accept)

    def get_text(self):
        return self.text_input.text()

    def get_size(self):
        return self.size_spin.value()

    def get_visible(self):
        return self.visible_check.isChecked()

class GlobalKeyFilter(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            focus_widget = QApplication.focusWidget()
            if focus_widget and isinstance(focus_widget, (QLineEdit, QDoubleSpinBox)):
                return super().eventFilter(obj, event)
            return self.window.handle_global_key(event)
        return super().eventFilter(obj, event)

class FootprintEditorWindow(QMainWindow):
    def __init__(self, footprint=None):
        super().__init__()
        
        self.footprint = footprint or Footprint(name="New_Footprint")
        self.setWindowTitle(f"TraceCAD - Редактор корпусов: {self.footprint.name}")
        self.resize(1000, 700)
        
        self.current_tool = Tool.SELECT
        self.line_start_point = None
        self.circle_center_point = None
        self.text_position = None
        self.clipboard = []
        self._current_mouse_scene_pos = QPointF(0, 0)
        
        self._init_menu()
        
        self.canvas = FootprintCanvas(self)
        self.setCentralWidget(self.canvas)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.canvas.canvas_clicked.connect(self._on_canvas_clicked)
        self.canvas.mouse_moved.connect(self._on_mouse_moved)
        self.canvas.finish_drawing.connect(self._finish_drawing)
        self.canvas.scene.selectionChanged.connect(self._on_selection_changed)
        
        self.manager = FootprintManager(self.footprint, self.canvas.scene, self.canvas)
        
        self.log_label = QLabel("Готово.", self)
        self.log_label.setStyleSheet(Styles.LOG_LABEL)
        self.log_label.adjustSize()
        self.log_label.raise_()
        
        self.key_filter = GlobalKeyFilter(self)
        QApplication.instance().installEventFilter(self.key_filter)
        
        self._init_docks()
        self._init_toolbars()
        self._init_statusbar()
        self._connect_right_panel()

    def _init_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Файл")
        file_menu.addAction("Выбрать библиотеку").setEnabled(False)
        file_menu.addAction("Создать библиотеку").setEnabled(False)
        file_menu.addSeparator()
        file_menu.addAction("Новый модуль").setEnabled(False)
        file_menu.addAction("Сохранить модуль").setEnabled(False)
        file_menu.addAction("Загрузить модуль из библиотеки").setEnabled(False)
        file_menu.addSeparator()
        file_menu.addAction("Свойства модуля").setEnabled(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'log_label') and hasattr(self, 'canvas'):
            canvas_rect = self.canvas.geometry()
            label_size = self.log_label.sizeHint()
            x = canvas_rect.left() + 10
            y = canvas_rect.bottom() - label_size.height() - 10
            self.log_label.move(x, y)

    def show_log(self, text):
        self.log_label.setText(text)
        self.log_label.adjustSize()
        self.resizeEvent(None)

    def _init_docks(self):
        self.properties_dock = QDockWidget("Панель инструментов", self)
        self.properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.right_panel = RightPanel()
        self.right_panel.setStyleSheet(Styles.RIGHT_PANEL)
        
        self.properties_dock.setWidget(self.right_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)

    def _connect_right_panel(self):
        self.right_panel.btn_select.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_select))
        self.right_panel.btn_add_pad.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_pad))
        self.right_panel.btn_add_line.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_line))
        self.right_panel.btn_add_circle.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_circle))
        self.right_panel.btn_add_text.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_text))
        self.right_panel.btn_delete.clicked.connect(self._delete_selected)

    def _init_toolbars(self):
        toolbar = QToolBar("Настройки вида", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        grid_label = QLabel(" Шаг сетки (мм): ")
        toolbar.addWidget(grid_label)
        
        self.grid_combo = QComboBox()
        self.grid_combo.addItems(Steps.GRID)
        self.grid_combo.setCurrentText(Steps.DEFAULT_GRID)
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
        
        self.tool_label = QLabel("Инструмент: select")
        self.status_bar.addWidget(self.tool_label)

    def _on_tool_button_clicked(self, button):
        if button == self.right_panel.btn_select:
            self.current_tool = Tool.SELECT
        elif button == self.right_panel.btn_add_pad:
            self.current_tool = Tool.ADD_PAD
        elif button == self.right_panel.btn_add_line:
            self.current_tool = Tool.ADD_LINE
        elif button == self.right_panel.btn_add_circle:
            self.current_tool = Tool.ADD_CIRCLE
        elif button == self.right_panel.btn_add_text:
            self.current_tool = Tool.ADD_TEXT
        
        self.right_panel.update_tool_buttons(button)
            
        self.line_start_point = None
        self.circle_center_point = None
        self.text_position = None
        self.canvas.clear_ghost_line()
        self.canvas.clear_ghost_circle()
        self.canvas.clear_ghost_text()
        
        if self.current_tool == Tool.SELECT:
            self.canvas.set_show_snap(False)
            self.canvas.set_interaction_enabled(True)
            self.canvas.set_drag_mode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.canvas.set_show_snap(True)
            self.canvas.set_interaction_enabled(False)
            self.canvas.set_drag_mode(QGraphicsView.DragMode.NoDrag)
            
        self.tool_label.setText(f"Инструмент: {self.current_tool}")

    def _finish_drawing(self):
        self.line_start_point = None
        self.circle_center_point = None
        self.text_position = None
        self.canvas.clear_ghost_line()
        self.canvas.clear_ghost_circle()
        self.canvas.clear_ghost_text()

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
            next_num = self.manager.get_next_pad_number()
            new_pad = Pad(number=next_num, shape=PadShape.CIRCLE, pad_type=PadType.SMD, x=x, y=y, width=1.5, height=1.5, drill=0.8)
            self.footprint.pads.append(new_pad)
            self.manager.add_model(new_pad)
            self.canvas.set_interaction_enabled(False)
            self.show_log(f'элемент "площадка" #{next_num} установлен')
            
        elif self.current_tool == Tool.ADD_LINE:
            if self.line_start_point is None:
                self.line_start_point = (x, y)
                self.canvas.set_ghost_line(x, y, x, y)
            else:
                start_x, start_y = self.line_start_point
                new_line = Line(start_x, start_y, x, y)
                self.footprint.lines.append(new_line)
                self.manager.add_model(new_line)
                self.canvas.set_interaction_enabled(False)
                self.line_start_point = (x, y)
                self.canvas.set_ghost_line(x, y, x, y)
                self.show_log('элемент "линия" установлен')

        elif self.current_tool == Tool.ADD_CIRCLE:
            if self.circle_center_point is None:
                self.circle_center_point = (x, y)
                self.canvas.set_ghost_circle(x, y, 0.0)
            else:
                cx, cy = self.circle_center_point
                r = math.sqrt((x - cx)**2 + (y - cy)**2)
                r = round(r / self.canvas.grid_size) * self.canvas.grid_size
                if r > 0:
                    new_circle = Circle(cx, cy, r)
                    self.footprint.circles.append(new_circle)
                    self.manager.add_model(new_circle)
                    self.canvas.set_interaction_enabled(False)
                    self.show_log('элемент "окружность" установлен')
                self.circle_center_point = None
                self.canvas.clear_ghost_circle()

        elif self.current_tool == Tool.ADD_TEXT:
            self.text_position = (x, y)
            self.canvas.set_ghost_text(x, y, "", 0.2, True)
            self._show_text_dialog()

    def _show_text_dialog(self):
        dialog = TextDialog(self)
        dialog.text_changed.connect(lambda text: self.canvas.set_ghost_text(*self.text_position, text, dialog.get_size(), dialog.get_visible()))
        dialog.size_changed.connect(lambda size: self.canvas.set_ghost_text(*self.text_position, dialog.get_text(), size, dialog.get_visible()))
        dialog.visible_changed.connect(lambda visible: self.canvas.set_ghost_text(*self.text_position, dialog.get_text(), dialog.get_size(), visible))
        
        if dialog.exec() == QDialog.Accepted:
            text = dialog.get_text()
            size = dialog.get_size()
            visible = dialog.get_visible()
            if text:
                new_text = Text(self.text_position[0], self.text_position[1], text, size, visible)
                self.footprint.texts.append(new_text)
                self.manager.add_model(new_text)
                self.canvas.set_interaction_enabled(False)
                self.show_log('элемент "текст" установлен')
        
        self.text_position = None
        self.canvas.clear_ghost_text()

    def _on_mouse_moved(self, x, y):
        self._current_mouse_scene_pos = QPointF(x, y)
        self.coords_label.setText(f"X: {x:.4f}, Y: {y:.4f}")
        
        if self.current_tool == Tool.ADD_LINE and self.line_start_point:
            self.canvas.set_ghost_line(self.line_start_point[0], self.line_start_point[1], x, y)
        elif self.current_tool == Tool.ADD_CIRCLE and self.circle_center_point:
            cx, cy = self.circle_center_point
            r = math.sqrt((x - cx)**2 + (y - cy)**2)
            r = round(r / self.canvas.grid_size) * self.canvas.grid_size
            self.canvas.set_ghost_circle(cx, cy, r)
        else:
            self.canvas.clear_ghost_line()
            self.canvas.clear_ghost_circle()

    def _on_selection_changed(self):
        selected_items = self.canvas.scene.selectedItems()
        has_selection = len(selected_items) > 0
        self.right_panel.btn_delete.setEnabled(has_selection)
        
        if len(selected_items) == 1:
            item = selected_items[0]
            if isinstance(item, (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem, TextGraphicsItem)):
                self.right_panel.properties_panel.set_object(item.model)
            else:
                self.right_panel.properties_panel.clear_panel()
        else:
            self.right_panel.properties_panel.clear_panel()

    def _delete_selected(self):
        selected_items = self.canvas.scene.selectedItems()
        for item in selected_items:
            if isinstance(item, (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem, TextGraphicsItem)):
                self.footprint.pads.remove(item.model) if item.model in self.footprint.pads else None
                self.footprint.lines.remove(item.model) if item.model in self.footprint.lines else None
                self.footprint.circles.remove(item.model) if item.model in self.footprint.circles else None
                self.footprint.texts.remove(item.model) if item.model in self.footprint.texts else None
                self.manager.remove_model(item.model)
                
        self.right_panel.btn_delete.setEnabled(False)
        self.right_panel.properties_panel.clear_panel()
        self.show_log("элементы удалены")

    def _copy_selected(self):
        self.clipboard = []
        for item in self.canvas.scene.selectedItems():
            if isinstance(item, (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem, TextGraphicsItem)):
                self.clipboard.append(copy.deepcopy(item.model))
        if self.clipboard:
            self.show_log("(буфер обмена) элементы скопированы")

    def _paste_from_clipboard(self):
        if not self.clipboard:
            return
        self.canvas.scene.clearSelection()
        
        center_x, center_y = 0, 0
        count = 0
        for model in self.clipboard:
            if isinstance(model, Pad):
                center_x += model.x; center_y += model.y; count += 1
            elif isinstance(model, Line):
                center_x += (model.x1 + model.x2)/2; center_y += (model.y1 + model.y2)/2; count += 1
            elif isinstance(model, Circle):
                center_x += model.x; center_y += model.y; count += 1
            elif isinstance(model, Text):
                center_x += model.x; center_y += model.y; count += 1
                
        if count > 0:
            center_x /= count
            center_y /= count
            
        dx = self._current_mouse_scene_pos.x() - center_x
        dy = self._current_mouse_scene_pos.y() - center_y
        dx = round(dx / self.canvas.grid_size) * self.canvas.grid_size
        dy = round(dy / self.canvas.grid_size) * self.canvas.grid_size
        
        for model in self.clipboard:
            new_model = copy.deepcopy(model)
            new_model.uid = str(uuid.uuid4())
            
            if isinstance(new_model, Pad):
                new_model.x += dx; new_model.y += dy
            elif isinstance(new_model, Line):
                new_model.x1 += dx; new_model.y1 += dy
                new_model.x2 += dx; new_model.y2 += dy
            elif isinstance(new_model, Circle):
                new_model.x += dx; new_model.y += dy
            elif isinstance(new_model, Text):
                new_model.x += dx; new_model.y += dy
            
            if isinstance(new_model, Pad):
                self.footprint.pads.append(new_model)
            elif isinstance(new_model, Line):
                self.footprint.lines.append(new_model)
            elif isinstance(new_model, Circle):
                self.footprint.circles.append(new_model)
            elif isinstance(new_model, Text):
                self.footprint.texts.append(new_model)
            
            item = self.manager.add_model(new_model)
            item.setSelected(True)
                
        self.show_log("(буфер обмена) элементы установлены")

    def handle_global_key(self, event):
        vk = event.nativeVirtualKey()
        modifiers = event.modifiers()
        
        if event.type() == QEvent.Type.KeyPress:
            if vk in PAN_KEYS:
                self.canvas.pressed_keys.add(vk)
                if not self.canvas.pan_timer.isActive():
                    self.canvas.pan_timer.start()
                return True
            elif vk == VK_ESCAPE:
                self._finish_drawing()
                self.canvas.scene.clearSelection()
                self.right_panel.btn_select.setChecked(True)
                self._on_tool_button_clicked(self.right_panel.btn_select)
                return True
            elif vk == VK_DELETE:
                self._delete_selected()
                return True
            elif vk == VK_F1:
                self._change_grid_step(-1)
                return True
            elif vk == VK_F2:
                self._change_grid_step(1)
                return True
            elif vk == VK_C and (modifiers & Qt.KeyboardModifier.ControlModifier):
                self._copy_selected()
                return True
            elif vk == VK_V and (modifiers & Qt.KeyboardModifier.ControlModifier):
                self._paste_from_clipboard()
                return True
                
        elif event.type() == QEvent.Type.KeyRelease:
            if vk in PAN_KEYS:
                self.canvas.pressed_keys.discard(vk)
                if not self.canvas.pressed_keys:
                    self.canvas.pan_timer.stop()
                return True
                
        return False