import copy
import math
import re
from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox
from PySide6.QtCore import QPointF

from constants import Tool, Sizes
from footprint_editor.core.models import (
    Footprint, Pad, PadShape, PadType, Line, Circle, Arc, Text, TextType, new_uid
)
from footprint_editor.core.kicad_parser import parse_kicad_mod
from footprint_editor.core.arc_geometry import arc_sample_points
from footprint_editor.graphics.pad_item import PadGraphicsItem
from footprint_editor.graphics.line_item import LineGraphicsItem
from footprint_editor.graphics.circle_item import CircleGraphicsItem
from footprint_editor.graphics.arc_item import ArcGraphicsItem
from footprint_editor.graphics.text_item import TextGraphicsItem
from footprint_editor.ui.dialogs.text_dialog import TextDialog
from footprint_editor.ui.dialogs.arc_dialog import ArcDialog
from footprint_editor.ui.dialogs.input_dialog import InputDialog
from footprint_editor.ui.dialogs.libraries_dialog import LibrariesManagerDialog


MODEL_ITEMS = (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem,
               ArcGraphicsItem, TextGraphicsItem)


def _rotate_point_90(x, y, cx, cy):
    dx, dy = x - cx, y - cy
    return cx - dy, cy + dx


class CommandHandler:
    def __init__(self, window):
        self.w = window
        self.clipboard = []
        self._current_mouse_pos = QPointF(0, 0)

    def on_canvas_clicked(self, x, y):
        tool = self.w.current_tool
        {
            Tool.ADD_PAD: self.add_pad,
            Tool.ADD_LINE: self.add_line_point,
            Tool.ADD_CIRCLE: self.add_circle_point,
            Tool.ADD_ARC: self.add_arc_point,
            Tool.ADD_TEXT: self.add_text_at,
        }.get(tool, lambda *_: None)(x, y)

    def on_mouse_moved(self, x, y):
        self._current_mouse_pos = QPointF(x, y)
        self.w.coords_label.setText(f"X: {x:.4f}, Y: {y:.4f}")

        tool = self.w.current_tool
        canvas = self.w.canvas
        grid = canvas.grid_size

        if tool == Tool.ADD_LINE and self.w.line_start_point:
            sx, sy = self.w.line_start_point
            canvas.set_ghost_line(sx, sy, x, y)
        elif tool == Tool.ADD_CIRCLE and self.w.circle_center_point:
            cx, cy = self.w.circle_center_point
            r = round(math.hypot(x - cx, y - cy) / grid) * grid
            canvas.set_ghost_circle(cx, cy, r)
        elif tool == Tool.ADD_ARC and self.w.arc_center_point and self.w.arc_start_point is None:
            cx, cy = self.w.arc_center_point
            canvas.set_ghost_line(cx, cy, x, y)
        else:
            canvas.clear_ghost_line()
            canvas.clear_ghost_circle()

    def add_pad(self, x, y):
        num = self.w.manager.get_next_pad_number()
        pad = Pad(number=num, shape=PadShape.CIRCLE, pad_type=PadType.STANDARD,
                  x=x, y=y, width=1.5, height=1.5, drill=0.8)
        self.w.footprint.pads.append(pad)
        self.w.manager.add_model(pad)
        self.w.canvas.set_interaction_enabled(False)
        self.w.commit_history("площадка")
        self.w.show_log(f'площадка #{num} установлена')

    def add_line_point(self, x, y):
        if self.w.line_start_point is None:
            self.w.line_start_point = (x, y)
            self.w.canvas.set_ghost_line(x, y, x, y)
            return
        sx, sy = self.w.line_start_point
        line = Line(sx, sy, x, y, width=Sizes.DEFAULT_LINE_WIDTH)
        self.w.footprint.lines.append(line)
        self.w.manager.add_model(line)
        self.w.canvas.set_interaction_enabled(False)
        self.w.line_start_point = (x, y)
        self.w.canvas.set_ghost_line(x, y, x, y)
        self.w.commit_history("линия")
        self.w.show_log('линия установлена')

    def add_circle_point(self, x, y):
        if self.w.circle_center_point is None:
            self.w.circle_center_point = (x, y)
            self.w.canvas.set_ghost_circle(x, y, 0.0)
            return
        cx, cy = self.w.circle_center_point
        grid = self.w.canvas.grid_size
        r = round(math.hypot(x - cx, y - cy) / grid) * grid
        if r > 0:
            circle = Circle(cx, cy, r, width=Sizes.DEFAULT_LINE_WIDTH)
            self.w.footprint.circles.append(circle)
            self.w.manager.add_model(circle)
            self.w.canvas.set_interaction_enabled(False)
            self.w.commit_history("окружность")
            self.w.show_log('окружность установлена')
        self.w.circle_center_point = None
        self.w.canvas.clear_ghost_circle()

    def add_arc_point(self, x, y):
        if self.w.arc_center_point is None:
            self.w.arc_center_point = (x, y)
            self.w.canvas.set_ghost_line(x, y, x, y)
            return
        if self.w.arc_start_point is None:
            self.w.arc_start_point = (x, y)
            cx, cy = self.w.arc_center_point
            self.w.canvas.set_ghost_line(cx, cy, x, y)
            self._show_arc_dialog()
            return
        self.w.arc_center_point = (x, y)
        self.w.arc_start_point = None
        self.w.canvas.set_ghost_line(x, y, x, y)

    def _show_arc_dialog(self):
        cx, cy = self.w.arc_center_point
        sx, sy = self.w.arc_start_point

        dlg = ArcDialog(self.w)
        dlg.angle_changed.connect(
            lambda a: self.w.canvas.set_ghost_arc(cx, cy, sx, sy, a)
        )
        self.w.canvas.set_ghost_arc(cx, cy, sx, sy, dlg.get_angle())

        if dlg.exec() == QDialog.Accepted:
            arc = Arc(cx=cx, cy=cy, sx=sx, sy=sy,
                      angle=dlg.get_angle(), width=Sizes.DEFAULT_LINE_WIDTH)
            self.w.footprint.arcs.append(arc)
            self.w.manager.add_model(arc)
            self.w.canvas.set_interaction_enabled(False)
            self.w.commit_history("дуга")
            self.w.show_log('дуга установлена')

        self.w.arc_center_point = None
        self.w.arc_start_point = None
        self.w.canvas.clear_ghost_arc()

    def add_text_at(self, x, y):
        self.w.text_position = (x, y)
        self.w.canvas.set_ghost_text(x, y, "", 1.0, True)

        dialog = TextDialog(self.w)
        dialog.text_changed.connect(
            lambda t: self.w.canvas.set_ghost_text(*self.w.text_position, t,
                                                    dialog.get_size(), dialog.get_visible()))
        dialog.size_changed.connect(
            lambda s: self.w.canvas.set_ghost_text(*self.w.text_position, dialog.get_text(),
                                                    s, dialog.get_visible()))
        dialog.visible_changed.connect(
            lambda v: self.w.canvas.set_ghost_text(*self.w.text_position, dialog.get_text(),
                                                    dialog.get_size(), v))

        if dialog.exec() == QDialog.Accepted:
            text_value = dialog.get_text() or "Text"
            tx, ty = self.w.text_position
            t = Text(tx, ty, text_value, dialog.get_size(), dialog.get_visible())
            self.w.footprint.texts.append(t)
            self.w.manager.add_model(t)
            self.w.canvas.set_interaction_enabled(False)
            self.w.commit_history("текст")
            self.w.show_log('текст установлен')

        self.w.text_position = None
        self.w.canvas.clear_ghost_text()

    def _selected_model_items(self):
        return [it for it in self.w.canvas.scene.selectedItems()
                if isinstance(it, MODEL_ITEMS)]

    def delete_selected(self):
        deleted_models = []
        for item in list(self.w.canvas.scene.selectedItems()):
            if not isinstance(item, MODEL_ITEMS):
                continue
            if getattr(item.model, 'locked', False):
                continue
            item.setSelected(False)
            deleted_models.append(item.model)

        for model in deleted_models:
            self._remove_from_footprint(model)
            self.w.manager.remove_model(model)

        self.w.canvas.scene.clearSelection()
        self.w.aux_bar.set_delete_enabled(False)
        self.w.right_panel.properties_panel.clear_panel()
        self.w.canvas.scene.update()
        self.w.canvas.viewport().update()

        if deleted_models:
            self.w.commit_history("удаление")
        self.w.show_log("элементы удалены")

    def _remove_from_footprint(self, model):
        fp = self.w.footprint
        for bucket in (fp.pads, fp.lines, fp.circles, fp.arcs, fp.texts):
            if model in bucket:
                bucket.remove(model)
                return

    def copy_selected(self):
        self.clipboard = []
        for item in self.w.canvas.scene.selectedItems():
            if isinstance(item, MODEL_ITEMS) and not getattr(item.model, 'locked', False):
                self.clipboard.append(copy.deepcopy(item.model))
        if self.clipboard:
            self.w.show_log("(буфер обмена) элементы скопированы")

    def paste(self):
        if not self.clipboard:
            return
        self.w.canvas.scene.clearSelection()

        cx, cy = self._clipboard_center()
        dx = self._current_mouse_pos.x() - cx
        dy = self._current_mouse_pos.y() - cy
        grid = self.w.canvas.grid_size
        dx = round(dx / grid) * grid
        dy = round(dy / grid) * grid

        for model in self.clipboard:
            new_model = copy.deepcopy(model)
            new_model.uid = new_uid()
            new_model.locked = False
            self._translate_model(new_model, dx, dy)
            self._append_model(new_model)
            item = self.w.manager.add_model(new_model)
            item.setSelected(True)

        self.w.commit_history("вставка")
        self.w.show_log("(буфер обмена) элементы установлены")

    def _clipboard_center(self):
        sx = sy = 0.0
        n = 0
        for m in self.clipboard:
            px, py = self._model_center(m)
            sx += px
            sy += py
            n += 1
        return (sx / n, sy / n) if n else (0, 0)

    def _model_center(self, m):
        if isinstance(m, Pad):
            return m.x, m.y
        if isinstance(m, Line):
            return (m.x1 + m.x2) / 2, (m.y1 + m.y2) / 2
        if isinstance(m, Circle):
            return m.x, m.y
        if isinstance(m, Arc):
            return m.cx, m.cy
        if isinstance(m, Text):
            return m.x, m.y
        return 0, 0

    def _translate_model(self, m, dx, dy):
        if isinstance(m, Pad):
            m.x += dx
            m.y += dy
        elif isinstance(m, Line):
            m.x1 += dx
            m.y1 += dy
            m.x2 += dx
            m.y2 += dy
        elif isinstance(m, Circle):
            m.x += dx
            m.y += dy
        elif isinstance(m, Arc):
            m.cx += dx
            m.cy += dy
            m.sx += dx
            m.sy += dy
        elif isinstance(m, Text):
            m.x += dx
            m.y += dy

    def _append_model(self, m):
        fp = self.w.footprint
        if isinstance(m, Pad):
            fp.pads.append(m)
        elif isinstance(m, Line):
            fp.lines.append(m)
        elif isinstance(m, Circle):
            fp.circles.append(m)
        elif isinstance(m, Arc):
            fp.arcs.append(m)
        elif isinstance(m, Text):
            fp.texts.append(m)

    def rotate_selected(self):
        items = self._selected_model_items()
        if not items:
            return

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        for item in items:
            for px, py in self._model_bounds(item.model):
                min_x = min(min_x, px)
                min_y = min(min_y, py)
                max_x = max(max_x, px)
                max_y = max(max_y, py)

        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2

        for item in items:
            self._rotate_model(item.model, cx, cy)
            if isinstance(item, PadGraphicsItem):
                item.setPos(item.model.x, item.model.y)
            item.update_geometry()

        self.w.commit_history("поворот")
        self.w.show_log("элементы повёрнуты на 90°")

    def _model_bounds(self, m):
        if isinstance(m, Pad):
            return [(m.x - m.width / 2, m.y - m.height / 2),
                    (m.x + m.width / 2, m.y + m.height / 2)]
        if isinstance(m, Line):
            return [(m.x1, m.y1), (m.x2, m.y2)]
        if isinstance(m, Circle):
            return [(m.x - m.radius, m.y - m.radius),
                    (m.x + m.radius, m.y + m.radius)]
        if isinstance(m, Arc):
            return arc_sample_points(m.cx, m.cy, m.sx, m.sy, m.angle, 16)
        if isinstance(m, Text):
            return [(m.x, m.y)]
        return []

    def _rotate_model(self, m, cx, cy):
        if isinstance(m, Pad):
            m.x, m.y = _rotate_point_90(m.x, m.y, cx, cy)
            if m.shape in (PadShape.RECT, PadShape.OVAL):
                m.width, m.height = m.height, m.width
        elif isinstance(m, Line):
            m.x1, m.y1 = _rotate_point_90(m.x1, m.y1, cx, cy)
            m.x2, m.y2 = _rotate_point_90(m.x2, m.y2, cx, cy)
        elif isinstance(m, Circle):
            m.x, m.y = _rotate_point_90(m.x, m.y, cx, cy)
        elif isinstance(m, Arc):
            m.cx, m.cy = _rotate_point_90(m.cx, m.cy, cx, cy)
            m.sx, m.sy = _rotate_point_90(m.sx, m.sy, cx, cy)
        elif isinstance(m, Text):
            m.x, m.y = _rotate_point_90(m.x, m.y, cx, cy)

    def ensure_reference_and_value(self):
        fp = self.w.footprint
        has_ref = any(t.text_type == TextType.REFERENCE for t in fp.texts)
        has_val = any(t.text_type == TextType.VALUE for t in fp.texts)
        if not has_ref:
            ref = Text(0, 0, fp.reference, 1.0, True, TextType.REFERENCE, locked=True)
            fp.texts.append(ref)
            self.w.manager.add_model(ref)
        if not has_val:
            val = Text(0, 1, fp.value, 1.0, True, TextType.VALUE, locked=True)
            fp.texts.append(val)
            self.w.manager.add_model(val)

    def new_module(self):
        dlg = InputDialog(self.w, title="Новый корпус", label="Имя корпуса:")
        if dlg.exec() != QDialog.Accepted:
            return
        name = dlg.get_text().strip()
        if not name:
            return

        self.w.stash_current_module()
        self.w.load_footprint(Footprint(name=name), mark_unsaved=False)
        if self.w.current_library_path:
            try:
                self._replace_module_in_library(self.w.current_library_path, name)
                self.w.reload_current_library()
                self.w.show_log(f"Создан корпус: {name}")
            except Exception as e:
                self.w.show_log(f"Ошибка сохранения: {e}")
        else:
            self.w.show_log(f"Создан корпус: {name}")

    def open_module_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self.w, "Открыть корпус", "",
            "KiCad Module (*.mod);;All Files (*)"
        )
        if not path:
            return
        try:
            footprints = parse_kicad_mod(path)
            if not footprints:
                QMessageBox.warning(self.w, "Пусто", "В файле нет модулей.")
                return
            self.w.stash_current_module()
            self.w.load_footprint(copy.deepcopy(footprints[0]))
        except Exception as e:
            QMessageBox.critical(self.w, "Ошибка", f"Не удалось открыть файл: {e}")

    def save_current(self):
        if not self.w.current_library_path:
            path, _ = QFileDialog.getSaveFileName(
                self.w, "Сохранить модуль", "",
                "KiCad Module (*.mod);;All Files (*)"
            )
            if not path:
                return
            if not path.lower().endswith('.mod'):
                path += '.mod'
            self.w.export_to_kicad(path)
            self.w.unsaved_modules.pop(self.w.current_module_name, None)
            self.w.mark_saved()
            self.w.show_log(f"Модуль сохранён: {Path(path).name}")
            return

        try:
            self._replace_module_in_library(self.w.current_library_path, self.w.current_module_name)
            self.w.reload_current_library()
            self.w.unsaved_modules.pop(self.w.current_module_name, None)
            self.w.mark_saved()
            self.w.show_log(f"Модуль сохранён: {self.w.current_module_name}")
        except Exception as e:
            QMessageBox.critical(self.w, "Ошибка", f"Не удалось сохранить: {e}")

    def _replace_module_in_library(self, path, module_name):
        content = Path(path).read_text(encoding='utf-8', errors='ignore')
        pattern = re.compile(
            r'\$MODULE\s+' + re.escape(module_name) + r'\b.*?\$EndMODULE[^\n]*\n',
            re.DOTALL
        )
        content = pattern.sub('', content)
        module_text = self.w.build_kicad_module_text()
        end_marker = "$EndLIBRARY"
        if end_marker in content:
            idx = content.rfind(end_marker)
            content = content[:idx] + module_text + "\n" + end_marker + "\n"
        else:
            content = content.rstrip() + "\n" + module_text + "\n" + end_marker + "\n"
        Path(path).write_text(content, encoding='utf-8')

    def add_library(self):
        path, _ = QFileDialog.getOpenFileName(
            self.w, "Добавить библиотеку KiCad", "",
            "KiCad Library (*.mod);;All Files (*)"
        )
        if not path:
            return
        if path in self.w.library_paths:
            QMessageBox.information(self.w, "Информация", "Эта библиотека уже добавлена.")
            return
        self.w.library_paths.append(path)
        self.w.save_library_paths()
        self.w.refresh_library_list()
        self.w.show_log(f"Библиотека добавлена: {Path(path).name}")

    def open_library(self):
        path, _ = QFileDialog.getOpenFileName(
            self.w, "Открыть библиотеку KiCad", "",
            "KiCad Library (*.mod);;All Files (*)"
        )
        if path:
            if path not in self.w.library_paths:
                self.w.library_paths.append(path)
                self.w.save_library_paths()
                self.w.refresh_library_list()
            self.select_library(path)

    def create_library(self):
        path, _ = QFileDialog.getSaveFileName(
            self.w, "Создать библиотеку", "",
            "KiCad Library (*.mod);;All Files (*)"
        )
        if not path:
            return
        if not path.lower().endswith('.mod'):
            path += '.mod'
        Path(path).write_text(
            "PCBNEW-LibModule-V1\n# encoding utf-8\n$INDEX\n$EndINDEX\n$EndLIBRARY\n",
            encoding='utf-8'
        )
        if path not in self.w.library_paths:
            self.w.library_paths.append(path)
            self.w.save_library_paths()
            self.w.refresh_library_list()
        self.select_library(path)
        self.w.show_log(f"Библиотека создана: {Path(path).name}")

    def manage_libraries(self):
        dlg = LibrariesManagerDialog(self.w.library_paths, self.w)
        if dlg.exec() != QDialog.Accepted:
            return
        new_paths = dlg.get_library_paths()
        if new_paths == self.w.library_paths:
            return
        self.w.library_paths = new_paths
        if self.w.current_library_path not in self.w.library_paths:
            self.w.current_library_path = None
            self.w.library_panel.set_modules([])
        self.w.save_library_paths()
        self.w.refresh_library_list()

    def select_library(self, path):
        if path not in self.w.library_modules:
            try:
                footprints = parse_kicad_mod(path)
                self.w.library_modules[path] = {fp.name: fp for fp in footprints}
            except Exception as e:
                self.w.show_log(f"Ошибка загрузки библиотеки: {e}")
                return
        self.w.current_library_path = path
        names = list(self.w.library_modules[path].keys())
        self.w.library_panel.set_modules(names)
        self.w.refresh_module_list_display()
        self.w._update_window_title()
        self.w.show_log(f"Библиотека: {Path(path).name}")

    def select_module(self, name):
        if name == self.w.current_module_name:
            return
        self.w.stash_current_module()

        if name in self.w.unsaved_modules:
            self.w.load_footprint(self.w.unsaved_modules[name], mark_unsaved=True)
            return

        if self.w.current_library_path and self.w.current_library_path in self.w.library_modules:
            module = self.w.library_modules[self.w.current_library_path].get(name)
            if module:
                self.w.load_footprint(copy.deepcopy(module))

    def reload_current_library(self):
        if not self.w.current_library_path:
            return
        try:
            footprints = parse_kicad_mod(self.w.current_library_path)
            self.w.library_modules[self.w.current_library_path] = {fp.name: fp for fp in footprints}
            names = list(self.w.library_modules[self.w.current_library_path].keys())
            self.w.library_panel.set_modules(names)
            self.w.refresh_module_list_display()
        except Exception as e:
            self.w.show_log(f"Ошибка перезагрузки: {e}")