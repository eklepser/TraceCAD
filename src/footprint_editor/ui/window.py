import copy
import uuid
import math
import re
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QToolBar, QStatusBar, QComboBox, QApplication, QGraphicsView,
                               QDialog, QLineEdit, QDoubleSpinBox, QCheckBox, QPushButton,
                               QFileDialog, QMessageBox, QInputDialog, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, QEvent, QObject, QPointF, Signal, QSettings
from PySide6.QtGui import QKeyEvent, QAction, QActionGroup

from constants import (Tool, PAN_KEYS, Steps, Styles, VK_ESCAPE, VK_DELETE, VK_F1, VK_F2,
                       VK_C, VK_V, VK_S, VK_R, apply_theme)
from footprint_editor.core.models import (Footprint, Pad, PadShape, PadType, Line, Circle,
                                          Arc, Text, TextType)
from footprint_editor.core.manager import FootprintManager
from footprint_editor.core.arc_geometry import arc_sample_points
from footprint_editor.core.kicad_parser import (
    parse_kicad_mod, parse_kicad_content, mm_to_kicad
)
from footprint_editor.ui.canvas import FootprintCanvas
from footprint_editor.graphics.pad_item import PadGraphicsItem
from footprint_editor.graphics.line_item import LineGraphicsItem
from footprint_editor.graphics.circle_item import CircleGraphicsItem
from footprint_editor.graphics.arc_item import ArcGraphicsItem
from footprint_editor.graphics.text_item import TextGraphicsItem
from footprint_editor.ui.right_panel import RightPanel
from footprint_editor.ui.libraries_dialog import LibrariesManagerDialog


SETTINGS_ORG = "TraceCAD"
SETTINGS_APP = "TraceCAD"
SETTINGS_KEY_LIBS = "library_paths"
SETTINGS_KEY_THEME = "theme"

LEFT_PANEL_MIN_WIDTH = 160
LEFT_PANEL_MAX_WIDTH = 320


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
        self.size_spin.setRange(0.05, 10.0)
        self.size_spin.setSingleStep(0.1)
        self.size_spin.setDecimals(2)
        self.size_spin.setValue(1.0)
        self.size_spin.setStyleSheet(Styles.INPUT_BG)
        self.size_spin.valueChanged.connect(self.size_changed.emit)
        size_layout.addWidget(self.size_spin)
        layout.addLayout(size_layout)

        self.visible_check = QCheckBox("Видимый")
        self.visible_check.setChecked(True)
        self.visible_check.stateChanged.connect(
            lambda state: self.visible_changed.emit(state == Qt.CheckState.Checked.value)
        )
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

        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.theme = self._settings.value(SETTINGS_KEY_THEME, "dark", type=str)
        apply_theme(self.theme)

        self.footprint = footprint or Footprint(name="New_Footprint")
        self.current_module_name = self.footprint.name
        self._modified = False
        self.unsaved_modules = {}

        self.setWindowTitle(f"TraceCAD - Редактор корпусов: {self.footprint.name}")
        self.resize(1000, 700)

        self.current_tool = Tool.SELECT
        self.line_start_point = None
        self.circle_center_point = None
        self.arc_center_point = None
        self.arc_start_point = None
        self.text_position = None
        self.clipboard = []
        self._current_mouse_scene_pos = QPointF(0, 0)

        self.library_paths = []
        self.library_modules = {}
        self.current_library_path = None

        self.log_label = QLabel("Готово.")

        self._init_menu()

        self.canvas = FootprintCanvas(self)
        self.setCentralWidget(self.canvas)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.canvas.canvas_clicked.connect(self._on_canvas_clicked)
        self.canvas.mouse_moved.connect(self._on_mouse_moved)
        self.canvas.finish_drawing.connect(self._finish_drawing)
        self.canvas.scene.selectionChanged.connect(self._on_selection_changed)
        self.canvas.content_changed.connect(self._mark_dirty)

        self.manager = FootprintManager(self.footprint, self.canvas.scene, self.canvas)

        self.key_filter = GlobalKeyFilter(self)
        QApplication.instance().installEventFilter(self.key_filter)

        self._init_docks()
        self._init_toolbars()
        self._init_statusbar()
        self._connect_right_panel()

        self._ensure_reference_and_value()

        self._load_library_paths()
        self._refresh_library_list()

        self.resizeDocks([self.library_dock], [LEFT_PANEL_MIN_WIDTH],
                         Qt.Orientation.Horizontal)
        self.resizeDocks([self.properties_dock], [LEFT_PANEL_MIN_WIDTH],
                         Qt.Orientation.Horizontal)

        self._apply_theme()

    def _apply_theme(self):
        app = QApplication.instance()
        app.setStyleSheet(Styles.TOOLTIP)
        self.setStyleSheet(Styles.MAIN_WINDOW)
        self.canvas.apply_theme()
        self.right_panel.setStyleSheet(Styles.RIGHT_PANEL)
        self.right_panel.apply_theme()
        self.library_list_widget.setStyleSheet(Styles.LIST_BG)
        self.module_list_widget.setStyleSheet(Styles.LIST_BG)
        self.btn_add_library.setStyleSheet(Styles.BUTTON_OK)
        self.btn_add_module.setStyleSheet(Styles.BUTTON_OK)
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

    def _ensure_reference_and_value(self):
        has_ref = any(t.text_type == TextType.REFERENCE for t in self.footprint.texts)
        has_val = any(t.text_type == TextType.VALUE for t in self.footprint.texts)

        if not has_ref:
            ref = Text(0, 0, self.footprint.reference, 1.0, True, TextType.REFERENCE, locked=True)
            self.footprint.texts.append(ref)
            self.manager.add_model(ref)

        if not has_val:
            val = Text(0, 1, self.footprint.value, 1.0, True, TextType.VALUE, locked=True)
            self.footprint.texts.append(val)
            self.manager.add_model(val)

    def _mark_dirty(self):
        self._modified = True
        self.unsaved_modules[self.current_module_name] = self.footprint
        self._update_module_list_display()

    def _update_module_list_display(self):
        for i in range(self.module_list_widget.count()):
            item = self.module_list_widget.item(i)
            name = item.data(Qt.ItemDataRole.UserRole)
            if name is None:
                continue
            if name in self.unsaved_modules:
                item.setText(f"{name} *")
            else:
                item.setText(name)

    def _stash_current_module(self):
        if self._modified:
            self.unsaved_modules[self.current_module_name] = self.footprint

    def _init_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Файл")

        lib_menu = file_menu.addMenu("Библиотека")
        lib_menu.addAction("Создать", self._on_create_library)
        lib_menu.addAction("Открыть", self._on_select_library)
        lib_menu.addAction("Управление", self._on_show_libraries)

        mod_menu = file_menu.addMenu("Корпус")
        mod_menu.addAction("Создать", self._on_add_new_module_clicked)
        mod_menu.addAction("Открыть", self._on_open_module_file)

        file_menu.addSeparator()

        act_exit = QAction("Выход", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        view_menu = menubar.addMenu("Вид")

        theme_menu = view_menu.addMenu("Тема")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        dark_act = QAction("Тёмная", self, checkable=True)
        dark_act.setChecked(self.theme == "dark")
        dark_act.triggered.connect(lambda: self._set_theme("dark"))
        theme_group.addAction(dark_act)
        theme_menu.addAction(dark_act)

        light_act = QAction("Светлая", self, checkable=True)
        light_act.setChecked(self.theme == "light")
        light_act.triggered.connect(lambda: self._set_theme("light"))
        theme_group.addAction(light_act)
        theme_menu.addAction(light_act)

        self._theme_group = theme_group

    def _load_library_paths(self):
        saved = self._settings.value(SETTINGS_KEY_LIBS, "", type=str)
        if saved:
            self.library_paths = [p for p in saved.split("\n") if p.strip()]

    def _save_library_paths(self):
        self._settings.setValue(SETTINGS_KEY_LIBS, "\n".join(self.library_paths))
        self._settings.sync()

    def _refresh_library_list(self):
        self.library_list_widget.clear()
        for path in self.library_paths:
            item = QListWidgetItem(Path(path).stem)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.library_list_widget.addItem(item)

    def _on_add_library_clicked(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Добавить библиотеку KiCad", "",
            "KiCad Library (*.mod);;All Files (*)"
        )
        if not path:
            return
        if path in self.library_paths:
            QMessageBox.information(self, "Информация", "Эта библиотека уже добавлена.")
            return
        self.library_paths.append(path)
        self._save_library_paths()
        self._refresh_library_list()
        self.show_log(f"Библиотека добавлена: {Path(path).name}")

    def _on_show_libraries(self):
        dlg = LibrariesManagerDialog(self.library_paths, self)
        if dlg.exec() == QDialog.Accepted:
            new_paths = dlg.get_library_paths()
            if new_paths != self.library_paths:
                self.library_paths = new_paths
                if self.current_library_path not in self.library_paths:
                    self.current_library_path = None
                    self.module_list_widget.clear()
                self._save_library_paths()
                self._refresh_library_list()

    def _on_library_item_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path is None:
            return
        if path not in self.library_modules:
            try:
                footprints = parse_kicad_mod(path)
                self.library_modules[path] = {fp.name: fp for fp in footprints}
            except Exception as e:
                self.show_log(f"Ошибка загрузки библиотеки: {e}")
                return
        self.current_library_path = path
        self._populate_module_list()
        self.show_log(f"Библиотека: {Path(path).name}")

    def _populate_module_list(self):
        self.module_list_widget.clear()
        if self.current_library_path and self.current_library_path in self.library_modules:
            for name in sorted(self.library_modules[self.current_library_path].keys()):
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, name)
                item.setToolTip(name)
                self.module_list_widget.addItem(item)
        self._update_module_list_display()

    def _reload_current_library(self):
        if not self.current_library_path:
            return
        try:
            footprints = parse_kicad_mod(self.current_library_path)
            self.library_modules[self.current_library_path] = {fp.name: fp for fp in footprints}
            self._populate_module_list()
        except Exception as e:
            self.show_log(f"Ошибка перезагрузки: {e}")

    def _on_module_item_clicked(self, item):
        name = item.data(Qt.ItemDataRole.UserRole)
        if name is None:
            return
        if name == self.current_module_name:
            return

        self._stash_current_module()

        if name in self.unsaved_modules:
            self._load_module(self.unsaved_modules[name])
            self._modified = True
            self._update_module_list_display()
            return

        if self.current_library_path and self.current_library_path in self.library_modules:
            module = self.library_modules[self.current_library_path].get(name)
            if module:
                self._load_module(copy.deepcopy(module))

    def _on_select_library(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть библиотеку KiCad", "",
            "KiCad Library (*.mod);;All Files (*)"
        )
        if path:
            if path not in self.library_paths:
                self.library_paths.append(path)
                self._save_library_paths()
                self._refresh_library_list()
            self._load_library(path)

    def _load_library(self, path):
        try:
            footprints = parse_kicad_mod(path)
            self.library_modules[path] = {fp.name: fp for fp in footprints}
            self.current_library_path = path
            self._populate_module_list()
            self.show_log(f"Библиотека загружена: {Path(path).name} ({len(footprints)} модулей)")
        except Exception as e:
            self.show_log(f"Ошибка загрузки библиотеки: {e}")

    def _on_create_library(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Создать библиотеку", "",
            "KiCad Library (*.mod);;All Files (*)"
        )
        if path:
            if not path.lower().endswith('.mod'):
                path += '.mod'
            Path(path).write_text(
                "PCBNEW-LibModule-V1\n# encoding utf-8\n$INDEX\n$EndINDEX\n$EndLIBRARY\n",
                encoding='utf-8'
            )
            if path not in self.library_paths:
                self.library_paths.append(path)
                self._save_library_paths()
                self._refresh_library_list()
            self._load_library(path)
            self.show_log(f"Библиотека создана: {Path(path).name}")

    def _on_add_new_module_clicked(self):
        name, ok = QInputDialog.getText(self, "Новый корпус", "Имя корпуса:")
        if not ok or not name:
            return

        self._stash_current_module()

        self.footprint = Footprint(name=name)
        self.manager.footprint = self.footprint
        self.canvas.scene.clear()
        self.manager.items.clear()
        self._ensure_reference_and_value()
        self.current_module_name = name
        self._modified = False
        self.setWindowTitle(f"TraceCAD - Редактор корпусов: {name}")

        if self.current_library_path:
            try:
                self._replace_module_in_library(self.current_library_path, name)
                self._reload_current_library()
                self.show_log(f"Создан корпус: {name} (добавлен в библиотеку)")
            except Exception as e:
                self.show_log(f"Ошибка сохранения: {e}")
        else:
            self.show_log(f"Создан корпус: {name}")

    def _on_open_module_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть корпус", "",
            "KiCad Module (*.mod);;All Files (*)"
        )
        if not path:
            return
        try:
            footprints = parse_kicad_mod(path)
            if not footprints:
                QMessageBox.warning(self, "Пусто", "В файле нет модулей.")
                return
            self._stash_current_module()
            self._load_module(copy.deepcopy(footprints[0]))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {e}")

    def _on_save_current(self):
        if not self.current_library_path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить модуль", "",
                "KiCad Module (*.mod);;All Files (*)"
            )
            if not path:
                return
            if not path.lower().endswith('.mod'):
                path += '.mod'
            self._export_to_kicad(path)
            self.unsaved_modules.pop(self.current_module_name, None)
            self._modified = False
            self._update_module_list_display()
            self.show_log(f"Модуль сохранён: {Path(path).name}")
            return

        try:
            self._replace_module_in_library(self.current_library_path, self.current_module_name)
            self._reload_current_library()
            self.unsaved_modules.pop(self.current_module_name, None)
            self._modified = False
            self._update_module_list_display()
            self.show_log(f"Модуль сохранён: {self.current_module_name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def _replace_module_in_library(self, path, module_name):
        content = Path(path).read_text(encoding='utf-8', errors='ignore')
        pattern = re.compile(
            r'\$MODULE\s+' + re.escape(module_name) + r'\b.*?\$EndMODULE[^\n]*\n',
            re.DOTALL
        )
        content = pattern.sub('', content)
        module_text = self._build_kicad_module_text()
        end_marker = "$EndLIBRARY"
        if end_marker in content:
            idx = content.rfind(end_marker)
            content = content[:idx] + module_text + "\n" + end_marker + "\n"
        else:
            content = content.rstrip() + "\n" + module_text + "\n" + end_marker + "\n"
        Path(path).write_text(content, encoding='utf-8')

    def _load_module(self, module):
        self.footprint = module
        self.manager.footprint = self.footprint
        self.canvas.scene.clear()
        self.manager.items.clear()

        for pad in self.footprint.pads:
            self.manager.add_model(pad)
        for line in self.footprint.lines:
            self.manager.add_model(line)
        for circle in self.footprint.circles:
            self.manager.add_model(circle)
        for arc in self.footprint.arcs:
            self.manager.add_model(arc)
        for text in self.footprint.texts:
            self.manager.add_model(text)

        self._ensure_reference_and_value()
        self.current_module_name = module.name
        self._modified = module.name in self.unsaved_modules
        self.setWindowTitle(f"TraceCAD - Редактор корпусов: {module.name}")
        self._update_module_list_display()
        self.show_log(f"Загружен модуль: {module.name}")

    def _build_kicad_module_text(self):
        lines = []
        lines.append(f"$MODULE {self.footprint.name}")
        lines.append("Po 0 0 0 15 00000000 00000000 ~~")
        lines.append(f"Li {self.footprint.name}")
        lines.append("Sc 00000000")
        lines.append("AR")
        lines.append("Op 0 0 0")

        for text in self.footprint.texts:
            if text.text_type == TextType.REFERENCE:
                idx = 0
            elif text.text_type == TextType.VALUE:
                idx = 1
            else:
                continue

            x_k = mm_to_kicad(text.x)
            y_k = mm_to_kicad(text.y)
            size_k = mm_to_kicad(text.size)
            vis_flag = 'V' if text.visible else 'I'
            lines.append(
                f'T{idx} {x_k} {y_k} {size_k} {size_k} 0 120 N {vis_flag} 21 N "{text.text}"'
            )

        for line in self.footprint.lines:
            x1 = mm_to_kicad(line.x1)
            y1 = mm_to_kicad(line.y1)
            x2 = mm_to_kicad(line.x2)
            y2 = mm_to_kicad(line.y2)
            t = mm_to_kicad(line.width)
            lines.append(f"DS {x1} {y1} {x2} {y2} {t} 21")

        for circle in self.footprint.circles:
            x_c = mm_to_kicad(circle.x)
            y_c = mm_to_kicad(circle.y)
            r_k = mm_to_kicad(circle.radius)
            x_p = x_c + r_k
            y_p = y_c
            t = mm_to_kicad(circle.width)
            lines.append(f"DC {x_c} {y_c} {x_p} {y_p} {t} 21")

        for arc in self.footprint.arcs:
            cx = mm_to_kicad(arc.cx)
            cy = mm_to_kicad(arc.cy)
            sx = mm_to_kicad(arc.sx)
            sy = mm_to_kicad(arc.sy)
            a = int(round(arc.angle * 10))
            t = mm_to_kicad(arc.width)
            lines.append(f"DA {cx} {cy} {sx} {sy} {a} {t} 21")

        for pad in self.footprint.pads:
            lines.append("$PAD")
            shape_map = {PadShape.RECT: 'R', PadShape.CIRCLE: 'C', PadShape.OVAL: 'O'}
            shape_char = shape_map.get(pad.shape, 'C')
            sx = mm_to_kicad(pad.width)
            sy = mm_to_kicad(pad.height)
            drill = mm_to_kicad(pad.drill or 0)
            x = mm_to_kicad(pad.x)
            y = mm_to_kicad(pad.y)
            attr = 'STD' if pad.pad_type == PadType.THT else 'SMD'
            lines.append(f'Sh "{pad.number}" {shape_char} {sx} {sy} 0 0 0')
            lines.append(f"Dr {drill} 0 0")
            lines.append(f"At {attr} N 00E0FFFF")
            lines.append('Ne 0 ""')
            lines.append(f"Po {x} {y}")
            lines.append("$EndPAD")

        lines.append(f"$EndMODULE  {self.footprint.name}")
        return "\n".join(lines)

    def _export_to_kicad(self, filepath):
        lines = []
        lines.append(f"PCBNEW-LibModule-V1  {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        lines.append("# encoding utf-8")
        lines.append("$INDEX")
        lines.append(self.footprint.name)
        lines.append("$EndINDEX")
        lines.append(self._build_kicad_module_text())
        lines.append("$EndLIBRARY")
        Path(filepath).write_text('\n'.join(lines), encoding='utf-8')

    def show_log(self, text):
        self.log_label.setText(text)

    def _build_library_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(LEFT_PANEL_MIN_WIDTH)
        panel.setMaximumWidth(LEFT_PANEL_MAX_WIDTH)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        lib_header = QHBoxLayout()
        lib_header.setContentsMargins(0, 0, 0, 0)
        lbl_libs = QLabel("Библиотеки")
        lbl_libs.setStyleSheet("font-weight: bold;")
        lib_header.addWidget(lbl_libs)
        lib_header.addStretch()

        self.btn_add_library = QPushButton("+")
        self.btn_add_library.setFixedSize(24, 24)
        self.btn_add_library.setToolTip("Добавить библиотеку")
        self.btn_add_library.setStyleSheet(Styles.BUTTON_OK)
        self.btn_add_library.clicked.connect(self._on_add_library_clicked)
        lib_header.addWidget(self.btn_add_library)
        layout.addLayout(lib_header)

        self.library_list_widget = QListWidget()
        self.library_list_widget.setStyleSheet(Styles.LIST_BG)
        self.library_list_widget.itemClicked.connect(self._on_library_item_clicked)
        layout.addWidget(self.library_list_widget, 1)

        mod_header = QHBoxLayout()
        mod_header.setContentsMargins(0, 0, 0, 0)
        lbl_mods = QLabel("Корпуса")
        lbl_mods.setStyleSheet("font-weight: bold;")
        mod_header.addWidget(lbl_mods)
        mod_header.addStretch()

        self.btn_add_module = QPushButton("+")
        self.btn_add_module.setFixedSize(24, 24)
        self.btn_add_module.setToolTip("Добавить корпус")
        self.btn_add_module.setStyleSheet(Styles.BUTTON_OK)
        self.btn_add_module.clicked.connect(self._on_add_new_module_clicked)
        mod_header.addWidget(self.btn_add_module)
        layout.addLayout(mod_header)

        self.module_list_widget = QListWidget()
        self.module_list_widget.setStyleSheet(Styles.LIST_BG)
        self.module_list_widget.itemClicked.connect(self._on_module_item_clicked)
        layout.addWidget(self.module_list_widget, 1)

        return panel

    def _hide_dock_title(self, dock):
        empty = QWidget()
        empty.setFixedHeight(0)
        dock.setTitleBarWidget(empty)

    def _init_docks(self):
        self.properties_dock = QDockWidget("", self)
        self.properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.right_panel = RightPanel()
        self.right_panel.setStyleSheet(Styles.RIGHT_PANEL)

        self.properties_dock.setWidget(self.right_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        self._hide_dock_title(self.properties_dock)

        self.library_dock = QDockWidget("", self)
        self.library_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.library_dock.setWidget(self._build_library_panel())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.library_dock)
        self._hide_dock_title(self.library_dock)

    def _connect_right_panel(self):
        self._active_tool_button = self.right_panel.btn_select
        self.right_panel.btn_select.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_select))
        self.right_panel.btn_add_pad.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_pad))
        self.right_panel.btn_add_line.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_line))
        self.right_panel.btn_add_circle.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_circle))
        self.right_panel.btn_add_arc.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_arc))
        self.right_panel.btn_add_text.clicked.connect(lambda: self._on_tool_button_clicked(self.right_panel.btn_add_text))
        self.right_panel.btn_delete.clicked.connect(self._delete_selected)
        self.right_panel.properties_panel.btn_apply.clicked.connect(self._mark_dirty)

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

        self.status_bar.addWidget(self.log_label)

        self.coords_label = QLabel("X: 0.0000, Y: 0.0000")
        self.status_bar.addPermanentWidget(self.coords_label)

    def _on_tool_button_clicked(self, button):
        self._active_tool_button = button
        if button == self.right_panel.btn_select:
            self.current_tool = Tool.SELECT
        elif button == self.right_panel.btn_add_pad:
            self.current_tool = Tool.ADD_PAD
        elif button == self.right_panel.btn_add_line:
            self.current_tool = Tool.ADD_LINE
        elif button == self.right_panel.btn_add_circle:
            self.current_tool = Tool.ADD_CIRCLE
        elif button == self.right_panel.btn_add_arc:
            self.current_tool = Tool.ADD_ARC
        elif button == self.right_panel.btn_add_text:
            self.current_tool = Tool.ADD_TEXT

        self.right_panel.update_tool_buttons(button)

        self.line_start_point = None
        self.circle_center_point = None
        self.arc_center_point = None
        self.arc_start_point = None
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

        self.show_log(f"Инструмент: {self.current_tool}")

    def _finish_drawing(self):
        self.line_start_point = None
        self.circle_center_point = None
        self.arc_center_point = None
        self.arc_start_point = None
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
            new_pad = Pad(number=next_num, shape=PadShape.CIRCLE, pad_type=PadType.SMD,
                          x=x, y=y, width=1.5, height=1.5, drill=0.8)
            self.footprint.pads.append(new_pad)
            self.manager.add_model(new_pad)
            self.canvas.set_interaction_enabled(False)
            self._mark_dirty()
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
                self._mark_dirty()
                self.show_log('элемент "линия" установлен')

        elif self.current_tool == Tool.ADD_CIRCLE:
            if self.circle_center_point is None:
                self.circle_center_point = (x, y)
                self.canvas.set_ghost_circle(x, y, 0.0)
            else:
                cx, cy = self.circle_center_point
                r = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                r = round(r / self.canvas.grid_size) * self.canvas.grid_size
                if r > 0:
                    new_circle = Circle(cx, cy, r)
                    self.footprint.circles.append(new_circle)
                    self.manager.add_model(new_circle)
                    self.canvas.set_interaction_enabled(False)
                    self._mark_dirty()
                    self.show_log('элемент "окружность" установлен')
                self.circle_center_point = None
                self.canvas.clear_ghost_circle()

        elif self.current_tool == Tool.ADD_ARC:
            if self.arc_center_point is None:
                self.arc_center_point = (x, y)
                self.canvas.set_ghost_line(x, y, x, y)
            elif self.arc_start_point is None:
                self.arc_start_point = (x, y)
                self.canvas.set_ghost_line(self.arc_center_point[0], self.arc_center_point[1], x, y)
                self._show_arc_dialog()
            else:
                self.arc_center_point = (x, y)
                self.arc_start_point = None
                self.canvas.set_ghost_line(x, y, x, y)

        elif self.current_tool == Tool.ADD_TEXT:
            self.text_position = (x, y)
            self.canvas.set_ghost_text(x, y, "", 1.0, True)
            self._show_text_dialog()

    def _show_arc_dialog(self):
        angle, ok = QInputDialog.getDouble(
            self, "Угол дуги", "Угол дуги (градусы, + против ЧС):",
            90.0, -359.0, 359.0, 1
        )
        if ok and self.arc_center_point and self.arc_start_point:
            new_arc = Arc(
                cx=self.arc_center_point[0], cy=self.arc_center_point[1],
                sx=self.arc_start_point[0], sy=self.arc_start_point[1],
                angle=angle
            )
            self.footprint.arcs.append(new_arc)
            self.manager.add_model(new_arc)
            self.canvas.set_interaction_enabled(False)
            self._mark_dirty()
            self.show_log('элемент "дуга" установлен')
        self.arc_center_point = None
        self.arc_start_point = None
        self.canvas.clear_ghost_line()

    def _show_text_dialog(self):
        dialog = TextDialog(self)
        dialog.text_changed.connect(
            lambda text: self.canvas.set_ghost_text(*self.text_position, text, dialog.get_size(), dialog.get_visible())
        )
        dialog.size_changed.connect(
            lambda size: self.canvas.set_ghost_text(*self.text_position, dialog.get_text(), size, dialog.get_visible())
        )
        dialog.visible_changed.connect(
            lambda visible: self.canvas.set_ghost_text(*self.text_position, dialog.get_text(), dialog.get_size(), visible)
        )

        if dialog.exec() == QDialog.Accepted:
            text = dialog.get_text()
            size = dialog.get_size()
            visible = dialog.get_visible()
            if text:
                new_text = Text(self.text_position[0], self.text_position[1], text, size, visible)
                self.footprint.texts.append(new_text)
                self.manager.add_model(new_text)
                self.canvas.set_interaction_enabled(False)
                self._mark_dirty()
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
            r = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            r = round(r / self.canvas.grid_size) * self.canvas.grid_size
            self.canvas.set_ghost_circle(cx, cy, r)
        elif self.current_tool == Tool.ADD_ARC and self.arc_center_point and self.arc_start_point is None:
            self.canvas.set_ghost_line(self.arc_center_point[0], self.arc_center_point[1], x, y)
        else:
            self.canvas.clear_ghost_line()
            self.canvas.clear_ghost_circle()

    def _on_selection_changed(self):
        selected_items = self.canvas.scene.selectedItems()
        has_selection = len(selected_items) > 0
        self.right_panel.btn_delete.setEnabled(has_selection)

        if len(selected_items) == 1:
            item = selected_items[0]
            if isinstance(item, (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem,
                                 ArcGraphicsItem, TextGraphicsItem)):
                if getattr(item.model, 'locked', False):
                    self.right_panel.btn_delete.setEnabled(False)
                self.right_panel.properties_panel.set_object(item.model)
            else:
                self.right_panel.properties_panel.clear_panel()
        else:
            self.right_panel.properties_panel.clear_panel()

    def _delete_selected(self):
        selected_items = self.canvas.scene.selectedItems()
        deleted_any = False
        for item in selected_items:
            if isinstance(item, (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem,
                                 ArcGraphicsItem, TextGraphicsItem)):
                if getattr(item.model, 'locked', False):
                    continue
                if item.model in self.footprint.pads:
                    self.footprint.pads.remove(item.model)
                if item.model in self.footprint.lines:
                    self.footprint.lines.remove(item.model)
                if item.model in self.footprint.circles:
                    self.footprint.circles.remove(item.model)
                if item.model in self.footprint.arcs:
                    self.footprint.arcs.remove(item.model)
                if item.model in self.footprint.texts:
                    self.footprint.texts.remove(item.model)
                self.manager.remove_model(item.model)
                deleted_any = True

        self.right_panel.btn_delete.setEnabled(False)
        self.right_panel.properties_panel.clear_panel()
        if deleted_any:
            self._mark_dirty()
        self.show_log("элементы удалены")

    def _copy_selected(self):
        self.clipboard = []
        for item in self.canvas.scene.selectedItems():
            if isinstance(item, (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem,
                                 ArcGraphicsItem, TextGraphicsItem)):
                if not getattr(item.model, 'locked', False):
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
                center_x += (model.x1 + model.x2) / 2; center_y += (model.y1 + model.y2) / 2; count += 1
            elif isinstance(model, Circle):
                center_x += model.x; center_y += model.y; count += 1
            elif isinstance(model, Arc):
                center_x += model.cx; center_y += model.cy; count += 1
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
            new_model.locked = False

            if isinstance(new_model, Pad):
                new_model.x += dx; new_model.y += dy
                self.footprint.pads.append(new_model)
            elif isinstance(new_model, Line):
                new_model.x1 += dx; new_model.y1 += dy
                new_model.x2 += dx; new_model.y2 += dy
                self.footprint.lines.append(new_model)
            elif isinstance(new_model, Circle):
                new_model.x += dx; new_model.y += dy
                self.footprint.circles.append(new_model)
            elif isinstance(new_model, Arc):
                new_model.cx += dx; new_model.cy += dy
                new_model.sx += dx; new_model.sy += dy
                self.footprint.arcs.append(new_model)
            elif isinstance(new_model, Text):
                new_model.x += dx; new_model.y += dy
                self.footprint.texts.append(new_model)

            item = self.manager.add_model(new_model)
            item.setSelected(True)

        self._mark_dirty()
        self.show_log("(буфер обмена) элементы установлены")

    def _rotate_point_90(self, x, y, cx, cy):
        dx = x - cx
        dy = y - cy
        return (cx - dy, cy + dx)

    def _rotate_model_90(self, model, cx, cy):
        if isinstance(model, Pad):
            model.x, model.y = self._rotate_point_90(model.x, model.y, cx, cy)
            if model.shape in (PadShape.RECT, PadShape.OVAL):
                model.width, model.height = model.height, model.width
        elif isinstance(model, Line):
            model.x1, model.y1 = self._rotate_point_90(model.x1, model.y1, cx, cy)
            model.x2, model.y2 = self._rotate_point_90(model.x2, model.y2, cx, cy)
        elif isinstance(model, Circle):
            model.x, model.y = self._rotate_point_90(model.x, model.y, cx, cy)
        elif isinstance(model, Arc):
            model.cx, model.cy = self._rotate_point_90(model.cx, model.cy, cx, cy)
            model.sx, model.sy = self._rotate_point_90(model.sx, model.sy, cx, cy)
        elif isinstance(model, Text):
            model.x, model.y = self._rotate_point_90(model.x, model.y, cx, cy)

    def _model_bounds(self, model):
        if isinstance(model, Pad):
            hw = model.width / 2.0
            hh = model.height / 2.0
            return [(model.x - hw, model.y - hh), (model.x + hw, model.y + hh)]
        if isinstance(model, Line):
            return [(model.x1, model.y1), (model.x2, model.y2)]
        if isinstance(model, Circle):
            return [(model.x - model.radius, model.y - model.radius),
                    (model.x + model.radius, model.y + model.radius)]
        if isinstance(model, Arc):
            return arc_sample_points(model.cx, model.cy, model.sx, model.sy, model.angle, 16)
        if isinstance(model, Text):
            return [(model.x, model.y), (model.x, model.y)]
        return []

    def _rotate_selected(self):
        selected_items = self.canvas.scene.selectedItems()
        items = [it for it in selected_items
                 if isinstance(it, (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem,
                                    ArcGraphicsItem, TextGraphicsItem))]
        if not items:
            return

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        for item in items:
            for px, py in self._model_bounds(item.model):
                min_x = min(min_x, px); min_y = min(min_y, py)
                max_x = max(max_x, px); max_y = max(max_y, py)

        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0

        for item in items:
            self._rotate_model_90(item.model, cx, cy)
            if isinstance(item, PadGraphicsItem):
                item.setPos(item.model.x, item.model.y)
            item.update_geometry()

        self._mark_dirty()
        self.show_log("элементы повёрнуты на 90°")

    def handle_global_key(self, event):
        vk = event.nativeVirtualKey()
        modifiers = event.modifiers()
        ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)

        if event.type() == QEvent.Type.KeyPress:
            if ctrl:
                if vk == VK_C:
                    self._copy_selected()
                    return True
                elif vk == VK_V:
                    self._paste_from_clipboard()
                    return True
                elif vk == VK_S:
                    self._on_save_current()
                    return True
                return False

            if vk == VK_R:
                self._rotate_selected()
                return True

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

        elif event.type() == QEvent.Type.KeyRelease:
            if vk in PAN_KEYS:
                self.canvas.pressed_keys.discard(vk)
                if not self.canvas.pressed_keys:
                    self.canvas.pan_timer.stop()
                return True

        return False