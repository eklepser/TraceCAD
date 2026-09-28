from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QDockWidget, QWidget, QLabel, QToolBar,
                               QStatusBar, QComboBox, QApplication, QGraphicsView,
                               QVBoxLayout, QMenuBar)
from PySide6.QtGui import QAction, QActionGroup, QGuiApplication
from PySide6.QtCore import Qt, QEvent, QSettings

from constants import (Tool, Steps, Styles, VK_ESCAPE, VK_DELETE, VK_F1, VK_F2, VK_F3,
                       VK_F11, VK_C, VK_V, VK_S, VK_R, VK_Y, VK_Z,
                       VK_1, VK_2, VK_3, VK_4, VK_5, PAN_KEYS, apply_theme)
from footprint_editor.core.models import (Footprint, Pad, PadShape, PadType, Line,
                                          Circle, Arc, Text, TextType)
from footprint_editor.core.manager import FootprintManager
from footprint_editor.core.kicad_parser import (
    mm_to_kicad, parse_kicad_mod, INTERNAL_TO_KICAD_LAYER, layer_to_id
)
from footprint_editor.core.history import History
from footprint_editor.ui.canvas import FootprintCanvas
from footprint_editor.ui.shortcuts import GlobalKeyFilter
from footprint_editor.ui.commands import CommandHandler
from footprint_editor.ui.panels.right_panel import RightPanel
from footprint_editor.ui.panels.library_panel import LibraryPanel
from footprint_editor.ui.panels.drawing_tool_bar import DrawingToolBar
from footprint_editor.ui.panels.aux_bar import AuxBar
from footprint_editor.graphics.pad_item import PadGraphicsItem
from footprint_editor.graphics.line_item import LineGraphicsItem
from footprint_editor.graphics.circle_item import CircleGraphicsItem
from footprint_editor.graphics.arc_item import ArcGraphicsItem
from footprint_editor.graphics.text_item import TextGraphicsItem


SETTINGS_ORG = "TraceCAD"
SETTINGS_APP = "TraceCAD"
SETTINGS_KEY_LIBS = "library_paths"
SETTINGS_KEY_GRID_MODE = "grid_mode"
SETTINGS_KEY_LAST_LIB = "last_library"
SETTINGS_KEY_LAST_MODULE = "last_module"

LEFT_PANEL_MIN_WIDTH = 160

GRID_SERIES = {
    "1x": Steps.GRID_1X,
    "1.27x": Steps.GRID_127X,
}
GRID_SERIES_LABEL = {"1x": "1x", "1.27x": "1.27x"}


class FootprintEditorWindow(QMainWindow):
    def __init__(self, footprint=None):
        super().__init__()

        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        apply_theme()

        self.grid_mode = self._settings.value(SETTINGS_KEY_GRID_MODE, "1x", type=str)
        if self.grid_mode not in GRID_SERIES:
            self.grid_mode = "1x"

        self.footprint = footprint or Footprint(name="New_Footprint")
        self.current_module_name = self.footprint.name
        self.unsaved_modules = {}
        self._modified = False

        self.library_paths = []
        self.library_modules = {}
        self.current_library_path = None

        self.current_tool = Tool.ADD_LINE
        self.line_start_point = None
        self.circle_center_point = None
        self.arc_center_point = None
        self.arc_start_point = None
        self.text_position = None

        self.history = History()

        self._apply_startup_geometry()
        self._update_window_title()

        self.commands = CommandHandler(self)

        self._init_canvas()
        self._init_toolbar()
        self._init_menu()
        self._init_docks()
        self._init_statusbar()
        self._init_shortcuts()
        self._wire_panels()

        self.commands.ensure_reference_and_value()

        self.load_library_paths()
        self.refresh_library_list()
        self._apply_grid_series(self.grid_mode, initial=True)

        self.resizeDocks([self.library_dock], [LEFT_PANEL_MIN_WIDTH], Qt.Orientation.Horizontal)
        self.resizeDocks([self.properties_dock], [LEFT_PANEL_MIN_WIDTH], Qt.Orientation.Horizontal)

        self._apply_theme()

        self.history.reset(self.footprint)
        self._update_history_buttons()
        self._set_tool(Tool.ADD_LINE)
        self.tool_bar.set_active(Tool.ADD_LINE)

        self._restore_last_session()

    def _apply_startup_geometry(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 800)
            return
        avail = screen.availableGeometry()
        self.setGeometry(avail)
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)

    def _update_window_title(self):
        if self.current_library_path:
            lib_name = Path(self.current_library_path).stem
            title = f"TraceCAD: {lib_name}/{self.footprint.name}"
        else:
            title = f"TraceCAD: {self.footprint.name}"
        self.setWindowTitle(title)

    # =========================================================
    # init steps
    # =========================================================

    def _init_canvas(self):
        self.canvas = FootprintCanvas(self)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.canvas.canvas_clicked.connect(self.commands.on_canvas_clicked)
        self.canvas.mouse_moved.connect(self.commands.on_mouse_moved)
        self.canvas.finish_drawing.connect(self.finish_drawing)
        self.canvas.scene.selectionChanged.connect(self._on_selection_changed)
        self.canvas.content_changed.connect(self.commit_history)

        self.manager = FootprintManager(self.footprint, self.canvas.scene, self.canvas)

        self.aux_bar = AuxBar()
        self.aux_bar.undo_requested.connect(self.undo)
        self.aux_bar.redo_requested.connect(self.redo)
        self.aux_bar.select_requested.connect(lambda: self._set_tool(Tool.SELECT))
        self.aux_bar.delete_requested.connect(self.commands.delete_selected)

        self.tool_bar = DrawingToolBar()
        self.tool_bar.tool_selected.connect(self._on_drawing_tool)

        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self.aux_bar, 0)
        v.addWidget(self.canvas, 1)
        v.addWidget(self.tool_bar, 0)
        self.setCentralWidget(central)

    def _init_toolbar(self):
        toolbar = QToolBar("Верхняя панель", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        self.toolbar = toolbar

        toolbar.addWidget(QLabel("Сетка: "))
        self.grid_series_combo = QComboBox()
        for mode, label in GRID_SERIES_LABEL.items():
            self.grid_series_combo.addItem(label, mode)
        idx = self.grid_series_combo.findData(self.grid_mode)
        if idx >= 0:
            self.grid_series_combo.setCurrentIndex(idx)
        self.grid_series_combo.currentIndexChanged.connect(
            lambda i: self._apply_grid_series(self.grid_series_combo.itemData(i))
        )
        toolbar.addWidget(self.grid_series_combo)

        toolbar.addWidget(QLabel(" Шаг: "))
        self.grid_combo = QComboBox()
        self.grid_combo.currentTextChanged.connect(self._on_grid_changed)
        toolbar.addWidget(self.grid_combo)

        toolbar.addSeparator()
        self.zoom_label = QLabel(" 100% ")
        toolbar.addWidget(self.zoom_label)

    def _init_menu(self):
        menubar = QMenuBar(self)
        menubar.setNativeMenuBar(False)
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("Файл")
        lib_menu = file_menu.addMenu("Библиотека")
        lib_menu.addAction("Создать", self.commands.create_library)
        lib_menu.addAction("Открыть", self.commands.open_library)
        lib_menu.addAction("Управление", self.commands.manage_libraries)

        mod_menu = file_menu.addMenu("Корпус")
        mod_menu.addAction("Создать", self.commands.new_module)
        mod_menu.addAction("Открыть", self.commands.open_module_file)

        file_menu.addSeparator()
        act_exit = QAction("Выход", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        edit_menu = menubar.addMenu("Правка")
        act_undo = QAction("Отменить", self)
        act_undo.setShortcut("Ctrl+Z")
        act_undo.triggered.connect(self.undo)
        edit_menu.addAction(act_undo)

        act_redo = QAction("Повторить", self)
        act_redo.setShortcut("Ctrl+Shift+Z")
        act_redo.triggered.connect(self.redo)
        edit_menu.addAction(act_redo)

        view_menu = menubar.addMenu("Вид")
        grid_menu = view_menu.addMenu("Шаг сетки")
        self._grid_group = QActionGroup(self)
        self._grid_group.setExclusive(True)
        self._grid_actions = {}
        for mode, label in GRID_SERIES_LABEL.items():
            act = QAction(label, self, checkable=True)
            act.setChecked(mode == self.grid_mode)
            act.triggered.connect(lambda _=False, m=mode: self._apply_grid_series(m))
            self._grid_group.addAction(act)
            grid_menu.addAction(act)
            self._grid_actions[mode] = act

        act_full = QAction("Полный экран", self)
        act_full.setShortcut("F11")
        act_full.triggered.connect(self.toggle_fullscreen)
        view_menu.addSeparator()
        view_menu.addAction(act_full)

    def _init_docks(self):
        self.properties_dock = QDockWidget("", self)
        self.properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.right_panel = RightPanel()
        self.properties_dock.setWidget(self.right_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        self._hide_dock_title(self.properties_dock)

        self.library_dock = QDockWidget("", self)
        self.library_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.library_panel = LibraryPanel()
        self.library_dock.setWidget(self.library_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.library_dock)
        self._hide_dock_title(self.library_dock)

    def _init_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.log_label = QLabel("Готово.")
        sb.addWidget(self.log_label)
        self.coords_label = QLabel("X: 0.0000, Y: 0.0000")
        sb.addPermanentWidget(self.coords_label)

    def _init_shortcuts(self):
        self.key_filter = GlobalKeyFilter(self)
        QApplication.instance().installEventFilter(self.key_filter)

    def _wire_panels(self):
        rp = self.right_panel
        rp.properties_panel.btn_apply.clicked.connect(self.commit_history)

        lp = self.library_panel
        lp.add_library_requested.connect(self.commands.add_library)
        lp.add_module_requested.connect(self.commands.new_module)
        lp.library_selected.connect(self.commands.select_library)
        lp.module_selected.connect(self.commands.select_module)

    def _hide_dock_title(self, dock):
        empty = QWidget()
        empty.setFixedHeight(0)
        dock.setTitleBarWidget(empty)

    # =========================================================
    # session persistence
    # =========================================================

    def _restore_last_session(self):
        last_lib = self._settings.value(SETTINGS_KEY_LAST_LIB, "", type=str)
        last_mod = self._settings.value(SETTINGS_KEY_LAST_MODULE, "", type=str)
        if not last_lib or last_lib not in self.library_paths:
            return
        try:
            if last_lib not in self.library_modules:
                footprints = parse_kicad_mod(last_lib)
                self.library_modules[last_lib] = {fp.name: fp for fp in footprints}
            self.current_library_path = last_lib
            names = list(self.library_modules[last_lib].keys())
            self.library_panel.set_modules(names)
            self.refresh_module_list_display()

            if last_mod and last_mod in self.library_modules[last_lib]:
                import copy as _copy
                module = _copy.deepcopy(self.library_modules[last_lib][last_mod])
                self.load_footprint(module)
                self.show_log(f"Восстановлен: {Path(last_lib).stem}/{last_mod}")
            else:
                self._update_window_title()
        except Exception:
            pass

    def _save_last_session(self):
        if self.current_library_path:
            self._settings.setValue(SETTINGS_KEY_LAST_LIB, self.current_library_path)
            self._settings.setValue(SETTINGS_KEY_LAST_MODULE, self.current_module_name)
        else:
            self._settings.setValue(SETTINGS_KEY_LAST_LIB, "")
            self._settings.setValue(SETTINGS_KEY_LAST_MODULE, "")
        self._settings.sync()

    def closeEvent(self, event):
        self._save_last_session()
        super().closeEvent(event)

    # =========================================================
    # grid series
    # =========================================================

    def _apply_grid_series(self, mode, initial=False):
        if mode not in GRID_SERIES:
            return
        self.grid_mode = mode
        self._settings.setValue(SETTINGS_KEY_GRID_MODE, mode)
        self._settings.sync()

        for m, act in self._grid_actions.items():
            act.setChecked(m == mode)

        idx = self.grid_series_combo.findData(mode)
        if idx >= 0 and self.grid_series_combo.currentIndex() != idx:
            self.grid_series_combo.blockSignals(True)
            self.grid_series_combo.setCurrentIndex(idx)
            self.grid_series_combo.blockSignals(False)

        values = GRID_SERIES[mode]
        self.grid_combo.blockSignals(True)
        self.grid_combo.clear()
        self.grid_combo.addItems(values)
        default = "1.000" if mode == "1x" else "1.270"
        self.grid_combo.setCurrentText(default if default in values else values[0])
        self.grid_combo.blockSignals(False)

        self.canvas.set_grid_size(float(self.grid_combo.currentText()))
        if not initial:
            self.show_log(f"Ряд сетки: {GRID_SERIES_LABEL[mode]}")

    def _toggle_grid_series(self):
        self._apply_grid_series("1.27x" if self.grid_mode == "1x" else "1x")

    # =========================================================
    # theme
    # =========================================================

    def _apply_theme(self):
        app = QApplication.instance()
        app.setStyleSheet(Styles.TOOLTIP)
        self.setStyleSheet(Styles.MAIN_WINDOW)
        self.canvas.apply_theme()
        self.right_panel.setStyleSheet(Styles.RIGHT_PANEL)
        self.right_panel.apply_theme()
        self.library_panel.apply_theme()
        self.tool_bar.apply_theme()
        self.aux_bar.apply_theme()
        self.log_label.setStyleSheet(Styles.LOG_LABEL)
        self.canvas.scene.update()
        self.canvas.viewport().update()

    # =========================================================
    # tool management
    # =========================================================

    def _on_drawing_tool(self, tool):
        self._set_tool(tool)
        self.aux_bar.set_select_active(False)

    def _on_right_tool(self, tool):
        self._set_tool(tool)
        if tool != Tool.SELECT:
            self.tool_bar.set_active(tool)

    def _set_tool(self, tool):
        self.current_tool = tool

        if tool == Tool.SELECT:
            self.aux_bar.set_select_active(True)
            self.tool_bar.clear_active()
        else:
            self.aux_bar.set_select_active(False)
            self.tool_bar.set_active(tool)

        self.line_start_point = None
        self.circle_center_point = None
        self.arc_center_point = None
        self.arc_start_point = None
        self.text_position = None
        self.canvas.clear_ghost_line()
        self.canvas.clear_ghost_circle()
        self.canvas.clear_ghost_arc()
        self.canvas.clear_ghost_text()

        if tool == Tool.SELECT:
            self.canvas.set_show_snap(False)
            self.canvas.set_interaction_enabled(True)
            self.canvas.set_drag_mode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.canvas.set_show_snap(True)
            self.canvas.set_interaction_enabled(False)
            self.canvas.set_drag_mode(QGraphicsView.DragMode.NoDrag)

        self.show_log(f"Инструмент: {tool}")

    def finish_drawing(self):
        self.line_start_point = None
        self.circle_center_point = None
        self.arc_center_point = None
        self.arc_start_point = None
        self.text_position = None
        self.canvas.clear_ghost_line()
        self.canvas.clear_ghost_circle()
        self.canvas.clear_ghost_arc()
        self.canvas.clear_ghost_text()

    # =========================================================
    # fullscreen
    # =========================================================

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        else:
            self.showFullScreen()

    # =========================================================
    # history
    # =========================================================

    def commit_history(self, *_args):
        self._modified = True
        self.unsaved_modules[self.current_module_name] = self.footprint
        self.refresh_module_list_display()

        self.history.push(self.footprint)
        self._update_history_buttons()

    def undo(self):
        snapshot = self.history.undo()
        if snapshot is None:
            return
        self._restore_footprint(snapshot)
        self._update_history_buttons()
        self.show_log("отменено")

    def redo(self):
        snapshot = self.history.redo()
        if snapshot is None:
            return
        self._restore_footprint(snapshot)
        self._update_history_buttons()
        self.show_log("повторено")

    def _restore_footprint(self, snapshot):
        name = self.current_module_name
        self.footprint = snapshot
        self.footprint.name = name
        self.manager.footprint = self.footprint

        self.canvas.scene.clear()
        self.manager.items.clear()
        for bucket in (self.footprint.pads, self.footprint.lines, self.footprint.circles,
                       self.footprint.arcs, self.footprint.texts):
            for model in bucket:
                self.manager.add_model(model)
        self.commands.ensure_reference_and_value()
        self.right_panel.properties_panel.clear_panel()
        self.unsaved_modules[self.current_module_name] = self.footprint

    def _update_history_buttons(self):
        self.aux_bar.set_undo_enabled(self.history.can_undo())
        self.aux_bar.set_redo_enabled(self.history.can_redo())

    # =========================================================
    # module lifecycle helpers
    # =========================================================

    def load_footprint(self, module, mark_unsaved=None):
        self.footprint = module
        self.manager.footprint = self.footprint
        self.canvas.scene.clear()
        self.manager.items.clear()

        for bucket in (module.pads, module.lines, module.circles, module.arcs, module.texts):
            for model in bucket:
                self.manager.add_model(model)

        self.commands.ensure_reference_and_value()

        self.current_module_name = module.name
        if mark_unsaved is None:
            mark_unsaved = module.name in self.unsaved_modules
        self._modified = mark_unsaved
        self._update_window_title()
        self.refresh_module_list_display()
        self.history.reset(self.footprint)
        self._update_history_buttons()
        self.show_log(f"Загружен модуль: {module.name}")

    def stash_current_module(self):
        if self._modified:
            self.unsaved_modules[self.current_module_name] = self.footprint

    def mark_saved(self):
        self._modified = False
        self.refresh_module_list_display()

    def refresh_module_list_display(self):
        self.library_panel.mark_unsaved(set(self.unsaved_modules.keys()))

    def build_kicad_module_text(self):
        return _build_kicad_module_text(self.footprint)

    def export_to_kicad(self, filepath):
        from datetime import datetime
        lines = [
            f"PCBNEW-LibModule-V1  {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            "# encoding utf-8",
            "$INDEX", self.footprint.name, "$EndINDEX",
            _build_kicad_module_text(self.footprint),
            "$EndLIBRARY",
        ]
        Path(filepath).write_text("\n".join(lines), encoding='utf-8')

    # =========================================================
    # library state helpers
    # =========================================================

    def load_library_paths(self):
        saved = self._settings.value(SETTINGS_KEY_LIBS, "", type=str)
        if saved:
            self.library_paths = [p for p in saved.split("\n") if p.strip()]

    def save_library_paths(self):
        self._settings.setValue(SETTINGS_KEY_LIBS, "\n".join(self.library_paths))
        self._settings.sync()

    def refresh_library_list(self):
        self.library_panel.set_libraries(self.library_paths)

    def reload_current_library(self):
        self.commands.reload_current_library()

    # =========================================================
    # UI events
    # =========================================================

    def show_log(self, text):
        self.log_label.setText(text)

    def _on_grid_changed(self, text):
        if not text:
            return
        self.canvas.set_grid_size(float(text))
        self.canvas.setFocus()

    def _change_grid_step(self, direction):
        i = self.grid_combo.currentIndex() + direction
        if 0 <= i < self.grid_combo.count():
            self.grid_combo.setCurrentIndex(i)

    def _update_zoom_label(self, zoom):
        self.zoom_label.setText(f" {int(zoom * 100)}% ")

    def _on_selection_changed(self):
        items = self.canvas.scene.selectedItems()
        has_sel = len(items) > 0
        self.aux_bar.set_delete_enabled(has_sel)

        if len(items) == 1:
            item = items[0]
            if isinstance(item, (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem,
                                 ArcGraphicsItem, TextGraphicsItem)):
                if getattr(item.model, 'locked', False):
                    self.aux_bar.set_delete_enabled(False)
                self.right_panel.properties_panel.set_object(item.model)
            else:
                self.right_panel.properties_panel.clear_panel()
        else:
            self.right_panel.properties_panel.clear_panel()

    def handle_global_key(self, event):
        vk = event.nativeVirtualKey()
        ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

        if event.type() == QEvent.Type.KeyPress:
            if ctrl and shift and vk == VK_Z:
                self.redo()
                return True
            if ctrl and vk == VK_Z:
                self.undo()
                return True
            if ctrl and vk == VK_Y:
                self.redo()
                return True

            if ctrl:
                if vk == VK_C:
                    self.commands.copy_selected()
                    return True
                if vk == VK_V:
                    self.commands.paste()
                    return True
                if vk == VK_S:
                    self.commands.save_current()
                    return True
                return False

            if vk == VK_R:
                self.commands.rotate_selected()
                return True
            if vk == VK_1:
                self._on_drawing_tool(Tool.ADD_LINE)
                self.tool_bar.set_active(Tool.ADD_LINE)
                return True
            if vk == VK_2:
                self._on_drawing_tool(Tool.ADD_PAD)
                self.tool_bar.set_active(Tool.ADD_PAD)
                return True
            if vk == VK_3:
                self._on_drawing_tool(Tool.ADD_CIRCLE)
                self.tool_bar.set_active(Tool.ADD_CIRCLE)
                return True
            if vk == VK_4:
                self._on_drawing_tool(Tool.ADD_ARC)
                self.tool_bar.set_active(Tool.ADD_ARC)
                return True
            if vk == VK_5:
                self._on_drawing_tool(Tool.ADD_TEXT)
                self.tool_bar.set_active(Tool.ADD_TEXT)
                return True
            if vk == VK_F11:
                self.toggle_fullscreen()
                return True

            if vk in PAN_KEYS:
                self.canvas.pressed_keys.add(vk)
                if not self.canvas.pan_timer.isActive():
                    self.canvas.pan_timer.start()
                return True
            if vk == VK_ESCAPE:
                self.finish_drawing()
                self.canvas.scene.clearSelection()
                self._set_tool(Tool.SELECT)
                return True
            if vk == VK_DELETE:
                self.commands.delete_selected()
                return True
            if vk == VK_F1:
                self._change_grid_step(-1)
                return True
            if vk == VK_F2:
                self._change_grid_step(1)
                return True
            if vk == VK_F3:
                self._toggle_grid_series()
                return True

        elif event.type() == QEvent.Type.KeyRelease:
            if vk in PAN_KEYS:
                self.canvas.pressed_keys.discard(vk)
                if not self.canvas.pressed_keys:
                    self.canvas.pan_timer.stop()
                return True

        return False


# =========================================================
# kicad serialization (для KiCad 2011, legacy .mod)
# =========================================================

def _build_kicad_module_text(fp):
    lines = [
        f"$MODULE {fp.name}",
        "Po 0 0 0 15 00000000 00000000 ~~",
        f"Li {fp.name}",
        "Sc 00000000",
        "AR",
        "Op 0 0 0",
    ]

    text_idx = 2
    for text in fp.texts:
        if text.text_type == TextType.REFERENCE:
            idx = 0
        elif text.text_type == TextType.VALUE:
            idx = 1
        else:
            idx = text_idx
            text_idx += 1

        x_k = mm_to_kicad(text.x)
        y_k = mm_to_kicad(text.y)
        size_k = mm_to_kicad(text.size)
        vis = 'V' if text.visible else 'I'
        lid = layer_to_id(text.layer)
        text_value = text.text if text.text else "Text"
        lines.append(
            f'T{idx} {x_k} {y_k} {size_k} {size_k} 0 120 N {vis} {lid} N "{text_value}"'
        )

    for line in fp.lines:
        lid = layer_to_id(line.layer)
        lines.append(
            f"DS {mm_to_kicad(line.x1)} {mm_to_kicad(line.y1)} "
            f"{mm_to_kicad(line.x2)} {mm_to_kicad(line.y2)} "
            f"{mm_to_kicad(line.width)} {lid}"
        )

    for circle in fp.circles:
        x_c = mm_to_kicad(circle.x)
        y_c = mm_to_kicad(circle.y)
        r_k = mm_to_kicad(circle.radius)
        lid = layer_to_id(circle.layer)
        lines.append(f"DC {x_c} {y_c} {x_c + r_k} {y_c} {mm_to_kicad(circle.width)} {lid}")

    for arc in fp.arcs:
        lid = layer_to_id(arc.layer)
        lines.append(
            f"DA {mm_to_kicad(arc.cx)} {mm_to_kicad(arc.cy)} "
            f"{mm_to_kicad(arc.sx)} {mm_to_kicad(arc.sy)} "
            f"{int(round(arc.angle * 10))} {mm_to_kicad(arc.width)} {lid}"
        )

    for pad in fp.pads:
        shape_map = {PadShape.RECT: 'R', PadShape.CIRCLE: 'C', PadShape.OVAL: 'O'}
        shape_char = shape_map.get(pad.shape, 'C')

        if pad.pad_type == PadType.STANDARD:
            attr = 'STD'
            mask = '00E0FFFF'
            drill_val = pad.drill if pad.drill else 0.8
            dr_line = f"Dr {mm_to_kicad(drill_val)} 0 0"
        elif pad.pad_type == PadType.SMD:
            attr = 'SMD'
            mask = '00888000'
            dr_line = "Dr 0 0 0"
        elif pad.pad_type == PadType.CONN:
            attr = 'CONN'
            mask = '00808000'
            dr_line = "Dr 0 0 0"
        else:
            attr = 'STD'
            mask = '00E0FFFF'
            drill_val = pad.drill if pad.drill else 0.8
            dr_line = f"Dr {mm_to_kicad(drill_val)} 0 0"

        lines.append("$PAD")
        lines.append(f'Sh "{pad.number}" {shape_char} '
                     f'{mm_to_kicad(pad.width)} {mm_to_kicad(pad.height)} 0 0 0')
        lines.append(dr_line)
        lines.append(f"At {attr} N {mask}")
        lines.append('Ne 0 ""')
        lines.append(f"Po {mm_to_kicad(pad.x)} {mm_to_kicad(pad.y)}")
        lines.append("$EndPAD")

    lines.append(f"$EndMODULE  {fp.name}")
    return "\n".join(lines)