import copy
from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from footprint_editor.core.models import Footprint, Text, TextType
from kicad.mod_importer import parse_kicad_mod
from footprint_editor.ui.dialogs.input_dialog import InputDialog


class ModuleFilesMixin:
    def ensure_reference_and_value(self):
        fp = self.w.footprint
        has_ref = any(t.text_type == TextType.REFERENCE for t in fp.texts)
        has_val = any(t.text_type == TextType.VALUE for t in fp.texts)
        if not has_ref:
            ref = Text(x=0, y=0, text=fp.reference, size=1.0, visible=True, text_type=TextType.REFERENCE, locked=True)
            fp.texts.append(ref)
            self.w.manager.add_model(ref)
        if not has_val:
            val = Text(x=0, y=1, text=fp.value, size=1.0, visible=True, text_type=TextType.VALUE, locked=True)
            fp.texts.append(val)
            self.w.manager.add_model(val)

    def new_module(self):
        name = self.w.get_next_module_name()
        dlg = InputDialog(self.w, title="Новый корпус", label="Имя корпуса:", initial=name)
        if dlg.exec() != QDialog.Accepted:
            return
        name = dlg.get_text().strip()
        if not name:
            return

        self.w.stash_current_module()

        new_fp = Footprint(name=name, reference=name, value="VAL**")
        self.w.load_footprint(new_fp, mark_unsaved=False)

        for t in self.w.footprint.texts:
            if t.text_type == TextType.REFERENCE:
                t.text = name
                if t.graphics_item:
                    t.graphics_item.prepareGeometryChange()
                    t.graphics_item.update()
                break

        if self.w.current_library_path:
            try:
                self._write_module_to_library(self.w.current_library_path, name, self.w.footprint)
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