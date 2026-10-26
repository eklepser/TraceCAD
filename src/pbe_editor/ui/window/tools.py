from PySide6.QtWidgets import QGraphicsItem, QGraphicsView

from pbe_editor.ui.panels.drawing_tool_bar import BoardTool
from pbe_editor.graphics.module_item import BoardModuleGraphicsItem
from pbe_editor.graphics.board_line_item import (
    BoardLineGraphicsItem, BoardCircleGraphicsItem, BoardArcGraphicsItem,
    BoardTextGraphicsItem,
)
from pbe_editor.graphics.ratsnest_item import RatsnestGraphicsItem


class ToolsService:
    def set_selectable_all(self, enabled):
        for item in self.canvas.scene.items():
            if isinstance(item, (BoardModuleGraphicsItem, BoardLineGraphicsItem,
                                 BoardCircleGraphicsItem, BoardArcGraphicsItem,
                                 BoardTextGraphicsItem, RatsnestGraphicsItem)):
                try:
                    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled)
                    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled)
                except RuntimeError:
                    pass

    def set_tool(self, tool):
        self.current_tool = tool
        self._line_start = None
        self._circle_center_point = None
        self._arc_center_point = None
        self._arc_start_point = None
        self._text_position = None
        self._net_start = None
        self.canvas.clear_ghost_line()
        self.canvas.clear_ghost_circle()
        self.canvas.clear_ghost_arc()
        self.canvas.clear_ghost_text()
        self.canvas.clear_highlight_pad()

        if tool in (BoardTool.SELECT, BoardTool.ADD_NET):
            self.canvas.set_show_snap(False)
        else:
            self.canvas.set_show_snap(True)

        if tool == BoardTool.SELECT:
            self.set_selectable_all(True)
            self.aux_bar.set_select_active(True)
            self.tool_bar.clear_active()
            self.canvas.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.right_panel.properties_panel.clear_panel()
        else:
            self.set_selectable_all(False)
            self.canvas.scene.clearSelection()
            self.aux_bar.set_select_active(False)
            self.tool_bar.set_active(tool)
            self.canvas.setDragMode(QGraphicsView.DragMode.NoDrag)
            if tool in (BoardTool.ADD_LINE, BoardTool.ADD_CIRCLE,
                        BoardTool.ADD_ARC, BoardTool.ADD_TEXT):
                self.right_panel.properties_panel.show_line_layer_picker(self._line_layer)
            elif tool == BoardTool.ADD_MODULE:
                self.right_panel.properties_panel.show_module_picker(self.library_modules)
            elif tool == BoardTool.ADD_NET:
                self.right_panel.properties_panel.clear_panel()
        self.show_log(f"Инструмент: {tool}")

    def exit_to_select_mode(self):
        self.set_tool(BoardTool.SELECT)
        self.canvas.scene.clearSelection()