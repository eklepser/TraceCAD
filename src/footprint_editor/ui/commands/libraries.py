from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from footprint_editor.kicad.importer import parse_kicad_mod
from footprint_editor.ui.dialogs.libraries_dialog import LibrariesManagerDialog


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
                self.w.load_footprint(__import__('copy').deepcopy(module))

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