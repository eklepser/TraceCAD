from pathlib import Path
from constants import (
    SETTINGS_KEY_LAST_LIB, SETTINGS_KEY_LAST_MODULE,
    SETTINGS_KEY_LIBS, SETTINGS_KEY_GRID_MODE,
)
from footprint_editor.kicad.importer import parse_kicad_mod


class SessionService:
    def _load_library_paths(self):
        saved = self._settings.value(SETTINGS_KEY_LIBS, "", type=str)
        if saved:
            self.library_paths = [p for p in saved.split("\n") if p.strip()]

    def _save_library_paths(self):
        self._settings.setValue(SETTINGS_KEY_LIBS, "\n".join(self.library_paths))
        self._settings.sync()

    def _load_grid_mode(self):
        mode = self._settings.value(SETTINGS_KEY_GRID_MODE, "1x", type=str)
        return mode if mode in self._grid_series() else "1x"

    def _persist_grid_mode(self, mode):
        self._settings.setValue(SETTINGS_KEY_GRID_MODE, mode)
        self._settings.sync()

    def _restore_last_session(self):
        last_lib = self._settings.value(SETTINGS_KEY_LAST_LIB, "", type=str)
        last_mod = self._settings.value(SETTINGS_KEY_LAST_MODULE, "", type=str)
        if not last_lib or last_lib not in self.library_paths:
            return
        try:
            if last_lib not in self.library_modules:
                footprints = parse_kicad_mod(last_lib)
                self.library_modules[last_lib] = {fp.name: fp for fp in footprints}
            self.current_library_path = last_lib
            names = list(self.library_modules[last_lib].keys())
            self.library_panel.set_modules(names)
            self.refresh_module_list_display()

            if last_mod and last_mod in self.library_modules[last_lib]:
                import copy as _copy
                module = _copy.deepcopy(self.library_modules[last_lib][last_mod])
                self.load_footprint(module)
                self.show_log(f"Восстановлен: {Path(last_lib).stem}/{last_mod}")
            else:
                self._update_window_title()
        except Exception:
            pass

    def _save_last_session(self):
        if self.current_library_path:
            self._settings.setValue(SETTINGS_KEY_LAST_LIB, self.current_library_path)
            self._settings.setValue(SETTINGS_KEY_LAST_MODULE, self.current_module_name)
        else:
            self._settings.setValue(SETTINGS_KEY_LAST_LIB, "")
            self._settings.setValue(SETTINGS_KEY_LAST_MODULE, "")
        self._settings.sync()

    def closeEvent(self, event):
        self._save_last_session()
        super().closeEvent(event)