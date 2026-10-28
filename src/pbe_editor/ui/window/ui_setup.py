from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QComboBox, QToolBar, QStatusBar,
                               QDockWidget, QApplication, QMenuBar, QDialog)
from PySide6.QtGui import QAction, QActionGroup, QGuiApplication
from PySide6.QtCore import Qt

from constants import Styles, GRID_SERIES, GRID_SERIES_LABEL
from common.ui.panels.aux_bar import AuxBar
from common.ui.dialogs.libraries_dialog import LibrariesManagerDialog
from pbe_editor.core.board_manager import BoardManager
from pbe_editor.ui.board_canvas import BoardCanvas
from pbe_editor.ui.panels.board_right_panel import BoardRightPanel
from pbe_editor.ui.panels.drawing_tool_bar import BoardDrawingToolBar, BoardTool
from pbe_editor.ui.dialogs.nets_dialog import NetsDialog


class UiSetupService:
    def init_canvas(self):
        self.canvas = BoardCanvas(self)
        self.canvas.zoom_changed.connect(self.update_zoom_label)
        self.canvas.mouse_moved.connect(self.commands.on_mouse_moved)
        self.canvas.ratsnest_update_requested.connect(self.on_ratsnest_update)
        self.canvas.canvas_clicked.connect(self.commands.on_canvas_clicked)
        self.canvas.canvas_right_clicked.connect(self.commands.on_canvas_right_clicked)
        self.canvas.selection_changed.connect(self.commands.on_selection_changed)
        self.canvas.content_changed.connect(self.commit_snapshot)
        self.manager = BoardManager(self.board, self.canvas.scene, self.canvas)

        self.aux_bar = AuxBar(object_name="BoardAuxBar")
        self.aux_bar.undo_requested.connect(self.undo)
        self.aux_bar.redo_requested.connect(self.redo)
        self.aux_bar.select_requested.connect(lambda: self.set_tool(BoardTool.SELECT))
        self.aux_bar.delete_requested.connect(self.commands.delete_selected)

        self.tool_bar = BoardDrawingToolBar()
        self.tool_bar.tool_selected.connect(self.set_tool)

        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self.aux_bar, 0)
        v.addWidget(self.canvas, 1)
        v.addWidget(self.tool_bar, 0)
        self.setCentralWidget(central)

    def init_toolbars(self):
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
            lambda i: self.apply_grid_series(self.grid_series_combo.itemData(i))
        )
        toolbar.addWidget(self.grid_series_combo)

        toolbar.addWidget(QLabel(" Шаг: "))
        self.grid_combo = QComboBox()
        self.grid_combo.currentTextChanged.connect(self.on_grid_changed)
        toolbar.addWidget(self.grid_combo)

        toolbar.addSeparator()
        self.zoom_label = QLabel(" 100% ")
        toolbar.addWidget(self.zoom_label)

    def init_menu(self):
        menubar = QMenuBar(self)
        menubar.setNativeMenuBar(False)
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("Файл")
        act_import_net = QAction("Импорт схемы (.net)...", self)
        act_import_net.triggered.connect(self.on_import_net)
        file_menu.addAction(act_import_net)

        act_open = QAction("Открыть плату (.brd)...", self)
        act_open.triggered.connect(self.on_open_board)
        file_menu.addAction(act_open)

        act_save = QAction("Сохранить", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.save_board)
        file_menu.addAction(act_save)

        act_save_as = QAction("Сохранить как...", self)
        act_save_as.setShortcut("Ctrl+Shift+S")
        act_save_as.triggered.connect(self.on_save_board_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()

        act_add_lib = QAction("Добавить библиотеку...", self)
        act_add_lib.triggered.connect(self.add_library)
        file_menu.addAction(act_add_lib)

        act_manage_lib = QAction("Подключенные библиотеки...", self)
        act_manage_lib.triggered.connect(self.manage_libraries)
        file_menu.addAction(act_manage_lib)

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

        view_menu = menubar.addMenu("Вид")
        self.act_show_ratsnest = QAction("Показать связи", self, checkable=True)
        self.act_show_ratsnest.setChecked(True)
        self.act_show_ratsnest.setShortcut("L")
        self.act_show_ratsnest.triggered.connect(self.on_toggle_ratsnest)
        view_menu.addAction(self.act_show_ratsnest)

        self.act_show_values = QAction("Показать значения", self, checkable=True)
        self.act_show_values.setChecked(self.canvas.show_values)
        self.act_show_values.setShortcut("O")
        self.act_show_values.triggered.connect(self.toggle_values)
        view_menu.addAction(self.act_show_values)

        act_nets = QAction("Список связей...", self)
        act_nets.triggered.connect(self.on_show_nets)
        view_menu.addAction(act_nets)
        view_menu.addSeparator()

        self.act_show_grid = QAction("Показывать сетку", self, checkable=True)
        self.act_show_grid.setChecked(True)
        self.act_show_grid.setShortcut("G")
        self.act_show_grid.triggered.connect(self.toggle_grid)
        view_menu.addAction(self.act_show_grid)

        grid_menu = view_menu.addMenu("Шаг сетки")
        self._grid_group = QActionGroup(self)
        self._grid_group.setExclusive(True)
        self._grid_actions = {}
        for mode, label in GRID_SERIES_LABEL.items():
            act = QAction(label, self, checkable=True)
            act.setChecked(mode == self.grid_mode)
            act.triggered.connect(lambda _=False, m=mode: self.apply_grid_series(m))
            self._grid_group.addAction(act)
            grid_menu.addAction(act)
            self._grid_actions[mode] = act

        view_menu.addSeparator()
        act_full = QAction("Полный экран", self)
        act_full.setShortcut("F11")
        act_full.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(act_full)

    def init_docks(self):
        self.module_dock = QDockWidget("", self)
        self.module_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        panel = QWidget()
        panel.setMinimumWidth(160)
        panel.setMaximumWidth(320)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Модули на плате")
        title.setStyleSheet(Styles.SECTION_LABEL)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.module_list = QListWidget()
        self.module_list.setStyleSheet(Styles.LIST_BG)
        self.module_list.itemClicked.connect(self.commands.on_module_list_clicked)
        layout.addWidget(self.module_list, 1)

        self.module_dock.setWidget(panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.module_dock)
        self._hide_dock_title(self.module_dock)

        self.properties_dock = QDockWidget("", self)
        self.properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.right_panel = BoardRightPanel()
        self.properties_dock.setWidget(self.right_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        self._hide_dock_title(self.properties_dock)

    def _hide_dock_title(self, dock):
        empty = QWidget()
        empty.setFixedHeight(0)
        dock.setTitleBarWidget(empty)

    def init_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.log_label = QLabel("Готово.")
        sb.addWidget(self.log_label)
        self.coords_label = QLabel("X: 0.0000, Y: 0.0000")
        sb.addPermanentWidget(self.coords_label)

    def apply_theme(self):
        app = QApplication.instance()
        app.setStyleSheet(Styles.TOOLTIP)
        self.setStyleSheet(Styles.MAIN_WINDOW)
        self.canvas.apply_theme()
        self.log_label.setStyleSheet(Styles.LOG_LABEL)
        self.right_panel.setStyleSheet(Styles.RIGHT_PANEL)
        self.right_panel.apply_theme()
        self.tool_bar.apply_theme()
        self.aux_bar.apply_theme()
        self.module_dock.setStyleSheet(Styles.MAIN_WINDOW)

    def wire_panels(self):
        self.right_panel.properties_panel.btn_apply.clicked.connect(self.commands.on_apply_properties)
        self.right_panel.properties_panel.line_layer_selected.connect(self.commands.on_line_layer_selected)
        self.right_panel.properties_panel.module_selected.connect(self.commands.on_module_picked_from_panel)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        else:
            self.showFullScreen()

    def on_show_nets(self):
        dlg = NetsDialog(self.board, self)
        dlg.exec()

    def on_toggle_ratsnest(self):
        self.manager.show_ratsnest = self.act_show_ratsnest.isChecked()
        self.manager.rebuild_ratsnest()

    def on_ratsnest_update(self):
        self.manager.rebuild_ratsnest()

    def _apply_startup_geometry(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 800)
            return
        avail = screen.availableGeometry()
        self.setGeometry(avail)
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)

    def toggle_values(self):
        self.canvas.set_show_values(self.act_show_values.isChecked())
        state = "включены" if self.canvas.show_values else "скрыты"
        self.show_log(f"Значения элементов {state}")