import copy
from footprint_editor.core.models import new_uid
from footprint_editor.graphics.pad_item import PadGraphicsItem
from footprint_editor.graphics.line_item import LineGraphicsItem
from footprint_editor.graphics.circle_item import CircleGraphicsItem
from footprint_editor.graphics.arc_item import ArcGraphicsItem
from footprint_editor.graphics.text_item import TextGraphicsItem
from footprint_editor.ui.commands._shared import (
    model_center, translate_model, append_model,
    model_bounds, rotate_model, remove_from_footprint,
)


MODEL_ITEMS = (PadGraphicsItem, LineGraphicsItem, CircleGraphicsItem,
               ArcGraphicsItem, TextGraphicsItem)


class EditingCommandsMixin:
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
            remove_from_footprint(self.w.footprint, model)
            self.w.manager.remove_model(model)

        self.w.canvas.scene.clearSelection()
        self.w.aux_bar.set_delete_enabled(False)
        self.w.right_panel.properties_panel.clear_panel()
        self.w.canvas.scene.update()
        self.w.canvas.viewport().update()

        if deleted_models:
            self.w.commit_history()
        self.w.show_log("элементы удалены")

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
            translate_model(new_model, dx, dy)
            append_model(self.w.footprint, new_model)
            item = self.w.manager.add_model(new_model)
            item.setSelected(True)

        self.w.commit_history()
        self.w.show_log("(буфер обмена) элементы установлены")

    def _clipboard_center(self):
        sx = sy = 0.0
        n = 0
        for m in self.clipboard:
            px, py = model_center(m)
            sx += px
            sy += py
            n += 1
        return (sx / n, sy / n) if n else (0, 0)

    def rotate_selected(self):
        items = self._selected_model_items()
        if not items:
            return

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        for item in items:
            for px, py in model_bounds(item.model):
                min_x = min(min_x, px)
                min_y = min(min_y, py)
                max_x = max(max_x, px)
                max_y = max(max_y, py)

        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2

        for item in items:
            rotate_model(item.model, cx, cy)
            if isinstance(item, PadGraphicsItem):
                item.setPos(item.model.x, item.model.y)
            item.update_geometry()

        self.w.commit_history()
        self.w.show_log("элементы повёрнуты на 90°")