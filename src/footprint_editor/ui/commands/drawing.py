import math
from PySide6.QtWidgets import QDialog
from constants import Tool, Sizes
from footprint_editor.core.models import Pad, PadShape, PadType, Line, Circle, Arc, Text
from common.ui.dialogs.text_dialog import TextDialog
from common.ui.dialogs.arc_dialog import ArcDialog


class DrawingCommandsMixin:
    def on_canvas_clicked(self, x, y):
        tool = self.w.current_tool
        {
            Tool.ADD_PAD: self.add_pad,
            Tool.ADD_LINE: self.add_line_point,
            Tool.ADD_CIRCLE: self.add_circle_point,
            Tool.ADD_ARC: self.add_arc_point,
            Tool.ADD_TEXT: self.add_text_at,
        }.get(tool, lambda *_: None)(x, y)

    def on_mouse_moved(self, x, y):
        from PySide6.QtCore import QPointF
        self._current_mouse_pos = QPointF(x, y)
        self.w.coords_label.setText(f"X: {x:.4f}, Y: {y:.4f}")

        tool = self.w.current_tool
        canvas = self.w.canvas
        grid = canvas.grid_size

        if tool == Tool.ADD_LINE and self.w.line_start_point:
            sx, sy = self.w.line_start_point
            canvas.set_ghost_line(sx, sy, x, y)
        elif tool == Tool.ADD_CIRCLE and self.w.circle_center_point:
            cx, cy = self.w.circle_center_point
            r = round(math.hypot(x - cx, y - cy) / grid) * grid
            canvas.set_ghost_circle(cx, cy, r)
        elif tool == Tool.ADD_ARC and self.w.arc_center_point and self.w.arc_start_point is None:
            cx, cy = self.w.arc_center_point
            canvas.set_ghost_line(cx, cy, x, y)
        else:
            canvas.clear_ghost_line()
            canvas.clear_ghost_circle()

    def add_pad(self, x, y):
        num = self.w.manager.get_next_pad_number()
        pad = Pad(number=num, shape=PadShape.CIRCLE, pad_type=PadType.STANDARD,
                  x=x, y=y, width=1.5, height=1.5, drill=0.8)
        self.w.footprint.pads.append(pad)
        self.w.manager.add_model(pad)
        self.w.canvas.set_interaction_enabled(False)
        self.w.commit_history()
        self.w.show_log(f'площадка #{num} установлена')

    def add_line_point(self, x, y):
        if self.w.line_start_point is None:
            self.w.line_start_point = (x, y)
            self.w.canvas.set_ghost_line(x, y, x, y)
            return
        sx, sy = self.w.line_start_point
        line = Line(sx, sy, x, y, width=Sizes.DEFAULT_LINE_WIDTH)
        self.w.footprint.lines.append(line)
        self.w.manager.add_model(line)
        self.w.canvas.set_interaction_enabled(False)
        self.w.line_start_point = (x, y)
        self.w.canvas.set_ghost_line(x, y, x, y)
        self.w.commit_history()
        self.w.show_log('линия установлена')

    def add_circle_point(self, x, y):
        if self.w.circle_center_point is None:
            self.w.circle_center_point = (x, y)
            self.w.canvas.set_ghost_circle(x, y, 0.0)
            return
        cx, cy = self.w.circle_center_point
        grid = self.w.canvas.grid_size
        r = round(math.hypot(x - cx, y - cy) / grid) * grid
        if r > 0:
            circle = Circle(cx, cy, r, width=Sizes.DEFAULT_LINE_WIDTH)
            self.w.footprint.circles.append(circle)
            self.w.manager.add_model(circle)
            self.w.canvas.set_interaction_enabled(False)
            self.w.commit_history()
            self.w.show_log('окружность установлена')
        self.w.circle_center_point = None
        self.w.canvas.clear_ghost_circle()

    def add_arc_point(self, x, y):
        if self.w.arc_center_point is None:
            self.w.arc_center_point = (x, y)
            self.w.canvas.set_ghost_line(x, y, x, y)
            return
        if self.w.arc_start_point is None:
            self.w.arc_start_point = (x, y)
            cx, cy = self.w.arc_center_point
            self.w.canvas.set_ghost_line(cx, cy, x, y)
            self._show_arc_dialog()
            return
        self.w.arc_center_point = (x, y)
        self.w.arc_start_point = None
        self.w.canvas.set_ghost_line(x, y, x, y)

    def _show_arc_dialog(self):
        cx, cy = self.w.arc_center_point
        sx, sy = self.w.arc_start_point

        dlg = ArcDialog(self.w)
        dlg.angle_changed.connect(
            lambda a: self.w.canvas.set_ghost_arc(cx, cy, sx, sy, a)
        )
        self.w.canvas.set_ghost_arc(cx, cy, sx, sy, dlg.get_angle())

        if dlg.exec() == QDialog.Accepted:
            arc = Arc(cx=cx, cy=cy, sx=sx, sy=sy,
                      angle=dlg.get_angle(), width=Sizes.DEFAULT_LINE_WIDTH)
            self.w.footprint.arcs.append(arc)
            self.w.manager.add_model(arc)
            self.w.canvas.set_interaction_enabled(False)
            self.w.commit_history()
            self.w.show_log('дуга установлена')

        self.w.arc_center_point = None
        self.w.arc_start_point = None
        self.w.canvas.clear_ghost_arc()

    def add_text_at(self, x, y):
        self.w.text_position = (x, y)
        self.w.canvas.set_ghost_text(x, y, "", 1.0, True)

        dialog = TextDialog(self.w)
        dialog.text_changed.connect(
            lambda t: self.w.canvas.set_ghost_text(*self.w.text_position, t,
                                                    dialog.get_size(), dialog.get_visible()))
        dialog.size_changed.connect(
            lambda s: self.w.canvas.set_ghost_text(*self.w.text_position, dialog.get_text(),
                                                    s, dialog.get_visible()))
        dialog.visible_changed.connect(
            lambda v: self.w.canvas.set_ghost_text(*self.w.text_position, dialog.get_text(),
                                                    dialog.get_size(), v))

        if dialog.exec() == QDialog.Accepted:
            text_value = dialog.get_text() or "Text"
            tx, ty = self.w.text_position
            t = Text(tx, ty, text_value, dialog.get_size(), dialog.get_visible())
            self.w.footprint.texts.append(t)
            self.w.manager.add_model(t)
            self.w.canvas.set_interaction_enabled(False)
            self.w.commit_history()
            self.w.show_log('текст установлен')

        self.w.text_position = None
        self.w.canvas.clear_ghost_text()