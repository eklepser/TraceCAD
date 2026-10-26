import copy
import re
import shutil
from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from kicad.mod_importer import parse_kicad_mod
from kicad.mod_exporter import build_kicad_module_text
from common.ui.dialogs.libraries_dialog import LibrariesManagerDialog
from common.ui.dialogs.custom_question_dialog import CustomQuestionDialog
from footprint_editor.ui.dialogs.input_dialog import InputDialog


class LibrariesMixin:
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

    def save_library(self):
        if not self.w.current_library_path:
            self.save_library_as()
            return

        lib_path = self.w.current_library_path
        if not Path(lib_path).exists():
            QMessageBox.warning(
                self.w, "Ошибка",
                f"Файл библиотеки не найден:\n{lib_path}"
            )
            return

        try:
            modules_to_save = dict(self.w.unsaved_modules)
            if self.w.current_module_name:
                modules_to_save[self.w.current_module_name] = self.w.footprint

            for name, module in modules_to_save.items():
                self._write_module_to_library(lib_path, name, module)

            self.w.unsaved_modules.clear()
            self.w.mark_saved()
            self.w.reload_current_library()
            self.w.save_library_paths()
            self.w.show_log(f"Библиотека сохранена: {Path(lib_path).name}")
        except Exception as e:
            QMessageBox.critical(self.w, "Ошибка", f"Не удалось сохранить библиотеку: {e}")

    def save_library_as(self):
        src = self.w.current_library_path
        if not src:
            QMessageBox.information(
                self.w, "Информация",
                "Сначала выберите библиотеку в левой панели."
            )
            return
        if not Path(src).exists():
            QMessageBox.warning(
                self.w, "Ошибка",
                f"Исходный файл библиотеки не найден:\n{src}"
            )
            return

        suggested = str(Path(src).with_name(Path(src).stem + "_copy.mod"))
        path, _ = QFileDialog.getSaveFileName(
            self.w, "Сохранить библиотеку как", suggested,
            "KiCad Library (*.mod);;All Files (*)"
        )
        if not path:
            return
        if not path.lower().endswith('.mod'):
            path += '.mod'

        if Path(path).resolve() == Path(src).resolve():
            QMessageBox.information(
                self.w, "Информация",
                "Новый путь совпадает с текущим — ничего не меняем."
            )
            return

        if Path(path).exists():
            answer = QMessageBox.question(
                self.w, "Перезаписать?",
                f"Файл уже существует:\n{path}\n\nПерезаписать?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, path)
        except Exception as e:
            QMessageBox.critical(
                self.w, "Ошибка",
                f"Не удалось сохранить библиотеку: {e}"
            )
            return

        if path not in self.w.library_paths:
            self.w.library_paths.append(path)
            self.w.save_library_paths()
            self.w.refresh_library_list()

        try:
            footprints = parse_kicad_mod(path)
            self.w.library_modules[path] = {fp.name: fp for fp in footprints}
        except Exception as e:
            self.w.show_log(f"Библиотека скопирована, но не разобрана: {e}")
            return

        self.select_library(path)
        self.w.show_log(f"Библиотека сохранена как: {Path(path).name}")

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
        self.w.library_panel.highlight_library(path)

        self.w.refresh_module_list_display()
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

    def rename_module(self, old_name):
        dlg = InputDialog(self.w, title="Переименовать корпус", label="Новое имя:", initial=old_name)
        if dlg.exec() != QDialog.Accepted:
            return
        new_name = dlg.get_text().strip()
        if not new_name or new_name == old_name:
            return

        lib_path = self.w.current_library_path
        if not lib_path or lib_path not in self.w.library_modules:
            return

        lib_data = self.w.library_modules[lib_path]
        if new_name in lib_data:
            QMessageBox.warning(self.w, "Ошибка", "Корпус с таким именем уже существует.")
            return

        is_current = (self.w.current_module_name == old_name)
        if is_current:
            self.w.footprint.name = new_name

        if old_name in self.w.unsaved_modules:
            self.w.unsaved_modules[new_name] = self.w.unsaved_modules.pop(old_name)
            self.w.unsaved_modules[new_name].name = new_name

        self._remove_module_from_library_file(lib_path, old_name)

        if is_current:
            self._write_module_to_library(lib_path, new_name, self.w.footprint)
        else:
            module = lib_data.get(old_name)
            if module:
                module.name = new_name
                self._write_module_to_library(lib_path, new_name, module)

        if old_name in lib_data:
            lib_data[new_name] = lib_data.pop(old_name)
            lib_data[new_name].name = new_name

        if is_current:
            self.w.current_module_name = new_name

        self.w.reload_current_library()
        self.w.refresh_module_list_display()

    def delete_module(self, name):
        lib_path = self.w.current_library_path
        if not lib_path or lib_path not in self.w.library_modules:
            return

        dlg = CustomQuestionDialog(
            self.w,
            title="Удаление корпуса",
            message=f"Вы уверены, что хотите удалить корпус '{name}'?"
        )
        result = dlg.exec()
        if result != CustomQuestionDialog.ResultSave:
            return

        if name in self.w.unsaved_modules:
            del self.w.unsaved_modules[name]

        self._remove_module_from_library_file(lib_path, name)

        if name in self.w.library_modules[lib_path]:
            del self.w.library_modules[lib_path][name]

        if self.w.current_module_name == name:
            if self.w.library_modules[lib_path]:
                new_name = list(self.w.library_modules[lib_path].keys())[0]
                self.select_module(new_name)
            else:
                from footprint_editor.core.models import Footprint
                self.w.load_footprint(Footprint(name="Empty"))
                self.w.current_module_name = "Empty"

        self.w.reload_current_library()
        self.w.refresh_module_list_display()
        self.w.show_log(f"Корпус удалён: {name}")

    def _write_module_to_library(self, path, module_name, module):
        content = Path(path).read_text(encoding='utf-8', errors='ignore')
        pattern = re.compile(
            r'\$MODULE\s+' + re.escape(module_name) + r'\b.*?\$EndMODULE[^\n]*\n',
            re.DOTALL
        )
        content = pattern.sub('', content)
        module_text = build_kicad_module_text(module)
        end_marker = "$EndLIBRARY"
        if end_marker in content:
            idx = content.rfind(end_marker)
            content = content[:idx] + module_text + "\n" + end_marker + "\n"
        else:
            content = content.rstrip() + "\n" + module_text + "\n" + end_marker + "\n"
        Path(path).write_text(content, encoding='utf-8')

    def _remove_module_from_library_file(self, path, module_name):
        content = Path(path).read_text(encoding='utf-8', errors='ignore')
        pattern = re.compile(
            r'\$MODULE\s+' + re.escape(module_name) + r'\b.*?\$EndMODULE[^\n]*\n',
            re.DOTALL
        )
        content = pattern.sub('', content)
        Path(path).write_text(content, encoding='utf-8')