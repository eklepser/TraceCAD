from PySide6.QtWidgets import QGraphicsView
from constants import Tool


class ToolsService:
    def _on_drawing_tool(self, tool):
        self._set_tool(tool)
        self.aux_bar.set_select_active(False)

    def _on_right_tool(self, tool):
        self._set_tool(tool)
        if tool != Tool.SELECT:
            self.tool_bar.set_active(tool)

    def _set_tool(self, tool):
        self.current_tool = tool

        if tool == Tool.SELECT:
            self.aux_bar.set_select_active(True)
            self.tool_bar.clear_active()
        else:
            self.aux_bar.set_select_active(False)
            self.tool_bar.set_active(tool)

        self._reset_drawing_state()

        if tool == Tool.SELECT:
            self.canvas.set_show_snap(False)
            self.canvas.set_interaction_enabled(True)
            self.canvas.set_drag_mode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.canvas.set_show_snap(True)
            self.canvas.set_interaction_enabled(False)
            self.canvas.set_drag_mode(QGraphicsView.DragMode.NoDrag)

        self.show_log(f"Инструмент: {tool}")

    def _reset_drawing_state(self):
        self.line_start_point = None
        self.circle_center_point = None
        self.arc_center_point = None
        self.arc_start_point = None
        self.text_position = None
        self.canvas.clear_ghost_line()
        self.canvas.clear_ghost_circle()
        self.canvas.clear_ghost_arc()
        self.canvas.clear_ghost_text()

    def finish_drawing(self):
        self._reset_drawing_state()