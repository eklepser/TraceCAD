from pbe_editor.graphics.module_item import BoardModuleGraphicsItem
from pbe_editor.graphics.board_line_item import (
    BoardLineGraphicsItem, BoardCircleGraphicsItem, BoardArcGraphicsItem,
    BoardTextGraphicsItem,
)
from pbe_editor.graphics.ratsnest_item import RatsnestGraphicsItem
from pbe_editor.ui.panels.drawing_tool_bar import BoardTool


class SelectionCommandsMixin:
    def on_selection_changed(self):
        if self.w.current_tool != BoardTool.SELECT:
            return
        items = self.w.canvas.scene.selectedItems()
        self.w.aux_bar.set_delete_enabled(len(items) > 0)
        if len(items) == 1:
            item = items[0]
            if isinstance(item, (BoardModuleGraphicsItem, BoardLineGraphicsItem,
                                 BoardCircleGraphicsItem, BoardArcGraphicsItem,
                                 BoardTextGraphicsItem, RatsnestGraphicsItem)):
                self.w.right_panel.properties_panel.show_object(item)
                return
        self.w.right_panel.properties_panel.clear_panel()

    def on_apply_properties(self):
        self.w.manager.rebuild_ratsnest()
        self.w.refresh_module_list()
        self.w.commit_snapshot()

    def on_line_layer_selected(self, layer):
        self.w._line_layer = layer
        self.w.show_log(f"Слой рисования: {layer}")

    def on_module_picked_from_panel(self, fp):
        self.w._selected_footprint = fp
        self.w.show_log(f"Выбран модуль для вставки: {fp.name}")

    def on_module_list_clicked(self, list_item):
        idx = self.w.module_list.row(list_item)
        if 0 <= idx < len(self.w.board.modules):
            module = self.w.board.modules[idx]
            item = self.w.manager.items.get(module.uid)
            if item is not None:
                self.w.canvas.scene.clearSelection()
                item.setSelected(True)
                self.w.right_panel.properties_panel.show_object(item)
                self.w.canvas.centerOn(item)