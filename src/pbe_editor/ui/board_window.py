from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel,
                               QListWidget, QListWidgetItem, QFileDialog,
                               QMessageBox, QComboBox, QToolBar, QStatusBar,
                               QDockWidget, QApplication, QMenuBar, QPushButton,
                               QHBoxLayout)
from PySide6.QtGui import QAction, QActionGroup, QGuiApplication
from PySide6.QtCore import Qt, QSettings, QEvent

from constants import (
    Styles, Steps, apply_theme, GRID_SERIES, GRID_SERIES_LABEL,
    VK_W, VK_A, VK_S, VK_D, PAN_KEYS,
    VK_ESCAPE, VK_DELETE, VK_F1, VK_F2, VK_F3, VK_F11, VK_G,
    VK_R, VK_L,
)
from constants.board_settings import SETTINGS_KEY_BRD_LIBS, SETTINGS_KEY_BRD_LAST
from footprint_editor.kicad.importer import parse_kicad_mod
from pbe_editor.core.board_models import Board, BoardModule, PadNet
from pbe_editor.core.board_manager import BoardManager
from pbe_editor.core.netlist_parser import parse_netlist
from pbe_editor.kicad.brd_exporter import build_brd_text
from pbe_editor.kicad.brd_importer import parse_brd
from pbe_editor.ui.board_canvas import BoardCanvas
from pbe_editor.ui.dialogs.nets_dialog import NetsDialog
from pbe_editor.ui.panels.board_right_panel import BoardRightPanel
from pbe_editor.graphics.module_item import BoardModuleGraphicsItem
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

        self.grid_mode = self._load_grid_mode()

        self.setWindowTitle("TraceCAD: Редактор печатной платы")
        self.resize(1200, 800)

        self._apply_startup_geometry()
        self._init_canvas()
        self._init_menu()
        self._init_toolbar()
        self._init_docks()
        self._init_statusbar()
        self._init_shortcuts()
        self._apply_theme()
        self._wire_panels()

        self._load_library_paths()
        self._refresh_library_modules()
        self._apply_grid_series(self.grid_mode, initial=True)

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
        self.setCentralWidget(self.canvas)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.canvas.mouse_moved.connect(self._on_mouse_moved)
        self.canvas.ratsnest_update_requested.connect(self._on_ratsnest_update)
        self.canvas.scene.selectionChanged.connect(self._on_selection_changed)
        self.manager = BoardManager(self.board, self.canvas.scene, self.canvas)

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

        act_save = QAction("Сохранить плату...", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self._on_save_board)
        file_menu.addAction(act_save)

        file_menu.addSeparator()

        act_exit = QAction("Выход", self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

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
        title = QLabel("Модули")
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
            self.canvas.scene.clearSelection()
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

    def _delete_selected(self):
        deleted = []
        for item in list(self.canvas.scene.selectedItems()):
            if isinstance(item, BoardModuleGraphicsItem):
                deleted.append(item.module)
                self.canvas.scene.removeItem(item)
                self.manager.items.pop(item.module.uid, None)
        if deleted:
            self.board.modules = [m for m in self.board.modules if m not in deleted]
            self._populate_module_list()
            self.manager.rebuild_ratsnest()
            self.show_log(f"Удалено модулей: {len(deleted)}")

    def _rotate_selected(self):
        items = [it for it in self.canvas.scene.selectedItems()
                 if isinstance(it, BoardModuleGraphicsItem)]
        if not items:
            return
        for item in items:
            module = item.module
            module.angle = (module.angle + 90.0) % 360.0
            item.setRotation(module.angle)
            item.prepareGeometryChange()
            item.update()
        self.manager.rebuild_ratsnest()
        if len(items) == 1:
            self.right_panel.properties_panel.refresh_values()
        self.show_log(f"Повёрнуто модулей: {len(items)}")

    def _wire_panels(self):
        rp = self.right_panel
        rp.properties_panel.btn_apply.clicked.connect(self._on_apply_properties)

    def _on_apply_properties(self):
        self.manager.rebuild_ratsnest()
        self._populate_module_list()

    def _on_selection_changed(self):
        items = self.canvas.scene.selectedItems()
        if len(items) == 1:
            item = items[0]
            if isinstance(item, (BoardModuleGraphicsItem, RatsnestGraphicsItem)):
                self.right_panel.properties_panel.set_object(item)
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
                self.right_panel.properties_panel.set_object(item)
                self.canvas.centerOn(item)

    def _apply_theme(self):
        app = QApplication.instance()
        app.setStyleSheet(Styles.TOOLTIP)
        self.setStyleSheet(Styles.MAIN_WINDOW)
        self.canvas.apply_theme()
        self.log_label.setStyleSheet(Styles.LOG_LABEL)
        self.right_panel.setStyleSheet(Styles.RIGHT_PANEL)
        self.right_panel.apply_theme()
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
        for path in self.library_paths:
            if path not in self.library_modules:
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

    def _populate_module_list(self):
        self.module_list.clear()
        for module in self.board.modules:
            item = QListWidgetItem(f"{module.reference}  [{module.footprint.name}]")
            item.setToolTip(f"{module.reference} = {module.value}")
            self.module_list.addItem(item)

    def _on_import_net(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть сетлист", "",
            "Netlist (*.net);;All Files (*)"
        )
        if not path:
            return

        self._refresh_library_modules()

        try:
            components = parse_netlist(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разобрать сетлист: {e}")
            return

        self.canvas.scene.clear()
        self.manager.items.clear()
        self.manager.ratsnest_items.clear()

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
                footprint=fp,
                reference=comp.reference,
                value=comp.value,
                x=0.0,
                y=0.0,
                angle=0.0,
                layer="F.Cu",
                uid=next_uid,
            )
            next_uid += 1

            pad_numbers = {p.number for p in fp.pads}
            for pad_number, net_name in comp.pins.items():
                if pad_number not in pad_numbers:
                    continue
                if not net_name:
                    continue
                net = self.board.get_or_create_net(net_name)
                module.pad_nets[pad_number] = PadNet(
                    pad_number=pad_number,
                    net_code=net.code,
                    net_name=net.name,
                )

            self.board.modules.append(module)
            self.manager.add_module(module)

        self._populate_module_list()
        self.manager.rebuild_ratsnest()

        self.setWindowTitle(f"TraceCAD: {self.board.name}")
        self.show_log(f"Импортировано модулей: {len(self.board.modules)}")

        if missing:
            QMessageBox.information(
                self, "Импорт завершён",
                "Импорт выполнен, но не найдены посадочные места:\n" + "\n".join(missing)
            )

    def _on_open_board(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть плату", "",
            "KiCad Board (*.brd);;All Files (*)"
        )
        if not path:
            return
        self._load_board_from_path(path)

    def _load_board_from_path(self, path):
        try:
            board = parse_brd(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть плату: {e}")
            return

        self.canvas.scene.clear()
        self.manager.items.clear()
        self.manager.ratsnest_items.clear()

        self.board = board
        self.manager.board = self.board

        for module in self.board.modules:
            self.manager.add_module(module)

        self._populate_module_list()
        self.manager.rebuild_ratsnest()

        self.board.filename = path
        self.setWindowTitle(f"TraceCAD: {Path(path).name}")
        self.show_log(f"Плата загружена: {Path(path).name} ({len(self.board.modules)} модулей)")

    def _on_save_board(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить плату", "",
            "KiCad Board (*.brd);;All Files (*)"
        )
        if not path:
            return
        if not path.lower().endswith('.brd'):
            path += '.brd'
        try:
            text = build_brd_text(self.board)
            Path(path).write_text(text, encoding='utf-8')
            self.board.filename = path
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
        self.coords_label.setText(f"X: {x:.4f}, Y: {y:.4f}")

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

    def _restore_last_board(self):
        last = self._settings.value(SETTINGS_KEY_BRD_LAST, "", type=str)
        if not last:
            return
        p = Path(last)
        if not p.exists() or not p.is_file():
            return
        self._load_board_from_path(str(p))

    def _save_last_board(self):
        if self.board.filename:
            self._settings.setValue(SETTINGS_KEY_BRD_LAST, self.board.filename)
        else:
            self._settings.setValue(SETTINGS_KEY_BRD_LAST, "")
        self._settings.sync()

    def closeEvent(self, event):
        self._save_last_board()
        super().closeEvent(event)