import copy
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QDialog, QGraphicsItem

from constants.board_settings import DEFAULT_LINE_WIDTH
from common.ui.dialogs.arc_dialog import ArcDialog
from common.ui.dialogs.text_dialog import TextDialog
from pbe_editor.core.board_models import (
    BoardModule, BoardLine, BoardCircle, BoardArc, BoardText, PadNet,
    prefix_from_footprint_name,
)
from pbe_editor.ui.panels.drawing_tool_bar import BoardTool


class DrawingCommandsMixin:
    def on_canvas_right_clicked(self):
        self.w.exit_to_select_mode()

    def on_canvas_clicked(self, x, y):
        tool = self.w.current_tool
        if tool == BoardTool.ADD_LINE:
            self._add_line_click(x, y)
        elif tool == BoardTool.ADD_CIRCLE:
            self._add_circle_click(x, y)
        elif tool == BoardTool.ADD_ARC:
            self._add_arc_click(x, y)
        elif tool == BoardTool.ADD_TEXT:
            self._add_text_click(x, y)
        elif tool == BoardTool.ADD_MODULE:
            self._add_module_click(x, y)
        elif tool == BoardTool.ADD_NET:
            self._add_net_click(x, y)

    def on_mouse_moved(self, x, y):
        self._current_mouse_pos = QPointF(x, y)
        self.w.coords_label.setText(f"X: {x:.4f}, Y: {y:.4f}")
        tool = self.w.current_tool

        if tool == BoardTool.ADD_NET:
            tol = self.w.canvas.grid_size * 1.5
            hit = self.w.board.find_pad_at(x, y, tol)
            if hit is not None:
                module, pad_number = hit
                pos = module.get_pad_absolute(pad_number)
                pad = None
                for p in module.footprint.pads:
                    if p.number == pad_number:
                        pad = p
                        break
                if pos and pad:
                    radius = max(pad.width, pad.height) * 0.8
                    self.w.canvas.set_highlight_pad(QPointF(*pos), radius)
                else:
                    self.w.canvas.clear_highlight_pad()
            else:
                self.w.canvas.clear_highlight_pad()

            if self.w._net_start:
                sx, sy = self.w._net_start[2]
                self.w.canvas.set_ghost_line(sx, sy, x, y)
            return

        self.w.canvas.clear_highlight_pad()

        if tool == BoardTool.ADD_LINE and self.w._line_start:
            sx, sy = self.w._line_start
            self.w.canvas.set_ghost_line(sx, sy, x, y)
        elif tool == BoardTool.ADD_CIRCLE and self.w._circle_center_point:
            cx, cy = self.w._circle_center_point
            g = self.w.canvas.grid_size
            r = round(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / g) * g
            self.w.canvas.set_ghost_circle(cx, cy, r)
        elif tool == BoardTool.ADD_ARC and self.w._arc_center_point and self.w._arc_start_point is None:
            cx, cy = self.w._arc_center_point
            self.w.canvas.set_ghost_line(cx, cy, x, y)
        elif tool == BoardTool.ADD_TEXT and self.w._text_position:
            tx, ty = self.w._text_position
            self.w.canvas.set_ghost_text(tx, ty, "", 1.0, True)
        else:
            self.w.canvas.clear_ghost_line()
            self.w.canvas.clear_ghost_circle()

    def _add_graphic_item(self, model, kind):
        if kind == "line":
            self.w.board.lines.append(model)
            item = self.w.manager.add_line(model)
        elif kind == "circle":
            self.w.board.circles.append(model)
            item = self.w.manager.add_circle(model)
        elif kind == "arc":
            self.w.board.arcs.append(model)
            item = self.w.manager.add_arc(model)
        elif kind == "text":
            self.w.board.texts.append(model)
            item = self.w.manager.add_text(model)
        else:
            return None
        if self.w.current_tool != BoardTool.SELECT:
            try:
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            except RuntimeError:
                pass
        return item

    def _add_line_click(self, x, y):
        if self.w._line_start is None:
            self.w._line_start = (x, y)
            self.w.canvas.set_ghost_line(x, y, x, y)
            return
        sx, sy = self.w._line_start
        if abs(sx - x) < 1e-6 and abs(sy - y) < 1e-6:
            return
        line = BoardLine(
            x1=sx, y1=sy, x2=x, y2=y,
            layer=self.w._line_layer, width=DEFAULT_LINE_WIDTH,
            uid=self.w.next_line_uid(),
        )
        self._add_graphic_item(line, "line")
        self.w._line_start = (x, y)
        self.w.canvas.set_ghost_line(x, y, x, y)
        self.w.commit_snapshot()
        self.w.show_log(f"Линия {self.w._line_layer}: добавлена")

    def _add_circle_click(self, x, y):
        g = self.w.canvas.grid_size
        if self.w._circle_center_point is None:
            self.w._circle_center_point = (x, y)
            self.w.canvas.set_ghost_circle(x, y, 0.0)
            return
        cx, cy = self.w._circle_center_point
        r = round(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / g) * g
        if r > 0:
            circle = BoardCircle(
                x=cx, y=cy, radius=r,
                layer=self.w._line_layer, width=DEFAULT_LINE_WIDTH,
                uid=self.w.next_circle_uid(),
            )
            self._add_graphic_item(circle, "circle")
            self.w.commit_snapshot()
            self.w.show_log(f"Окружность {self.w._line_layer}: добавлена")
        self.w._circle_center_point = None
        self.w.canvas.clear_ghost_circle()

    def _add_arc_click(self, x, y):
        if self.w._arc_center_point is None:
            self.w._arc_center_point = (x, y)
            self.w.canvas.set_ghost_line(x, y, x, y)
            return
        if self.w._arc_start_point is None:
            self.w._arc_start_point = (x, y)
            cx, cy = self.w._arc_center_point
            self.w.canvas.set_ghost_line(cx, cy, x, y)
            self._show_arc_dialog()
            return
        self.w._arc_center_point = (x, y)
        self.w._arc_start_point = None
        self.w.canvas.set_ghost_line(x, y, x, y)

    def _show_arc_dialog(self):
        cx, cy = self.w._arc_center_point
        sx, sy = self.w._arc_start_point

        dlg = ArcDialog(self.w)
        dlg.angle_changed.connect(
            lambda a: self.w.canvas.set_ghost_arc(cx, cy, sx, sy, a)
        )
        self.w.canvas.set_ghost_arc(cx, cy, sx, sy, dlg.get_angle())

        if dlg.exec() == QDialog.Accepted:
            arc = BoardArc(
                x=cx, y=cy, sx=sx, sy=sy,
                angle=dlg.get_angle(),
                layer=self.w._line_layer, width=DEFAULT_LINE_WIDTH,
                uid=self.w.next_arc_uid(),
            )
            self._add_graphic_item(arc, "arc")
            self.w.commit_snapshot()
            self.w.show_log(f"Дуга {self.w._line_layer}: добавлена")

        self.w._arc_center_point = None
        self.w._arc_start_point = None
        self.w.canvas.clear_ghost_arc()

    def _add_text_click(self, x, y):
        self.w._text_position = (x, y)
        self.w.canvas.set_ghost_text(x, y, "", 1.0, True)

        dialog = TextDialog(self.w)
        dialog.text_changed.connect(
            lambda t: self.w.canvas.set_ghost_text(
                self.w._text_position[0], self.w._text_position[1],
                t, dialog.get_size(), dialog.get_visible()))
        dialog.size_changed.connect(
            lambda s: self.w.canvas.set_ghost_text(
                self.w._text_position[0], self.w._text_position[1],
                dialog.get_text(), s, dialog.get_visible()))
        dialog.visible_changed.connect(
            lambda v: self.w.canvas.set_ghost_text(
                self.w._text_position[0], self.w._text_position[1],
                dialog.get_text(), dialog.get_size(), v))

        if dialog.exec() == QDialog.Accepted:
            text_value = dialog.get_text() or "Text"
            tx, ty = self.w._text_position
            text = BoardText(
                x=tx, y=ty, text=text_value,
                size=dialog.get_size(), visible=dialog.get_visible(),
                layer=self.w._line_layer, uid=self.w.next_text_uid(),
            )
            self._add_graphic_item(text, "text")
            self.w.commit_snapshot()
            self.w.show_log(f"Текст {self.w._line_layer}: добавлен")

        self.w._text_position = None
        self.w.canvas.clear_ghost_text()

    def _add_module_click(self, x, y):
        fp = self.w._selected_footprint
        if fp is None:
            self.w.show_log("Сначала выберите модуль справа")
            return
        prefix = prefix_from_footprint_name(fp.name)
        module = BoardModule(
            footprint=copy.deepcopy(fp),
            reference=self.w.board.auto_reference(prefix),
            value=fp.value,
            x=x, y=y, angle=0.0, layer="F.Cu",
            uid=self.w.next_module_uid(),
        )
        self.w.board.modules.append(module)
        item = self.w.manager.add_module(module)
        if self.w.current_tool != BoardTool.SELECT:
            try:
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            except RuntimeError:
                pass
        self.w.manager.rebuild_ratsnest()
        self.w.refresh_module_list()
        self.w.commit_snapshot()
        self.w.show_log(f"Модуль {module.reference} добавлен")

    def _add_net_click(self, x, y):
        tol = self.w.canvas.grid_size * 1.5
        hit = self.w.board.find_pad_at(x, y, tol)
        if hit is None:
            self.w.show_log("Не найден вывод в точке")
            return
        module, pad_number = hit
        pos = module.get_pad_absolute(pad_number)
        if self.w._net_start is None:
            self.w._net_start = (module, pad_number, pos)
            self.w.canvas.set_ghost_line(pos[0], pos[1], pos[0], pos[1])
            return
        m1, p1, pos1 = self.w._net_start
        if (m1, p1) == (module, pad_number):
            self.w._net_start = None
            self.w.canvas.clear_ghost_line()
            return
        pn1 = m1.pad_nets.get(p1)
        pn2 = module.pad_nets.get(pad_number)
        net_name = None
        if pn1 and pn1.net_name:
            net_name = pn1.net_name
        elif pn2 and pn2.net_name:
            net_name = pn2.net_name
        if net_name is None:
            net_name = f"Net-{m1.reference}-{p1}-{module.reference}-{pad_number}"
        net = self.w.board.get_or_create_net(net_name)
        for m, p in ((m1, p1), (module, pad_number)):
            m.pad_nets[p] = PadNet(pad_number=p, net_code=net.code, net_name=net.name)
        self.w._net_start = None
        self.w.canvas.clear_ghost_line()
        self.w.manager.rebuild_ratsnest()
        self.w.commit_snapshot()
        self.w.show_log(f"Связь {net_name}: {m1.reference}.{p1} ↔ {module.reference}.{pad_number}")