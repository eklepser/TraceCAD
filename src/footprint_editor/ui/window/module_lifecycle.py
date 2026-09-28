from datetime import datetime
from pathlib import Path

from footprint_editor.kicad.exporter import build_kicad_module_text


class ModuleLifecycleService:
    def _populate_scene(self, module):
        for bucket in (module.pads, module.lines, module.circles, module.arcs, module.texts):
            for model in bucket:
                self.manager.add_model(model)

    def load_footprint(self, module, mark_unsaved=None):
        self.footprint = module
        self.manager.footprint = self.footprint
        self.canvas.scene.clear()
        self.manager.items.clear()

        self._populate_scene(module)
        self.commands.ensure_reference_and_value()

        self.current_module_name = module.name
        if mark_unsaved is None:
            mark_unsaved = module.name in self.unsaved_modules
        self._modified = mark_unsaved
        self._update_window_title()
        self.refresh_module_list_display()
        self.history.reset(self.footprint)
        self._update_history_buttons()
        self.show_log(f"Загружен модуль: {module.name}")

    def stash_current_module(self):
        if self._modified:
            self.unsaved_modules[self.current_module_name] = self.footprint

    def mark_saved(self):
        self._modified = False
        self.refresh_module_list_display()

    def refresh_module_list_display(self):
        self.library_panel.mark_unsaved(set(self.unsaved_modules.keys()))

    def build_kicad_module_text(self):
        return build_kicad_module_text(self.footprint)

    def export_to_kicad(self, filepath):
        lines = [
            f"PCBNEW-LibModule-V1  {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            "# encoding utf-8",
            "$INDEX", self.footprint.name, "$EndINDEX",
            build_kicad_module_text(self.footprint),
            "$EndLIBRARY",
        ]
        Path(filepath).write_text("\n".join(lines), encoding='utf-8')

    def _update_window_title(self):
        if self.current_library_path:
            lib_name = Path(self.current_library_path).stem
            title = f"TraceCAD: {lib_name}/{self.footprint.name}"
        else:
            title = f"TraceCAD: {self.footprint.name}"
        self.setWindowTitle(title)