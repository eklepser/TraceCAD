from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel,
                               QListWidget, QListWidgetItem, QFileDialog,
                               QMessageBox, QComboBox, QToolBar, QStatusBar,
                               QDockWidget, QApplication)
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtCore import Qt, QSettings

from constants import Styles, Steps, apply_theme
from constants.board_settings import SETTINGS_KEY_BRD_LIBS
from footprint_editor.kicad.importer import parse_kicad_mod
from pbe_editor.core.board_models import Board, BoardModule, PadNet
from pbe_editor.core.board_manager import BoardManager
from pbe_editor.core.netlist_parser import parse_netlist
from pbe_editor.kicad.brd_exporter import build_brd_text
from pbe_editor.ui.board_canvas import BoardCanvas
from pbe_editor.ui.dialogs.nets_dialog import NetsDialog


class BoardEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._settings = QSettings("TraceCAD", "TraceCAD")
        apply_theme()

        self.board = Board()
        self.library_paths = []
        self.library_modules = {}

        self.setWindowTitle("TraceCAD: Редактор печатной платы")
        self.resize(1200, 800)

        self._apply_startup_geometry()
        self._init_canvas()
        self._init_menu()
        self._init_toolbar()
        self._init_docks()
        self._init_statusbar()
        self._apply_theme()

        self._load_library_paths()
        self._refresh_library_modules()

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
        self.manager = BoardManager(self.board, self.canvas.scene, self.canvas)

    def _init_menu(self):
        menubar = self.menuBar()

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

        act_lib = QAction("Добавить библиотеку...", self)
        act_lib.triggered.connect(self._on_add_library)
        file_menu.addAction(act_lib)

        file_menu.addSeparator()

        act_exit = QAction("Выход", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        view_menu = menubar.addMenu("Вид")

        act_nets = QAction("Список связей...", self)
        act_nets.triggered.connect(self._on_show_nets)
        view_menu.addAction(act_nets)

    def _init_toolbar(self):
        toolbar = QToolBar("Сетка", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addWidget(QLabel(" Шаг сетки: "))
        self.grid_combo = QComboBox()
        self.grid_combo.addItems(Steps.GRID_1X)
        self.grid_combo.setCurrentText(Steps.DEFAULT_GRID)
        self.grid_combo.currentTextChanged.connect(self._on_grid_changed)
        toolbar.addWidget(self.grid_combo)

        toolbar.addSeparator()
        self.zoom_label = QLabel(" 100% ")
        toolbar.addWidget(self.zoom_label)

    def _init_docks(self):
        self.module_dock = QDockWidget("Модули на плате", self)
        self.module_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)

        self.module_list = QListWidget()
        self.module_list.setStyleSheet(Styles.LIST_BG)
        layout.addWidget(self.module_list)

        self.module_dock.setWidget(panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.module_dock)

    def _init_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.log_label = QLabel("Готово.")
        sb.addWidget(self.log_label)
        self.coords_label = QLabel("X: 0.0000, Y: 0.0000")
        sb.addPermanentWidget(self.coords_label)

    def _apply_theme(self):
        app = QApplication.instance()
        app.setStyleSheet(Styles.TOOLTIP)
        self.setStyleSheet(Styles.MAIN_WINDOW)
        self.canvas.apply_theme()
        self.log_label.setStyleSheet(Styles.LOG_LABEL)

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
        self.module_list.clear()

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

            for pad_number, net_name in comp.pins.items():
                net = self.board.get_or_create_net(net_name)
                module.pad_nets[pad_number] = PadNet(
                    pad_number=pad_number,
                    net_code=net.code,
                    net_name=net.name,
                )

            self.board.modules.append(module)
            self.manager.add_module(module)

            item = QListWidgetItem(f"{module.reference}  [{module.footprint.name}]")
            item.setToolTip(f"{module.reference} = {module.value}")
            self.module_list.addItem(item)

        self.setWindowTitle(f"TraceCAD: {self.board.name}")
        self.show_log(f"Импортировано модулей: {len(self.board.modules)}")

        if missing:
            QMessageBox.information(
                self, "Импорт завершён",
                "Импорт выполнен, но не найдены посадочные места:\n" + "\n".join(missing)
            )

    def _on_open_board(self):
        QMessageBox.information(
            self, "Пока не реализовано",
            "Чтение .brd будет добавлено позже."
        )

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

    def _on_add_library(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Добавить библиотеку .mod", "",
            "KiCad Library (*.mod);;All Files (*)"
        )
        if not path:
            return
        if path in self.library_paths:
            return
        self.library_paths.append(path)
        self._save_library_paths()
        self._refresh_library_modules()
        self.show_log(f"Библиотека добавлена: {Path(path).name}")

    def _on_show_nets(self):
        dlg = NetsDialog(self.board, self)
        dlg.exec()

    def _on_grid_changed(self, text):
        if not text:
            return
        self.canvas.grid_size = float(text)
        self.canvas.viewport().update()

    def _on_mouse_moved(self, x, y):
        self.coords_label.setText(f"X: {x:.4f}, Y: {y:.4f}")

    def _update_zoom_label(self, zoom):
        self.zoom_label.setText(f" {int(zoom * 100)}% ")

    def show_log(self, text):
        self.log_label.setText(text)