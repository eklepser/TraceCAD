from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QDialog

from constants.board_settings import SETTINGS_KEY_BRD_LIBS
from common.ui.dialogs.libraries_dialog import LibrariesManagerDialog
from kicad.mod_importer import parse_kicad_mod
from pbe_editor.ui.panels.drawing_tool_bar import BoardTool


class LibrariesService:
    def load_library_paths(self):
        saved = self._settings.value(SETTINGS_KEY_BRD_LIBS, "", type=str)
        if saved:
            self.library_paths = [p for p in saved.split("\n") if p.strip()]

    def save_library_paths(self):
        self._settings.setValue(SETTINGS_KEY_BRD_LIBS, "\n".join(self.library_paths))
        self._settings.sync()

    def refresh_library_modules(self):
        self.library_modules = {}
        for path in self.library_paths:
            try:
                footprints = parse_kicad_mod(path)
                self.library_modules[path] = {fp.name: fp for fp in footprints}
            except Exception as e:
                self.show_log(f"Ошибка библиотеки {Path(path).name}: {e}")

    def find_footprint(self, name):
        for lib_data in self.library_modules.values():
            if name in lib_data:
                return lib_data[name]
        return None

    def add_library(self):
        path, _ = QFileDialog.getOpenFileName(self, "Добавить библиотеку .mod", "",
                                              "KiCad Library (*.mod);;All Files (*)")
        if not path or path in self.library_paths:
            return
        self.library_paths.append(path)
        self.save_library_paths()
        self.refresh_library_modules()
        if self.current_tool == BoardTool.ADD_MODULE:
            self.right_panel.properties_panel.show_module_picker(self.library_modules)
        self.show_log(f"Библиотека добавлена: {Path(path).name}")

    def manage_libraries(self):
        dlg = LibrariesManagerDialog(self.library_paths, self)
        if dlg.exec() != QDialog.Accepted:
            return
        new_paths = dlg.get_library_paths()
        if new_paths == self.library_paths:
            return
        self.library_paths = new_paths
        self.save_library_paths()
        self.refresh_library_modules()
        if self.current_tool == BoardTool.ADD_MODULE:
            self.right_panel.properties_panel.show_module_picker(self.library_modules)
        self.show_log(f"Библиотек: {len(self.library_paths)}")