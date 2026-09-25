from PySide6.QtWidgets import (QMainWindow, QDockWidget, QWidget, QLabel, QToolBar,
                               QStatusBar, QComboBox, QApplication, QGraphicsView)
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtCore import Qt, QEvent, QSettings

from constants import (Tool, Steps, Styles, VK_ESCAPE, VK_DELETE, VK_F1, VK_F2,
                       VK_C, VK_V, VK_S, VK_R, PAN_KEYS, apply_theme)
from footprint_editor.core.models import (Footprint, Pad, PadShape, PadType, Line,
                                          Circle, Arc, Text, TextType)
from footprint_editor.core.manager import FootprintManager
from footprint_editor.core.kicad_parser import mm_to_kicad
from footprint_editor.ui.canvas import FootprintCanvas
from footprint_editor.ui.shortcuts import GlobalKeyFilter
from footprint_editor.ui.commands import CommandHandler
from footprint_editor.ui.panels.right_panel import RightPanel
from footprint_editor.ui.panels.library_panel import LibraryPanel
from footprint_editor.graphics.pad_item import PadGraphicsItem
from footprint_editor.graphics.line_item import LineGraphicsItem
from footprint_editor.graphics.circle_item import CircleGraphicsItem
from footprint_editor.graphics.arc_item import ArcGraphicsItem
from footprint_editor.graphics.text_item import TextGraphicsItem

SETTINGS_ORG = "TraceCAD"
SETTINGS_APP = "TraceCAD"
SETTINGS_KEY_LIBS = "library_paths"
SETTINGS_KEY_THEME = "theme"

LEFT_PANEL_MIN_WIDTH = 160


class FootprintEditorWindow(QMainWindow):
    def __init__(self, footprint=None):
        super().__init__()

        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.theme = self._settings.value(SETTINGS_KEY_THEME, "dark", type=str)
        apply_theme(self.theme)

        # ---- domain state ----
        self.footprint = footprint or Footprint(name="New_Footprint")
        self.current_module_name = self.footprint.name
        self.unsaved_modules = {}
        self._modified = False

        # ---- library state ----
        self.library_paths = []
        self.library_modules = {}
        self.current_library_path = None

        # ---- tool state ----
        self.current_tool = Tool.SELECT
        self.line_start_point = None
        self.circle_center_point = None
        self.arc_center_point = None
        self.arc_start_point = None
        self.text_position = None

        self.setWindowTitle(f"TraceCAD - Редактор корпусов: {self.footprint.name}")
        self.resize(1000, 700)

        self.commands = CommandHandler(self)

        self._init_menu()
        self._init_canvas()
        self._init_docks()
        self._init_toolbar()
        self._init_statusbar()
        self._init_shortcuts()
        self._wire_panels()

        self.commands.ensure_reference_and_value()

        self.load_library_paths()
        self.refresh_library_list()

        self.resizeDocks([self.library_dock], [LEFT_PANEL_MIN_WIDTH], Qt.Orientation.Horizontal)
        self.resizeDocks([self.properties_dock], [LEFT_PANEL_MIN_WIDTH], Qt.Orientation.Horizontal)

        self._apply_theme()

    # =========================================================
    # init steps
    # =========================================================

    def _init_menu(self):
        menubar = self.menuBar()

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

        view_menu = menubar.addMenu("Вид")
        theme_menu = view_menu.addMenu("Тема")
        group = QActionGroup(self)
        group.setExclusive(True)

        dark = QAction("Тёмная", self, checkable=True)
        dark.setChecked(self.theme == "dark")
        dark.triggered.connect(lambda: self._set_theme("dark"))
        group.addAction(dark)
        theme_menu.addAction(dark)

        light = QAction("Светлая", self, checkable=True)
        light.setChecked(self.theme == "light")
        light.triggered.connect(lambda: self._set_theme("light"))
        group.addAction(light)
        theme_menu.addAction(light)

        self._theme_group = group

    def _init_canvas(self):
        self.canvas = FootprintCanvas(self)
        self.setCentralWidget(self.canvas)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.canvas.canvas_clicked.connect(self.commands.on_canvas_clicked)
        self.canvas.mouse_moved.connect(self.commands.on_mouse_moved)
        self.canvas.finish_drawing.connect(self.finish_drawing)
        self.canvas.scene.selectionChanged.connect(self._on_selection_changed)
        self.canvas.content_changed.connect(self.mark_dirty)

        self.manager = FootprintManager(self.footprint, self.canvas.scene, self.canvas)

    def _init_docks(self):
        # right
        self.properties_dock = QDockWidget("", self)
        self.properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.right_panel = RightPanel()
        self.properties_dock.setWidget(self.right_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        self._hide_dock_title(self.properties_dock)

        # left
        self.library_dock = QDockWidget("", self)
        self.library_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.library_panel = LibraryPanel()
        self.library_dock.setWidget(self.library_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.library_dock)
        self._hide_dock_title(self.library_dock)

    def _init_toolbar(self):
        toolbar = QToolBar("Настройки вида", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addWidget(QLabel(" Шаг сетки (мм): "))
        self.grid_combo = QComboBox()
        self.grid_combo.addItems(Steps.GRID)
        self.grid_combo.setCurrentText(Steps.DEFAULT_GRID)
        self.grid_combo.currentTextChanged.connect(self._on_grid_changed)
        toolbar.addWidget(self.grid_combo)

        toolbar.addSeparator()
        self.zoom_label = QLabel(" 100% ")
        toolbar.addWidget(self.zoom_label)

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
        self._active_tool_button = self.right_panel.btn_select

        rp = self.right_panel
        rp.btn_select.clicked.connect(lambda: self._set_tool(Tool.SELECT, rp.btn_select))
        rp.btn_add_pad.clicked.connect(lambda: self._set_tool(Tool.ADD_PAD, rp.btn_add_pad))
        rp.btn_add_line.clicked.connect(lambda: self._set_tool(Tool.ADD_LINE, rp.btn_add_line))
        rp.btn_add_circle.clicked.connect(lambda: self._set_tool(Tool.ADD_CIRCLE, rp.btn_add_circle))
        rp.btn_add_arc.clicked.connect(lambda: self._set_tool(Tool.ADD_ARC, rp.btn_add_arc))
        rp.btn_add_text.clicked.connect(lambda: self._set_tool(Tool.ADD_TEXT, rp.btn_add_text))
        rp.btn_delete.clicked.connect(self.commands.delete_selected)
        rp.properties_panel.btn_apply.clicked.connect(self.mark_dirty)

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
        self.log_label.setStyleSheet(Styles.LOG_LABEL)
        self.right_panel.update_tool_buttons(self._active_tool_button)
        self.canvas.scene.update()
        self.canvas.viewport().update()

    def _set_theme(self, name):
        if name == self.theme:
            return
        self.theme = name
        self._settings.setValue(SETTINGS_KEY_THEME, name)
        self._settings.sync()
        apply_theme(self.theme)
        self._apply_theme()
        self.show_log(f"Тема: {'светлая' if name == 'light' else 'тёмная'}")

    # =========================================================
    # tool management
    # =========================================================

    def _set_tool(self, tool, button):
        self.current_tool = tool
        self._active_tool_button = button
        self.right_panel.update_tool_buttons(button)

        self.line_start_point = None
        self.circle_center_point = None
        self.arc_center_point = None
        self.arc_start_point = None
        self.text_position = None
        self.canvas.clear_ghost_line()
        self.canvas.clear_ghost_circle()
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
        self.canvas.clear_ghost_text()

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
        self.setWindowTitle(f"TraceCAD - Редактор корпусов: {module.name}")
        self.refresh_module_list_display()
        self.show_log(f"Загружен модуль: {module.name}")

    def stash_current_module(self):
        if self._modified:
            self.unsaved_modules[self.current_module_name] = self.footprint

    def mark_dirty(self):
        self._modified = True
        self.unsaved_modules[self.current_module_name] = self.footprint
        self.refresh_module_list_display()

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
        self.right_panel.btn_delete.setEnabled(has_sel)

        if len(items) == 1:
            item = items[0]
            if isinstance(item, (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem,
                                 ArcGraphicsItem, TextGraphicsItem)):
                if getattr(item.model, 'locked', False):
                    self.right_panel.btn_delete.setEnabled(False)
                self.right_panel.properties_panel.set_object(item.model)
            else:
                self.right_panel.properties_panel.clear_panel()
        else:
            self.right_panel.properties_panel.clear_panel()

    def handle_global_key(self, event):
        vk = event.nativeVirtualKey()
        ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)

        if event.type() == QEvent.Type.KeyPress:
            if ctrl:
                if vk == VK_C:
                    self.commands.copy_selected(); return True
                if vk == VK_V:
                    self.commands.paste(); return True
                if vk == VK_S:
                    self.commands.save_current(); return True
                return False

            if vk == VK_R:
                self.commands.rotate_selected(); return True
            if vk in PAN_KEYS:
                self.canvas.pressed_keys.add(vk)
                if not self.canvas.pan_timer.isActive():
                    self.canvas.pan_timer.start()
                return True
            if vk == VK_ESCAPE:
                self.finish_drawing()
                self.canvas.scene.clearSelection()
                self.right_panel.btn_select.setChecked(True)
                self._set_tool(Tool.SELECT, self.right_panel.btn_select)
                return True
            if vk == VK_DELETE:
                self.commands.delete_selected(); return True
            if vk == VK_F1:
                self._change_grid_step(-1); return True
            if vk == VK_F2:
                self._change_grid_step(1); return True

        elif event.type() == QEvent.Type.KeyRelease:
            if vk in PAN_KEYS:
                self.canvas.pressed_keys.discard(vk)
                if not self.canvas.pressed_keys:
                    self.canvas.pan_timer.stop()
                return True

        return False


# =========================================================
# kicad serialization (pure function)
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

    for text in fp.texts:
        if text.text_type == TextType.REFERENCE:
            idx = 0
        elif text.text_type == TextType.VALUE:
            idx = 1
        else:
            continue
        x_k = mm_to_kicad(text.x)
        y_k = mm_to_kicad(text.y)
        size_k = mm_to_kicad(text.size)
        vis = 'V' if text.visible else 'I'
        lines.append(f'T{idx} {x_k} {y_k} {size_k} {size_k} 0 120 N {vis} 21 N "{text.text}"')

    for line in fp.lines:
        lines.append(
            f"DS {mm_to_kicad(line.x1)} {mm_to_kicad(line.y1)} "
            f"{mm_to_kicad(line.x2)} {mm_to_kicad(line.y2)} {mm_to_kicad(line.width)} 21"
        )

    for circle in fp.circles:
        x_c = mm_to_kicad(circle.x)
        y_c = mm_to_kicad(circle.y)
        r_k = mm_to_kicad(circle.radius)
        lines.append(f"DC {x_c} {y_c} {x_c + r_k} {y_c} {mm_to_kicad(circle.width)} 21")

    for arc in fp.arcs:
        lines.append(
            f"DA {mm_to_kicad(arc.cx)} {mm_to_kicad(arc.cy)} "
            f"{mm_to_kicad(arc.sx)} {mm_to_kicad(arc.sy)} "
            f"{int(round(arc.angle * 10))} {mm_to_kicad(arc.width)} 21"
        )

    for pad in fp.pads:
        shape_map = {PadShape.RECT: 'R', PadShape.CIRCLE: 'C', PadShape.OVAL: 'O'}
        shape_char = shape_map.get(pad.shape, 'C')
        attr = 'STD' if pad.pad_type == PadType.THT else 'SMD'
        lines.append("$PAD")
        lines.append(f'Sh "{pad.number}" {shape_char} '
                     f'{mm_to_kicad(pad.width)} {mm_to_kicad(pad.height)} 0 0 0')
        lines.append(f"Dr {mm_to_kicad(pad.drill or 0)} 0 0")
        lines.append(f"At {attr} N 00E0FFFF")
        lines.append('Ne 0 ""')
        lines.append(f"Po {mm_to_kicad(pad.x)} {mm_to_kicad(pad.y)}")
        lines.append("$EndPAD")

    lines.append(f"$EndMODULE  {fp.name}")
    return "\n".join(lines)