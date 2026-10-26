import copy

from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QListWidgetItem, QFileDialog,
                               QMessageBox, QComboBox, QToolBar, QStatusBar,
                               QDockWidget, QApplication, QMenuBar,
                               QGraphicsItem, QDialog)
from PySide6.QtGui import QAction, QActionGroup, QGuiApplication
from PySide6.QtCore import Qt, QSettings, QEvent, QPointF

from constants import (
    Styles, apply_theme, GRID_SERIES, GRID_SERIES_LABEL,
    VK_W, VK_A, VK_S, VK_D, PAN_KEYS,
    VK_ESCAPE, VK_DELETE, VK_F1, VK_F2, VK_F3, VK_F11, VK_G,
    VK_R, VK_L,
)
from constants.board_settings import (
    SETTINGS_KEY_BRD_LIBS, SETTINGS_KEY_BRD_LAST,
    DEFAULT_LINE_LAYER, DEFAULT_LINE_WIDTH,
)
from pbe_editor.kicad.importer import parse_kicad_mod
from pbe_editor.core.board_models import (
    Board, BoardModule, BoardLine, BoardCircle, BoardArc, BoardText, PadNet,
    prefix_from_footprint_name,
)
from pbe_editor.core.board_manager import BoardManager
from pbe_editor.core.netlist_parser import parse_netlist
from pbe_editor.kicad.brd_exporter import build_brd_text
from pbe_editor.kicad.brd_importer import parse_brd
from pbe_editor.ui.board_canvas import BoardCanvas
from pbe_editor.ui.dialogs.nets_dialog import NetsDialog
from pbe_editor.ui.dialogs.text_dialog import TextDialog
from pbe_editor.ui.dialogs.arc_dialog import ArcDialog
from pbe_editor.ui.dialogs.libraries_dialog import LibrariesManagerDialog
from pbe_editor.ui.dialogs.custom_question_dialog import CustomQuestionDialog
from pbe_editor.ui.panels.board_right_panel import BoardRightPanel
from pbe_editor.ui.panels.drawing_tool_bar import BoardDrawingToolBar, BoardTool
from pbe_editor.ui.panels.aux_bar import BoardAuxBar
from pbe_editor.graphics.module_item import BoardModuleGraphicsItem
from pbe_editor.graphics.board_line_item import (
    BoardLineGraphicsItem, BoardCircleGraphicsItem, BoardArcGraphicsItem,
    BoardTextGraphicsItem,
)
from pbe_editor.graphics.ratsnest_item import RatsnestGraphicsItem


SETTINGS_KEY_BRD_GRID_MODE = "brd_grid_mode"


class BoardEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._settings = QSettings("TraceCAD", "TraceCAD")
        apply_theme()

        self.board = Board()
        self.library_paths = []
        self.library_modules = {}
        self.current_library_path = None

        self._line_layer = DEFAULT_LINE_LAYER
        self._selected_footprint = None

        self.grid_mode = self._load_grid_mode()

        self.current_tool = BoardTool.SELECT
        self._line_start = None
        self._circle_center_point = None
        self._arc_center_point = None
        self._arc_start_point = None
        self._text_position = None
        self._net_start = None

        self._clipboard = []
        self._current_mouse_pos = QPointF(0, 0)

        self._modified = False
        self._undo_stack = []
        self._redo_stack = []
        self._current_snapshot = None

        self.setWindowTitle("TraceCAD: Редактор печатной платы")
        self.resize(1200, 800)

        self._apply_startup_geometry()
        self._init_canvas()
        self._init_toolbars()
        self._init_menu()
        self._init_docks()
        self._init_statusbar()
        self._init_shortcuts()
        self._apply_theme()
        self._wire_panels()

        self._load_library_paths()
        self._refresh_library_modules()
        self._refresh_module_list()
        self._apply_grid_series(self.grid_mode, initial=True)

        self._set_tool(BoardTool.SELECT)

        self._restore_last_board()

    def _apply_startup_geometry(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 800)
            return
        avail = screen.availableGeometry()
        self.setGeometry(avail)
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)

    def _init_canvas(self):
        self.canvas = BoardCanvas(self)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.canvas.mouse_moved.connect(self._on_mouse_moved)
        self.canvas.ratsnest_update_requested.connect(self._on_ratsnest_update)
        self.canvas.canvas_clicked.connect(self._on_canvas_clicked)
        self.canvas.canvas_right_clicked.connect(self._on_canvas_right_clicked)
        self.canvas.selection_changed.connect(self._on_selection_changed)
        self.canvas.content_changed.connect(self._commit_snapshot)
        self.manager = BoardManager(self.board, self.canvas.scene, self.canvas)

        self.aux_bar = BoardAuxBar()
        self.aux_bar.undo_requested.connect(self.undo)
        self.aux_bar.redo_requested.connect(self.redo)
        self.aux_bar.select_requested.connect(lambda: self._set_tool(BoardTool.SELECT))
        self.aux_bar.delete_requested.connect(self._delete_selected)

        self.tool_bar = BoardDrawingToolBar()
        self.tool_bar.tool_selected.connect(self._set_tool)

        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self.aux_bar, 0)
        v.addWidget(self.canvas, 1)
        v.addWidget(self.tool_bar, 0)
        self.setCentralWidget(central)

    def _init_toolbars(self):
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
        act_import_net = QAction("Импорт схемы (.net)...", self)
        act_import_net.triggered.connect(self._on_import_net)
        file_menu.addAction(act_import_net)

        act_open = QAction("Открыть плату (.brd)...", self)
        act_open.triggered.connect(self._on_open_board)
        file_menu.addAction(act_open)

        act_save = QAction("Сохранить", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self._on_save_board)
        file_menu.addAction(act_save)

        act_save_as = QAction("Сохранить как...", self)
        act_save_as.setShortcut("Ctrl+Shift+S")
        act_save_as.triggered.connect(self._on_save_board_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()

        act_add_lib = QAction("Добавить библиотеку...", self)
        act_add_lib.triggered.connect(self._add_library)
        file_menu.addAction(act_add_lib)

        act_manage_lib = QAction("Подключенные библиотеки...", self)
        act_manage_lib.triggered.connect(self._manage_libraries)
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
        act_copy.triggered.connect(self._copy_selected)
        edit_menu.addAction(act_copy)

        act_paste = QAction("Вставить", self)
        act_paste.setShortcut("Ctrl+V")
        act_paste.triggered.connect(self._paste)
        edit_menu.addAction(act_paste)

        act_delete = QAction("Удалить", self)
        act_delete.setShortcut("Del")
        act_delete.triggered.connect(self._delete_selected)
        edit_menu.addAction(act_delete)

        view_menu = menubar.addMenu("Вид")
        self.act_show_ratsnest = QAction("Связи на плате", self, checkable=True)
        self.act_show_ratsnest.setChecked(True)
        self.act_show_ratsnest.setShortcut("L")
        self.act_show_ratsnest.triggered.connect(self._on_toggle_ratsnest)
        view_menu.addAction(self.act_show_ratsnest)

        act_nets = QAction("Список связей...", self)
        act_nets.triggered.connect(self._on_show_nets)
        view_menu.addAction(act_nets)
        view_menu.addSeparator()

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

        view_menu.addSeparator()
        act_full = QAction("Полный экран", self)
        act_full.setShortcut("F11")
        act_full.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(act_full)

    def _init_docks(self):
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
        self.module_list.itemClicked.connect(self._on_module_list_clicked)
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

    def _init_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.log_label = QLabel("Готово.")
        sb.addWidget(self.log_label)
        self.coords_label = QLabel("X: 0.0000, Y: 0.0000")
        sb.addPermanentWidget(self.coords_label)

    def _init_shortcuts(self):
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if self._handle_key_press(event):
                return True
        elif event.type() == QEvent.Type.KeyRelease:
            if self._handle_key_release(event):
                return True
        return super().eventFilter(obj, event)

    def _handle_key_press(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._exit_to_select_mode()
            return True
        vk = event.nativeVirtualKey()
        if vk == VK_DELETE:
            self._delete_selected()
            return True
        if vk == VK_R:
            self._rotate_selected()
            return True
        if vk == VK_L:
            self.act_show_ratsnest.setChecked(not self.act_show_ratsnest.isChecked())
            self._on_toggle_ratsnest()
            return True
        if vk == VK_G:
            self.act_show_grid.setChecked(not self.act_show_grid.isChecked())
            self._toggle_grid()
            return True
        if vk == VK_F11:
            self.toggle_fullscreen()
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
        if vk in PAN_KEYS:
            self.canvas.pressed_keys.add(vk)
            if not self.canvas.pan_timer.isActive():
                self.canvas.pan_timer.start()
            return True
        return False

    def _handle_key_release(self, event):
        vk = event.nativeVirtualKey()
        if vk in PAN_KEYS:
            self.canvas.pressed_keys.discard(vk)
            if not self.canvas.pressed_keys:
                self.canvas.pan_timer.stop()
            return True
        return False

    def _wire_panels(self):
        self.right_panel.properties_panel.btn_apply.clicked.connect(self._on_apply_properties)
        self.right_panel.properties_panel.line_layer_selected.connect(self._on_line_layer_selected)
        self.right_panel.properties_panel.module_selected.connect(self._on_module_picked_from_panel)

    def _on_apply_properties(self):
        self.manager.rebuild_ratsnest()
        self._refresh_module_list()
        self._commit_snapshot()

    def _on_line_layer_selected(self, layer):
        self._line_layer = layer
        self.show_log(f"Слой рисования: {layer}")

    def _on_module_picked_from_panel(self, fp):
        self._selected_footprint = fp
        self.show_log(f"Выбран модуль для вставки: {fp.name}")

    def _on_selection_changed(self):
        if self.current_tool != BoardTool.SELECT:
            return
        items = self.canvas.scene.selectedItems()
        self.aux_bar.set_delete_enabled(len(items) > 0)
        if len(items) == 1:
            item = items[0]
            if isinstance(item, (BoardModuleGraphicsItem, BoardLineGraphicsItem,
                                 BoardCircleGraphicsItem, BoardArcGraphicsItem,
                                 BoardTextGraphicsItem, RatsnestGraphicsItem)):
                self.right_panel.properties_panel.show_object(item)
                return
        self.right_panel.properties_panel.clear_panel()

    def _on_module_list_clicked(self, list_item):
        idx = self.module_list.row(list_item)
        if 0 <= idx < len(self.board.modules):
            module = self.board.modules[idx]
            item = self.manager.items.get(module.uid)
            if item is not None:
                self.canvas.scene.clearSelection()
                item.setSelected(True)
                self.right_panel.properties_panel.show_object(item)
                self.canvas.centerOn(item)

    def _apply_theme(self):
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

    def _load_grid_mode(self):
        mode = self._settings.value(SETTINGS_KEY_BRD_GRID_MODE, "1x", type=str)
        return mode if mode in GRID_SERIES else "1x"

    def _persist_grid_mode(self, mode):
        self._settings.setValue(SETTINGS_KEY_BRD_GRID_MODE, mode)
        self._settings.sync()

    def _apply_grid_series(self, mode, initial=False):
        if mode not in GRID_SERIES:
            return
        self.grid_mode = mode
        self._persist_grid_mode(mode)
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

    def _toggle_grid(self):
        self.canvas.show_grid = self.act_show_grid.isChecked()
        self.canvas.viewport().update()

    def _on_grid_changed(self, text):
        if not text:
            return
        self.canvas.set_grid_size(float(text))
        self.canvas.setFocus()

    def _change_grid_step(self, direction):
        i = self.grid_combo.currentIndex() + direction
        if 0 <= i < self.grid_combo.count():
            self.grid_combo.setCurrentIndex(i)

    def _load_library_paths(self):
        saved = self._settings.value(SETTINGS_KEY_BRD_LIBS, "", type=str)
        if saved:
            self.library_paths = [p for p in saved.split("\n") if p.strip()]

    def _save_library_paths(self):
        self._settings.setValue(SETTINGS_KEY_BRD_LIBS, "\n".join(self.library_paths))
        self._settings.sync()

    def _refresh_library_modules(self):
        self.library_modules = {}
        for path in self.library_paths:
            try:
                footprints = parse_kicad_mod(path)
                self.library_modules[path] = {fp.name: fp for fp in footprints}
            except Exception as e:
                self.show_log(f"Ошибка библиотеки {Path(path).name}: {e}")

    def _find_footprint(self, name):
        for lib_data in self.library_modules.values():
            if name in lib_data:
                return lib_data[name]
        return None

    def _refresh_module_list(self):
        self.module_list.clear()
        for module in self.board.modules:
            item = QListWidgetItem(f"{module.reference}  [{module.footprint.name}]")
            item.setToolTip(f"{module.reference} = {module.value}")
            self.module_list.addItem(item)

    def _add_library(self):
        path, _ = QFileDialog.getOpenFileName(self, "Добавить библиотеку .mod", "",
                                              "KiCad Library (*.mod);;All Files (*)")
        if not path or path in self.library_paths:
            return
        self.library_paths.append(path)
        self._save_library_paths()
        self._refresh_library_modules()
        if self.current_tool == BoardTool.ADD_MODULE:
            self.right_panel.properties_panel.show_module_picker(self.library_modules)
        self.show_log(f"Библиотека добавлена: {Path(path).name}")

    def _manage_libraries(self):
        dlg = LibrariesManagerDialog(self.library_paths, self)
        if dlg.exec() != LibrariesManagerDialog.Accepted:
            return
        new_paths = dlg.get_library_paths()
        if new_paths == self.library_paths:
            return
        self.library_paths = new_paths
        self._save_library_paths()
        self._refresh_library_modules()
        if self.current_tool == BoardTool.ADD_MODULE:
            self.right_panel.properties_panel.show_module_picker(self.library_modules)
        self.show_log(f"Библиотек: {len(self.library_paths)}")

    def _next_module_uid(self):
        if not self.board.modules:
            return 1
        return max(m.uid for m in self.board.modules) + 1

    def _next_line_uid(self):
        if not self.board.lines:
            return 1
        return max(l.uid for l in self.board.lines) + 1

    def _next_circle_uid(self):
        if not self.board.circles:
            return 1
        return max(c.uid for c in self.board.circles) + 1

    def _next_arc_uid(self):
        if not self.board.arcs:
            return 1
        return max(a.uid for a in self.board.arcs) + 1

    def _next_text_uid(self):
        if not self.board.texts:
            return 1
        return max(t.uid for t in self.board.texts) + 1

    def _on_import_net(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть сетлист", "",
                                              "Netlist (*.net);;All Files (*)")
        if not path:
            return
        self._refresh_library_modules()
        try:
            components = parse_netlist(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разобрать сетлист: {e}")
            return

        self.manager.clear()
        self.board = Board(name=Path(path).stem)
        self.manager.board = self.board

        missing = []
        next_uid = 1
        for comp in components:
            fp = self._find_footprint(comp.footprint)
            if fp is None:
                missing.append(f"{comp.reference} ({comp.footprint})")
                continue
            module = BoardModule(
                footprint=fp, reference=comp.reference, value=comp.value,
                x=0.0, y=0.0, angle=0.0, layer="F.Cu", uid=next_uid,
            )
            next_uid += 1
            pad_numbers = {p.number for p in fp.pads}
            for pad_number, net_name in comp.pins.items():
                if pad_number not in pad_numbers or not net_name:
                    continue
                net = self.board.get_or_create_net(net_name)
                module.pad_nets[pad_number] = PadNet(
                    pad_number=pad_number,
                    net_code=net.code,
                    net_name=net.name,
                )
            self.board.modules.append(module)
            self.manager.add_module(module)
        self._refresh_module_list()
        self.manager.rebuild_ratsnest()
        self.setWindowTitle(f"TraceCAD: {self.board.name}")
        self.show_log(f"Импортировано модулей: {len(self.board.modules)}")
        self._reset_history()
        self._modified = True
        if missing:
            QMessageBox.information(self, "Импорт завершён",
                "Импорт выполнен, но не найдены посадочные места:\n" + "\n".join(missing))

    def _on_open_board(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть плату", "",
                                              "KiCad Board (*.brd);;All Files (*)")
        if not path:
            return
        self._load_board_from_path(path)

    
    def _load_board_from_path(self, path):
        try:
            board = parse_brd(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть плату: {e}")
            return
        self.manager.clear()
        self.board = board
        self.manager.board = self.board
        self.board.name = Path(path).stem

        for module in self.board.modules:
            self.manager.add_module(module)
        for line in self.board.lines:
            self.manager.add_line(line)
        for circle in self.board.circles:
            self.manager.add_circle(circle)
        for arc in self.board.arcs:
            self.manager.add_arc(arc)
        for text in self.board.texts:
            self.manager.add_text(text)

        self._refresh_module_list()
        self.manager.rebuild_ratsnest()
        self.board.filename = path
        self.setWindowTitle(f"TraceCAD: {Path(path).name}")
        self.show_log(f"Плата загружена: {Path(path).name} ({len(self.board.modules)} модулей)")
        self._reset_history()
        self._modified = False

    def _on_save_board(self):
        if not self.board.filename:
            self._on_save_board_as()
            return
        try:
            text = build_brd_text(self.board)
            Path(self.board.filename).write_text(text, encoding='utf-8')
            self._modified = False
            self.show_log(f"Плата сохранена: {Path(self.board.filename).name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def _on_save_board_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить плату как", "",
                                              "KiCad Board (*.brd);;All Files (*)")
        if not path:
            return
        if not path.lower().endswith('.brd'):
            path += '.brd'
        try:
            text = build_brd_text(self.board)
            Path(path).write_text(text, encoding='utf-8')
            self.board.filename = path
            self.board.name = Path(path).stem
            self._modified = False
            self.setWindowTitle(f"TraceCAD: {Path(path).name}")
            self.show_log(f"Плата сохранена: {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def _on_show_nets(self):
        dlg = NetsDialog(self.board, self)
        dlg.exec()

    def _on_toggle_ratsnest(self):
        self.manager.show_ratsnest = self.act_show_ratsnest.isChecked()
        self.manager.rebuild_ratsnest()

    def _on_ratsnest_update(self):
        self.manager.rebuild_ratsnest()

    def _on_mouse_moved(self, x, y):
        self._current_mouse_pos = QPointF(x, y)
        self.coords_label.setText(f"X: {x:.4f}, Y: {y:.4f}")
        tool = self.current_tool

        if tool == BoardTool.ADD_NET:
            tol = self.canvas.grid_size * 1.5
            hit = self.board.find_pad_at(x, y, tol)
            if hit is not None:
                module, pad_number = hit
                pos = module.get_pad_absolute(pad_number)
                pad = None
                for p in module.footprint.pads:
                    if p.number == pad_number:
                        pad = p
                        break
                if pos and pad:
                    radius = max(pad.width, pad.height) * 0.8
                    self.canvas.set_highlight_pad(QPointF(*pos), radius)
                else:
                    self.canvas.clear_highlight_pad()
            else:
                self.canvas.clear_highlight_pad()

            if self._net_start:
                sx, sy = self._net_start[2]
                self.canvas.set_ghost_line(sx, sy, x, y)
            return

        self.canvas.clear_highlight_pad()

        if tool == BoardTool.ADD_LINE and self._line_start:
            sx, sy = self._line_start
            self.canvas.set_ghost_line(sx, sy, x, y)
        elif tool == BoardTool.ADD_CIRCLE and self._circle_center_point:
            cx, cy = self._circle_center_point
            g = self.canvas.grid_size
            r = round(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / g) * g
            self.canvas.set_ghost_circle(cx, cy, r)
        elif tool == BoardTool.ADD_ARC and self._arc_center_point and self._arc_start_point is None:
            cx, cy = self._arc_center_point
            self.canvas.set_ghost_line(cx, cy, x, y)
        elif tool == BoardTool.ADD_TEXT and self._text_position:
            tx, ty = self._text_position
            self.canvas.set_ghost_text(tx, ty, "", 1.0, True)
        else:
            self.canvas.clear_ghost_line()
            self.canvas.clear_ghost_circle()

    def _update_zoom_label(self, zoom):
        self.zoom_label.setText(f" {int(zoom * 100)}% ")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        else:
            self.showFullScreen()

    def show_log(self, text):
        self.log_label.setText(text)

    def _set_selectable_all(self, enabled):
        for item in self.canvas.scene.items():
            if isinstance(item, (BoardModuleGraphicsItem, BoardLineGraphicsItem,
                                 BoardCircleGraphicsItem, BoardArcGraphicsItem,
                                 BoardTextGraphicsItem, RatsnestGraphicsItem)):
                try:
                    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled)
                    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled)
                except RuntimeError:
                    pass

    def _set_tool(self, tool):
        self.current_tool = tool
        self._line_start = None
        self._circle_center_point = None
        self._arc_center_point = None
        self._arc_start_point = None
        self._text_position = None
        self._net_start = None
        self.canvas.clear_ghost_line()
        self.canvas.clear_ghost_circle()
        self.canvas.clear_ghost_arc()
        self.canvas.clear_ghost_text()
        self.canvas.clear_highlight_pad()

        if tool in (BoardTool.SELECT, BoardTool.ADD_NET):
            self.canvas.set_show_snap(False)
        else:
            self.canvas.set_show_snap(True)

        if tool == BoardTool.SELECT:
            self._set_selectable_all(True)
            self.aux_bar.set_select_active(True)
            self.tool_bar.clear_active()
            self.canvas.setDragMode(self.canvas.DragMode.RubberBandDrag)
            self.right_panel.properties_panel.clear_panel()
        else:
            self._set_selectable_all(False)
            self.canvas.scene.clearSelection()
            self.aux_bar.set_select_active(False)
            self.tool_bar.set_active(tool)
            self.canvas.setDragMode(self.canvas.DragMode.NoDrag)
            if tool in (BoardTool.ADD_LINE, BoardTool.ADD_CIRCLE,
                        BoardTool.ADD_ARC, BoardTool.ADD_TEXT):
                self.right_panel.properties_panel.show_line_layer_picker(self._line_layer)
            elif tool == BoardTool.ADD_MODULE:
                self.right_panel.properties_panel.show_module_picker(self.library_modules)
            elif tool == BoardTool.ADD_NET:
                self.right_panel.properties_panel.clear_panel()
        self.show_log(f"Инструмент: {tool}")

    def _exit_to_select_mode(self):
        self._set_tool(BoardTool.SELECT)
        self.canvas.scene.clearSelection()

    def _on_canvas_clicked(self, x, y):
        tool = self.current_tool
        if tool == BoardTool.ADD_LINE:
            self._on_add_line_click(x, y)
        elif tool == BoardTool.ADD_CIRCLE:
            self._on_add_circle_click(x, y)
        elif tool == BoardTool.ADD_ARC:
            self._on_add_arc_click(x, y)
        elif tool == BoardTool.ADD_TEXT:
            self._on_add_text_click(x, y)
        elif tool == BoardTool.ADD_MODULE:
            self._on_add_module_click(x, y)
        elif tool == BoardTool.ADD_NET:
            self._on_add_net_click(x, y)

    def _on_canvas_right_clicked(self):
        self._exit_to_select_mode()

    def _add_graphic_item(self, model, kind):
        if kind == "line":
            self.board.lines.append(model)
            item = self.manager.add_line(model)
        elif kind == "circle":
            self.board.circles.append(model)
            item = self.manager.add_circle(model)
        elif kind == "arc":
            self.board.arcs.append(model)
            item = self.manager.add_arc(model)
        elif kind == "text":
            self.board.texts.append(model)
            item = self.manager.add_text(model)
        else:
            return None
        if self.current_tool != BoardTool.SELECT:
            try:
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            except RuntimeError:
                pass
        return item

    def _on_add_line_click(self, x, y):
        if self._line_start is None:
            self._line_start = (x, y)
            self.canvas.set_ghost_line(x, y, x, y)
            return
        sx, sy = self._line_start
        if abs(sx - x) < 1e-6 and abs(sy - y) < 1e-6:
            return
        line = BoardLine(
            x1=sx, y1=sy, x2=x, y2=y,
            layer=self._line_layer, width=DEFAULT_LINE_WIDTH,
            uid=self._next_line_uid(),
        )
        self._add_graphic_item(line, "line")
        self._line_start = (x, y)
        self.canvas.set_ghost_line(x, y, x, y)
        self._commit_snapshot()
        self.show_log(f"Линия {self._line_layer}: добавлена")

    def _on_add_circle_click(self, x, y):
        g = self.canvas.grid_size
        if self._circle_center_point is None:
            self._circle_center_point = (x, y)
            self.canvas.set_ghost_circle(x, y, 0.0)
            return
        cx, cy = self._circle_center_point
        r = round(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / g) * g
        if r > 0:
            circle = BoardCircle(
                x=cx, y=cy, radius=r,
                layer=self._line_layer, width=DEFAULT_LINE_WIDTH,
                uid=self._next_circle_uid(),
            )
            self._add_graphic_item(circle, "circle")
            self._commit_snapshot()
            self.show_log(f"Окружность {self._line_layer}: добавлена")
        self._circle_center_point = None
        self.canvas.clear_ghost_circle()

    def _on_add_arc_click(self, x, y):
        if self._arc_center_point is None:
            self._arc_center_point = (x, y)
            self.canvas.set_ghost_line(x, y, x, y)
            return
        if self._arc_start_point is None:
            self._arc_start_point = (x, y)
            cx, cy = self._arc_center_point
            self.canvas.set_ghost_line(cx, cy, x, y)
            self._show_arc_dialog()
            return
        self._arc_center_point = (x, y)
        self._arc_start_point = None
        self.canvas.set_ghost_line(x, y, x, y)

    def _show_arc_dialog(self):
        cx, cy = self._arc_center_point
        sx, sy = self._arc_start_point

        dlg = ArcDialog(self)
        dlg.angle_changed.connect(
            lambda a: self.canvas.set_ghost_arc(cx, cy, sx, sy, a)
        )
        self.canvas.set_ghost_arc(cx, cy, sx, sy, dlg.get_angle())

        if dlg.exec() == QDialog.Accepted:
            arc = BoardArc(
                x=cx, y=cy, sx=sx, sy=sy,
                angle=dlg.get_angle(),
                layer=self._line_layer, width=DEFAULT_LINE_WIDTH,
                uid=self._next_arc_uid(),
            )
            self._add_graphic_item(arc, "arc")
            self._commit_snapshot()
            self.show_log(f"Дуга {self._line_layer}: добавлена")

        self._arc_center_point = None
        self._arc_start_point = None
        self.canvas.clear_ghost_arc()

    def _on_add_text_click(self, x, y):
        self._text_position = (x, y)
        self.canvas.set_ghost_text(x, y, "", 1.0, True)

        dialog = TextDialog(self)
        dialog.text_changed.connect(
            lambda t: self.canvas.set_ghost_text(
                self._text_position[0], self._text_position[1],
                t, dialog.get_size(), dialog.get_visible()))
        dialog.size_changed.connect(
            lambda s: self.canvas.set_ghost_text(
                self._text_position[0], self._text_position[1],
                dialog.get_text(), s, dialog.get_visible()))
        dialog.visible_changed.connect(
            lambda v: self.canvas.set_ghost_text(
                self._text_position[0], self._text_position[1],
                dialog.get_text(), dialog.get_size(), v))

        if dialog.exec() == QDialog.Accepted:
            text_value = dialog.get_text() or "Text"
            tx, ty = self._text_position
            text = BoardText(
                x=tx, y=ty, text=text_value,
                size=dialog.get_size(), visible=dialog.get_visible(),
                layer=self._line_layer, uid=self._next_text_uid(),
            )
            self._add_graphic_item(text, "text")
            self._commit_snapshot()
            self.show_log(f"Текст {self._line_layer}: добавлен")

        self._text_position = None
        self.canvas.clear_ghost_text()

    def _on_add_module_click(self, x, y):
        fp = self._selected_footprint
        if fp is None:
            self.show_log("Сначала выберите модуль справа")
            return
        prefix = prefix_from_footprint_name(fp.name)
        module = BoardModule(
            footprint=copy.deepcopy(fp),
            reference=self.board.auto_reference(prefix),
            value=fp.value,
            x=x, y=y, angle=0.0, layer="F.Cu",
            uid=self._next_module_uid(),
        )
        self.board.modules.append(module)
        item = self.manager.add_module(module)
        if self.current_tool != BoardTool.SELECT:
            try:
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            except RuntimeError:
                pass
        self.manager.rebuild_ratsnest()
        self._refresh_module_list()
        self._commit_snapshot()
        self.show_log(f"Модуль {module.reference} добавлен")

    def _on_add_net_click(self, x, y):
        tol = self.canvas.grid_size * 1.5
        hit = self.board.find_pad_at(x, y, tol)
        if hit is None:
            self.show_log("Не найден вывод в точке")
            return
        module, pad_number = hit
        pos = module.get_pad_absolute(pad_number)
        if self._net_start is None:
            self._net_start = (module, pad_number, pos)
            self.canvas.set_ghost_line(pos[0], pos[1], pos[0], pos[1])
            return
        m1, p1, pos1 = self._net_start
        if (m1, p1) == (module, pad_number):
            self._net_start = None
            self.canvas.clear_ghost_line()
            return
        pn1 = m1.pad_nets.get(p1)
        pn2 = module.pad_nets.get(pad_number)
        net_name = None
        if pn1 and pn1.net_name:
            net_name = pn1.net_name
        elif pn2 and pn2.net_name:
            net_name = pn2.net_name
        if net_name is None:
            net_name = f"Net-{m1.reference}-{p1}-{module.reference}-{pad_number}"
        net = self.board.get_or_create_net(net_name)
        for m, p in ((m1, p1), (module, pad_number)):
            m.pad_nets[p] = PadNet(pad_number=p, net_code=net.code, net_name=net.name)
        self._net_start = None
        self.canvas.clear_ghost_line()
        self.manager.rebuild_ratsnest()
        self._commit_snapshot()
        self.show_log(f"Связь {net_name}: {m1.reference}.{p1} ↔ {module.reference}.{pad_number}")

    def _delete_selected(self):
        deleted_modules = []
        deleted_lines = []
        deleted_circles = []
        deleted_arcs = []
        deleted_texts = []
        deleted_ratsnest = []
        for item in list(self.canvas.scene.selectedItems()):
            if isinstance(item, BoardModuleGraphicsItem):
                deleted_modules.append(item.module)
            elif isinstance(item, BoardLineGraphicsItem):
                deleted_lines.append(item.model)
            elif isinstance(item, BoardCircleGraphicsItem):
                deleted_circles.append(item.model)
            elif isinstance(item, BoardArcGraphicsItem):
                deleted_arcs.append(item.model)
            elif isinstance(item, BoardTextGraphicsItem):
                deleted_texts.append(item.model)
            elif isinstance(item, RatsnestGraphicsItem):
                deleted_ratsnest.append(item)

        deleted_net_codes = set()
        for r in deleted_ratsnest:
            if r.net_code > 0:
                deleted_net_codes.add(r.net_code)

        for m in deleted_modules:
            self.manager.remove_module(m)
            if m in self.board.modules:
                self.board.modules.remove(m)
        for l in deleted_lines:
            self.manager.remove_line(l)
            if l in self.board.lines:
                self.board.lines.remove(l)
        for c in deleted_circles:
            self.manager.remove_circle(c)
            if c in self.board.circles:
                self.board.circles.remove(c)
        for a in deleted_arcs:
            self.manager.remove_arc(a)
            if a in self.board.arcs:
                self.board.arcs.remove(a)
        for t in deleted_texts:
            self.manager.remove_text(t)
            if t in self.board.texts:
                self.board.texts.remove(t)
        for r in deleted_ratsnest:
            if r in self.manager.ratsnest_items:
                self.manager.ratsnest_items.remove(r)
            try:
                self.canvas.scene.removeItem(r)
            except RuntimeError:
                pass
        if deleted_net_codes:
            for module in self.board.modules:
                for pad_number in list(module.pad_nets.keys()):
                    if module.pad_nets[pad_number].net_code in deleted_net_codes:
                        del module.pad_nets[pad_number]

        if deleted_modules or deleted_lines or deleted_circles or deleted_arcs or deleted_texts or deleted_ratsnest:
            self.manager.rebuild_ratsnest()
            self._refresh_module_list()
            self._commit_snapshot()
            self.show_log(
                f"Удалено: {len(deleted_modules)} модулей, "
                f"{len(deleted_lines)} линий, {len(deleted_circles)} окружностей, "
                f"{len(deleted_arcs)} дуг, {len(deleted_texts)} текстов, "
                f"{len(deleted_ratsnest)} связей"
            )

    def _rotate_selected(self):
        items = [it for it in self.canvas.scene.selectedItems()
                 if isinstance(it, (BoardModuleGraphicsItem, BoardLineGraphicsItem,
                                    BoardArcGraphicsItem))]
        if not items:
            return
        for item in items:
            if isinstance(item, BoardModuleGraphicsItem):
                item.module.angle = (item.module.angle + 90.0) % 360.0
                item.setRotation(item.module.angle)
                item.prepareGeometryChange()
                item.update()
            elif isinstance(item, BoardLineGraphicsItem):
                l = item.model
                cx = (l.x1 + l.x2) / 2.0
                cy = (l.y1 + l.y2) / 2.0
                dx1, dy1 = l.x1 - cx, l.y1 - cy
                dx2, dy2 = l.x2 - cx, l.y2 - cy
                l.x1, l.y1 = cx - dy1, cy + dx1
                l.x2, l.y2 = cx - dy2, cy + dx2
                item.setPos(l.x1, l.y1)
                item.prepareGeometryChange()
                item.update()
            elif isinstance(item, BoardArcGraphicsItem):
                a = item.model
                dx, dy = a.sx - a.x, a.sy - a.y
                a.sx = a.x - dy
                a.sy = a.y + dx
                item.setPos(a.x, a.y)
                item.prepareGeometryChange()
                item.update()
        self.manager.rebuild_ratsnest()
        self._commit_snapshot()
        self.show_log(f"Повёрнуто: {len(items)} элементов")

    def _model_center(self, m):
        if isinstance(m, BoardModule):
            return m.x, m.y
        if isinstance(m, BoardLine):
            return (m.x1 + m.x2) / 2.0, (m.y1 + m.y2) / 2.0
        if isinstance(m, (BoardCircle, BoardArc, BoardText)):
            return m.x, m.y
        return 0.0, 0.0

    def _translate_model(self, m, dx, dy):
        if isinstance(m, BoardModule):
            m.x += dx
            m.y += dy
        elif isinstance(m, BoardLine):
            m.x1 += dx
            m.y1 += dy
            m.x2 += dx
            m.y2 += dy
        elif isinstance(m, BoardArc):
            m.x += dx
            m.y += dy
            m.sx += dx
            m.sy += dy
        elif isinstance(m, (BoardCircle, BoardText)):
            m.x += dx
            m.y += dy

    def _copy_selected(self):
        self._clipboard = []
        for item in self.canvas.scene.selectedItems():
            if isinstance(item, BoardModuleGraphicsItem):
                self._clipboard.append(copy.deepcopy(item.module))
            elif isinstance(item, BoardLineGraphicsItem):
                self._clipboard.append(copy.deepcopy(item.model))
            elif isinstance(item, BoardCircleGraphicsItem):
                self._clipboard.append(copy.deepcopy(item.model))
            elif isinstance(item, BoardArcGraphicsItem):
                self._clipboard.append(copy.deepcopy(item.model))
            elif isinstance(item, BoardTextGraphicsItem):
                self._clipboard.append(copy.deepcopy(item.model))
        if self._clipboard:
            self.show_log(f"Скопировано: {len(self._clipboard)} элементов")

    def _clipboard_center(self):
        if not self._clipboard:
            return 0.0, 0.0
        sx = sy = 0.0
        n = 0
        for m in self._clipboard:
            px, py = self._model_center(m)
            sx += px
            sy += py
            n += 1
        return (sx / n, sy / n) if n else (0.0, 0.0)

    def _paste(self):
        if not self._clipboard:
            return
        self.canvas.scene.clearSelection()
        cx, cy = self._clipboard_center()
        dx = self._current_mouse_pos.x() - cx
        dy = self._current_mouse_pos.y() - cy
        grid = self.canvas.grid_size
        dx = round(dx / grid) * grid
        dy = round(dy / grid) * grid

        for model in self._clipboard:
            new_model = copy.deepcopy(model)
            if isinstance(new_model, BoardModule):
                new_model.uid = self._next_module_uid()
                new_model.reference = self.board.auto_reference(
                    prefix_from_footprint_name(new_model.footprint.name))
                self._translate_model(new_model, dx, dy)
                self.board.modules.append(new_model)
                item = self.manager.add_module(new_model)
            elif isinstance(new_model, BoardLine):
                new_model.uid = self._next_line_uid()
                self._translate_model(new_model, dx, dy)
                self.board.lines.append(new_model)
                item = self.manager.add_line(new_model)
            elif isinstance(new_model, BoardCircle):
                new_model.uid = self._next_circle_uid()
                self._translate_model(new_model, dx, dy)
                self.board.circles.append(new_model)
                item = self.manager.add_circle(new_model)
            elif isinstance(new_model, BoardArc):
                new_model.uid = self._next_arc_uid()
                self._translate_model(new_model, dx, dy)
                self.board.arcs.append(new_model)
                item = self.manager.add_arc(new_model)
            elif isinstance(new_model, BoardText):
                new_model.uid = self._next_text_uid()
                self._translate_model(new_model, dx, dy)
                self.board.texts.append(new_model)
                item = self.manager.add_text(new_model)
            else:
                continue
            item.setSelected(True)

        self._refresh_module_list()
        self.manager.rebuild_ratsnest()
        self._commit_snapshot()
        self.show_log(f"Вставлено: {len(self._clipboard)} элементов")

    def _snapshot(self):
        return {
            "modules": copy.deepcopy(self.board.modules),
            "lines": copy.deepcopy(self.board.lines),
            "circles": copy.deepcopy(self.board.circles),
            "arcs": copy.deepcopy(self.board.arcs),
            "texts": copy.deepcopy(self.board.texts),
            "nets": copy.deepcopy(self.board.nets),
        }

    def _restore_snapshot(self, snap):
        self.board.modules = copy.deepcopy(snap["modules"])
        self.board.lines = copy.deepcopy(snap["lines"])
        self.board.circles = copy.deepcopy(snap["circles"])
        self.board.arcs = copy.deepcopy(snap["arcs"])
        self.board.texts = copy.deepcopy(snap.get("texts", []))
        self.board.nets = copy.deepcopy(snap["nets"])
        self.manager.clear()
        self.manager.board = self.board
        for m in self.board.modules:
            self.manager.add_module(m)
        for l in self.board.lines:
            self.manager.add_line(l)
        for c in self.board.circles:
            self.manager.add_circle(c)
        for a in self.board.arcs:
            self.manager.add_arc(a)
        for t in self.board.texts:
            self.manager.add_text(t)
        if self.current_tool != BoardTool.SELECT:
            self._set_selectable_all(False)
        self.manager.rebuild_ratsnest()
        self._refresh_module_list()

    def _reset_history(self):
        self._undo_stack = []
        self._redo_stack = []
        self._current_snapshot = self._snapshot()
        self._update_history_buttons()

    def _commit_snapshot(self):
        self._modified = True
        if self._current_snapshot is None:
            self._current_snapshot = self._snapshot()
            return
        self._undo_stack.append(self._current_snapshot)
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._current_snapshot = self._snapshot()
        self._update_history_buttons()

    def undo(self):
        if not self._undo_stack:
            return
        self._redo_stack.append(self._current_snapshot)
        self._current_snapshot = self._undo_stack.pop()
        self._restore_snapshot(self._current_snapshot)
        self._update_history_buttons()
        self._modified = True
        self.show_log("отменено")

    def redo(self):
        if not self._redo_stack:
            return
        self._undo_stack.append(self._current_snapshot)
        self._current_snapshot = self._redo_stack.pop()
        self._restore_snapshot(self._current_snapshot)
        self._update_history_buttons()
        self._modified = True
        self.show_log("повторено")

    def _update_history_buttons(self):
        self.aux_bar.set_undo_enabled(bool(self._undo_stack))
        self.aux_bar.set_redo_enabled(bool(self._redo_stack))

    def _restore_last_board(self):
        last = self._settings.value(SETTINGS_KEY_BRD_LAST, "", type=str)
        if not last:
            self._reset_history()
            return
        p = Path(last)
        if not p.exists() or not p.is_file():
            self._reset_history()
            return
        self._load_board_from_path(str(p))

    def _save_last_board(self):
        if self.board.filename:
            self._settings.setValue(SETTINGS_KEY_BRD_LAST, self.board.filename)
        else:
            self._settings.setValue(SETTINGS_KEY_BRD_LAST, "")
        self._settings.sync()

    def closeEvent(self, event):
        if self._modified:
            dlg = CustomQuestionDialog(
                self,
                title="Несохранённые изменения",
                message=f"Сохранить изменения в плате '{self.board.name}' перед выходом?"
            )
            result = dlg.exec()
            if result == CustomQuestionDialog.ResultSave:
                self._on_save_board()
                if self._modified:
                    event.ignore()
                    return
            elif result == CustomQuestionDialog.ResultCancel:
                event.ignore()
                return
        self._save_last_board()
        super().closeEvent(event)