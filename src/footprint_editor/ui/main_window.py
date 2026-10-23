from PySide6.QtWidgets import (QMainWindow, QDockWidget, QWidget, QLabel, QToolBar,
                               QStatusBar, QComboBox, QApplication, QVBoxLayout, QMenuBar)
from PySide6.QtGui import QAction, QActionGroup, QGuiApplication
from PySide6.QtCore import Qt, QSettings

from constants import (
    Tool, Styles, GRID_SERIES, GRID_SERIES_LABEL,
    SETTINGS_ORG, SETTINGS_APP,
    LEFT_PANEL_MIN_WIDTH, RIGHT_PANEL_MAX_WIDTH,
    apply_theme,
)
from footprint_editor.core.models import Footprint
from footprint_editor.core.manager import FootprintManager
from footprint_editor.core.history import History
from footprint_editor.ui.canvas import FootprintCanvas
from footprint_editor.ui.shortcuts import GlobalKeyFilter
from footprint_editor.ui.commands import CommandHandler
from footprint_editor.ui.panels.right_panel import RightPanel
from footprint_editor.ui.panels.library_panel import LibraryPanel
from footprint_editor.ui.panels.drawing_tool_bar import DrawingToolBar
from footprint_editor.ui.panels.aux_bar import AuxBar
from footprint_editor.ui.window import (
    SessionService, HistoryService, ModuleLifecycleService,
    ToolsService, GridService, StatusService, KeyboardService,
)


class FootprintEditorWindow(
    SessionService, HistoryService, ModuleLifecycleService,
    ToolsService, GridService, StatusService, KeyboardService,
    QMainWindow,
):
    def __init__(self, footprint=None):
        super().__init__()

        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        apply_theme()

        self.grid_mode = self._load_grid_mode()

        self.footprint = footprint or Footprint(name="New_Footprint")
        self.current_module_name = self.footprint.name
        self.unsaved_modules = {}
        self._modified = False

        self.library_paths = []
        self.library_modules = {}
        self.current_library_path = None

        self.current_tool = Tool.SELECT
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

        self._load_library_paths()
        self.refresh_library_list()
        self._apply_grid_series(self.grid_mode, initial=True)

        self.resizeDocks([self.library_dock], [LEFT_PANEL_MIN_WIDTH], Qt.Orientation.Horizontal)
        self.resizeDocks([self.properties_dock], [RIGHT_PANEL_MAX_WIDTH], Qt.Orientation.Horizontal)

        self._apply_theme()

        self.history.reset(self.footprint)
        self._update_history_buttons()
        self._set_tool(Tool.SELECT)

        self._restore_last_session()

    def _apply_startup_geometry(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 800)
            return
        avail = screen.availableGeometry()
        self.setGeometry(avail)
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)

    def _init_canvas(self):
        self.canvas = FootprintCanvas(self)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.canvas.canvas_clicked.connect(self.commands.on_canvas_clicked)
        self.canvas.mouse_moved.connect(self.commands.on_mouse_moved)
        self.canvas.finish_drawing.connect(self.finish_drawing)
        self.canvas.scene.selectionChanged.connect(self._on_selection_changed)
        self.canvas.content_changed.connect(self.commit_history)
        self.canvas.properties_changed.connect(self._on_properties_changed)

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
        act_lib_new = QAction("Создать", self)
        act_lib_new.triggered.connect(self.commands.create_library)
        lib_menu.addAction(act_lib_new)

        act_lib_open = QAction("Открыть", self)
        act_lib_open.triggered.connect(self.commands.open_library)
        lib_menu.addAction(act_lib_open)

        act_lib_manage = QAction("Управление", self)
        act_lib_manage.triggered.connect(self.commands.manage_libraries)
        lib_menu.addAction(act_lib_manage)

        mod_menu = file_menu.addMenu("Корпус")
        act_mod_new = QAction("Создать", self)
        act_mod_new.triggered.connect(self.commands.new_module)
        mod_menu.addAction(act_mod_new)

        act_mod_open = QAction("Открыть файл...", self)
        act_mod_open.triggered.connect(self.commands.open_module_file)
        mod_menu.addAction(act_mod_open)

        act_mod_save = QAction("Сохранить", self)
        act_mod_save.setShortcut("Ctrl+S")
        act_mod_save.triggered.connect(self.commands.save_current)
        mod_menu.addAction(act_mod_save)

        act_mod_save_as = QAction("Сохранить как...", self)
        act_mod_save_as.setShortcut("Ctrl+Shift+S")
        act_mod_save_as.triggered.connect(self.commands._save_current_as)
        mod_menu.addAction(act_mod_save_as)

        file_menu.addSeparator()

        act_exit = QAction("Выход", self)
        act_exit.setShortcut("Ctrl+Q")
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

        edit_menu.addSeparator()

        act_copy = QAction("Копировать", self)
        act_copy.setShortcut("Ctrl+C")
        act_copy.triggered.connect(self.commands.copy_selected)
        edit_menu.addAction(act_copy)

        act_paste = QAction("Вставить", self)
        act_paste.setShortcut("Ctrl+V")
        act_paste.triggered.connect(self.commands.paste)
        edit_menu.addAction(act_paste)

        act_delete = QAction("Удалить", self)
        act_delete.setShortcut("Del")
        act_delete.triggered.connect(self.commands.delete_selected)
        edit_menu.addAction(act_delete)

        edit_menu.addSeparator()

        act_rotate = QAction("Повернуть на 90°", self)
        act_rotate.setShortcut("R")
        act_rotate.triggered.connect(self.commands.rotate_selected)
        edit_menu.addAction(act_rotate)

        edit_menu.addSeparator()

        act_select_all = QAction("Выделить всё", self)
        act_select_all.setShortcut("Ctrl+A")
        act_select_all.triggered.connect(self._select_all)
        edit_menu.addAction(act_select_all)

        view_menu = menubar.addMenu("Вид")

        self.act_show_grid = QAction("Показывать сетку", self, checkable=True)
        self.act_show_grid.setChecked(True)
        self.act_show_grid.setShortcut("G")
        self.act_show_grid.triggered.connect(self._toggle_grid)
        view_menu.addAction(self.act_show_grid)

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

    def _toggle_grid(self):
        self.canvas.show_grid = self.act_show_grid.isChecked()
        self.canvas.viewport().update()

    def _select_all(self):
        for item in self.canvas.scene.items():
            if hasattr(item, 'model') and not getattr(item.model, 'locked', False):
                item.setSelected(True)

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
        lp.module_rename_requested.connect(self.commands.rename_module)
        lp.module_delete_requested.connect(self.commands.delete_module)

    def _hide_dock_title(self, dock):
        empty = QWidget()
        empty.setFixedHeight(0)
        dock.setTitleBarWidget(empty)

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

    def _on_selection_changed(self):
        from footprint_editor.graphics.pad_item import PadGraphicsItem
        from footprint_editor.graphics.line_item import LineGraphicsItem
        from footprint_editor.graphics.circle_item import CircleGraphicsItem
        from footprint_editor.graphics.arc_item import ArcGraphicsItem
        from footprint_editor.graphics.text_item import TextGraphicsItem

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

    def _on_properties_changed(self, model):
        panel = self.right_panel.properties_panel
        if panel.current_object == model:
            panel.refresh_values()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        else:
            self.showFullScreen()

    def refresh_library_list(self):
        self.library_panel.set_libraries(self.library_paths)
        self.library_panel.highlight_library(self.current_library_path)

    def save_library_paths(self):
        self._save_library_paths()

    def reload_current_library(self):
        self.commands.reload_current_library()