import copy

from pbe_editor.core.board_models import (
    BoardModule, BoardLine, BoardCircle, BoardArc, BoardText, PadNet,
    prefix_from_footprint_name,
)
from pbe_editor.graphics.module_item import BoardModuleGraphicsItem
from pbe_editor.graphics.board_line_item import (
    BoardLineGraphicsItem, BoardCircleGraphicsItem, BoardArcGraphicsItem,
    BoardTextGraphicsItem,
)
from pbe_editor.graphics.ratsnest_item import RatsnestGraphicsItem
from pbe_editor.ui.commands._shared import (
    model_center, translate_model, rotate_model_90, next_uid,
)


class EditingCommandsMixin:
    def delete_selected(self):
        deleted_modules = []
        deleted_lines = []
        deleted_circles = []
        deleted_arcs = []
        deleted_texts = []
        deleted_ratsnest = []
        for item in list(self.w.canvas.scene.selectedItems()):
            if isinstance(item, BoardModuleGraphicsItem):
                deleted_modules.append(item.module)
            elif isinstance(item, BoardLineGraphicsItem):
                deleted_lines.append(item.model)
            elif isinstance(item, BoardCircleGraphicsItem):
                deleted_circles.append(item.model)
            elif isinstance(item, BoardArcGraphicsItem):
                deleted_arcs.append(item.model)
            elif isinstance(item, BoardTextGraphicsItem):
                deleted_texts.append(item.model)
            elif isinstance(item, RatsnestGraphicsItem):
                deleted_ratsnest.append(item)

        deleted_net_codes = set()
        for r in deleted_ratsnest:
            if r.net_code > 0:
                deleted_net_codes.add(r.net_code)

        for m in deleted_modules:
            self.w.manager.remove_module(m)
            if m in self.w.board.modules:
                self.w.board.modules.remove(m)
        for l in deleted_lines:
            self.w.manager.remove_line(l)
            if l in self.w.board.lines:
                self.w.board.lines.remove(l)
        for c in deleted_circles:
            self.w.manager.remove_circle(c)
            if c in self.w.board.circles:
                self.w.board.circles.remove(c)
        for a in deleted_arcs:
            self.w.manager.remove_arc(a)
            if a in self.w.board.arcs:
                self.w.board.arcs.remove(a)
        for t in deleted_texts:
            self.w.manager.remove_text(t)
            if t in self.w.board.texts:
                self.w.board.texts.remove(t)
        for r in deleted_ratsnest:
            if r in self.w.manager.ratsnest_items:
                self.w.manager.ratsnest_items.remove(r)
            try:
                self.w.canvas.scene.removeItem(r)
            except RuntimeError:
                pass
        if deleted_net_codes:
            for module in self.w.board.modules:
                for pad_number in list(module.pad_nets.keys()):
                    if module.pad_nets[pad_number].net_code in deleted_net_codes:
                        del module.pad_nets[pad_number]

        if deleted_modules or deleted_lines or deleted_circles or deleted_arcs or deleted_texts or deleted_ratsnest:
            self.w.manager.rebuild_ratsnest()
            self.w.refresh_module_list()
            self.w.commit_snapshot()
            self.w.show_log(
                f"Удалено: {len(deleted_modules)} модулей, "
                f"{len(deleted_lines)} линий, {len(deleted_circles)} окружностей, "
                f"{len(deleted_arcs)} дуг, {len(deleted_texts)} текстов, "
                f"{len(deleted_ratsnest)} связей"
            )

    def rotate_selected(self):
        items = [it for it in self.w.canvas.scene.selectedItems()
                 if isinstance(it, (BoardModuleGraphicsItem, BoardLineGraphicsItem,
                                    BoardArcGraphicsItem))]
        if not items:
            return
        for item in items:
            if isinstance(item, BoardModuleGraphicsItem):
                rotate_model_90(item.module)
                item.setRotation(item.module.angle)
                item.prepareGeometryChange()
                item.update()
            elif isinstance(item, BoardLineGraphicsItem):
                rotate_model_90(item.model)
                item.setPos(item.model.x1, item.model.y1)
                item.prepareGeometryChange()
                item.update()
            elif isinstance(item, BoardArcGraphicsItem):
                rotate_model_90(item.model)
                item.setPos(item.model.x, item.model.y)
                item.prepareGeometryChange()
                item.update()
        self.w.manager.rebuild_ratsnest()
        self.w.commit_snapshot()
        self.w.show_log(f"Повёрнуто: {len(items)} элементов")

    def copy_selected(self):
        self._clipboard = []
        for item in self.w.canvas.scene.selectedItems():
            if isinstance(item, BoardModuleGraphicsItem):
                self._clipboard.append(copy.deepcopy(item.module))
            elif isinstance(item, BoardLineGraphicsItem):
                self._clipboard.append(copy.deepcopy(item.model))
            elif isinstance(item, BoardCircleGraphicsItem):
                self._clipboard.append(copy.deepcopy(item.model))
            elif isinstance(item, BoardArcGraphicsItem):
                self._clipboard.append(copy.deepcopy(item.model))
            elif isinstance(item, BoardTextGraphicsItem):
                self._clipboard.append(copy.deepcopy(item.model))
        if self._clipboard:
            self.w.show_log(f"Скопировано: {len(self._clipboard)} элементов")

    def _clipboard_center(self):
        if not self._clipboard:
            return 0.0, 0.0
        sx = sy = 0.0
        n = 0
        for m in self._clipboard:
            px, py = model_center(m)
            sx += px
            sy += py
            n += 1
        return (sx / n, sy / n) if n else (0.0, 0.0)

    def paste(self):
        if not self._clipboard:
            return
        self.w.canvas.scene.clearSelection()
        cx, cy = self._clipboard_center()
        dx = self._current_mouse_pos.x() - cx
        dy = self._current_mouse_pos.y() - cy
        grid = self.w.canvas.grid_size
        dx = round(dx / grid) * grid
        dy = round(dy / grid) * grid

        for model in self._clipboard:
            new_model = copy.deepcopy(model)
            if isinstance(new_model, BoardModule):
                new_model.uid = next_uid(self.w.board.modules)
                new_model.reference = self.w.board.auto_reference(
                    prefix_from_footprint_name(new_model.footprint.name))
                translate_model(new_model, dx, dy)
                self.w.board.modules.append(new_model)
                item = self.w.manager.add_module(new_model)
            elif isinstance(new_model, BoardLine):
                new_model.uid = next_uid(self.w.board.lines)
                translate_model(new_model, dx, dy)
                self.w.board.lines.append(new_model)
                item = self.w.manager.add_line(new_model)
            elif isinstance(new_model, BoardCircle):
                new_model.uid = next_uid(self.w.board.circles)
                translate_model(new_model, dx, dy)
                self.w.board.circles.append(new_model)
                item = self.w.manager.add_circle(new_model)
            elif isinstance(new_model, BoardArc):
                new_model.uid = next_uid(self.w.board.arcs)
                translate_model(new_model, dx, dy)
                self.w.board.arcs.append(new_model)
                item = self.w.manager.add_arc(new_model)
            elif isinstance(new_model, BoardText):
                new_model.uid = next_uid(self.w.board.texts)
                translate_model(new_model, dx, dy)
                self.w.board.texts.append(new_model)
                item = self.w.manager.add_text(new_model)
            else:
                continue
            item.setSelected(True)

        self.w.refresh_module_list()
        self.w.manager.rebuild_ratsnest()
        self.w.commit_snapshot()
        self.w.show_log(f"Вставлено: {len(self._clipboard)} элементов")