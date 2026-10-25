from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath
from PySide6.QtCore import QRectF, QPointF, Qt

from constants import Colors, Sizes
from footprint_editor.core.arc_geometry import arc_sample_points
from footprint_editor.core.models import PadShape, PadType
from footprint_editor.graphics.text_path import build_text_path


STANDARD_COLOR = (180, 160, 80)
SMD_COLOR = (220, 90, 90)
CONN_COLOR = (235, 150, 60)


class BoardModuleGraphicsItem(QGraphicsItem):
    def __init__(self, module, canvas, parent=None):
        super().__init__(parent)
        self.module = module
        self.canvas = canvas
        self.module.graphics_item = self

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setPos(module.x, module.y)
        self.setRotation(module.angle)
        self.setZValue(10)

        self._drag_start_scene = None
        self._drag_start_pos = None
        self._drag_moved = False
        self._is_drag_leader = False
        self._group_drag_start = {}

    def boundingRect(self):
        fp = self.module.footprint
        xs = []
        ys = []
        for pad in fp.pads:
            xs.append(pad.x - pad.width / 2)
            xs.append(pad.x + pad.width / 2)
            ys.append(pad.y - pad.height / 2)
            ys.append(pad.y + pad.height / 2)
        for line in fp.lines:
            xs.extend([line.x, line.x2])
            ys.extend([line.y, line.y2])
        for circle in fp.circles:
            xs.extend([circle.x - circle.radius, circle.x + circle.radius])
            ys.extend([circle.y - circle.radius, circle.y + circle.radius])
        for arc in fp.arcs:
            for px, py in arc_sample_points(arc.x, arc.y, arc.sx, arc.sy, arc.angle, 32):
                xs.append(px)
                ys.append(py)

        if not xs:
            return QRectF(-10, -10, 20, 20)

        left = min(xs)
        right = max(xs)
        top = min(ys)
        bottom = max(ys)
        extra = 1.0
        return QRectF(left - extra, top - extra,
                      right - left + 2 * extra, bottom - top + 2 * extra)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def _pad_color(self, pad, selected):
        if selected:
            return QColor(*Colors.SELECTED)
        if pad.pad_type == PadType.SMD:
            return QColor(*SMD_COLOR)
        if pad.pad_type == PadType.CONN:
            return QColor(*CONN_COLOR)
        return QColor(*STANDARD_COLOR)

    def paint(self, painter, option, widget):
        fp = self.module.footprint
        selected = bool(option.state & QStyle.StateFlag.State_Selected)

        if selected:
            outline_color = QColor(*Colors.SELECTED)
        else:
            outline_color = QColor(200, 200, 200)

        pen = QPen(outline_color, 0.15)
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for line in fp.lines:
            painter.drawLine(QPointF(line.x, line.y), QPointF(line.x2, line.y2))

        for circle in fp.circles:
            painter.drawEllipse(QPointF(circle.x, circle.y), circle.radius, circle.radius)

        for arc in fp.arcs:
            pts = arc_sample_points(arc.x, arc.y, arc.sx, arc.sy, arc.angle, 32)
            if len(pts) >= 2:
                path = QPainterPath()
                path.moveTo(pts[0][0], pts[0][1])
                for px, py in pts[1:]:
                    path.lineTo(px, py)
                painter.drawPath(path)

        for pad in fp.pads:
            pad_color = self._pad_color(pad, selected)
            w = pad.width
            h = pad.height
            rect = QRectF(pad.x - w / 2, pad.y - h / 2, w, h)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(pad_color)

            if pad.shape == PadShape.RECT:
                painter.drawRect(rect)
            elif pad.shape == PadShape.OVAL:
                painter.drawRoundedRect(rect, w / 2, h / 2)
            else:
                painter.drawEllipse(rect)

            drill = pad.drill or 0.0
            if drill > 0:
                painter.setBrush(QColor(*Colors.BACKGROUND))
                painter.drawEllipse(QRectF(pad.x - drill / 2, pad.y - drill / 2,
                                           drill, drill))

            if pad.number:
                target_h = min(pad.width, pad.height) * Sizes.PAD_NUMBER_FONT_RATIO
                text_path = build_text_path(pad.number, target_h, bold=True, center=True)
                painter.save()
                painter.translate(pad.x, pad.y)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(*Colors.PAD_NUMBER))
                painter.drawPath(text_path)
                painter.restore()

        if self.module.reference:
            ref_path = build_text_path(self.module.reference, 1.5, bold=True, center=True)
            if not ref_path.isEmpty():
                bounds = self.boundingRect()
                ref_y = bounds.top() + 0.5
                painter.save()
                painter.translate(0.0, ref_y)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(150, 220, 150))
                painter.drawPath(ref_path)
                painter.restore()

    def _collect_selected_modules(self):
        self._group_drag_start = {}
        scene = self.scene()
        if scene is None:
            return
        for item in scene.selectedItems():
            if isinstance(item, BoardModuleGraphicsItem):
                self._group_drag_start[item] = (item.pos().x(), item.pos().y())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            if self.isSelected():
                self._drag_start_scene = self.mapToScene(event.pos())
                self._drag_start_pos = QPointF(self.pos())
                self._drag_moved = False
                self._is_drag_leader = True
                self._collect_selected_modules()
                event.accept()
                return
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_drag_leader and self._drag_start_scene is not None and \
                (event.buttons() & Qt.MouseButton.LeftButton):
            current = self.mapToScene(event.pos())
            delta = current - self._drag_start_scene
            grid = self.canvas.grid_size
            snapped_dx = round(delta.x() / grid) * grid
            snapped_dy = round(delta.y() / grid) * grid

            if snapped_dx != 0 or snapped_dy != 0:
                self._drag_moved = True

            for item, (sx, sy) in self._group_drag_start.items():
                new_x = sx + snapped_dx
                new_y = sy + snapped_dy
                item.setPos(new_x, new_y)
                item.module.x = new_x
                item.module.y = new_y

            if hasattr(self.canvas, 'ratsnest_update_requested'):
                self.canvas.ratsnest_update_requested.emit()

            self.canvas.viewport().update()
            event.accept()
        else:
            self._drag_start_scene = None
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        was_dragging = self._drag_moved
        self._drag_start_scene = None
        self._drag_start_pos = None
        self._drag_moved = False
        self._is_drag_leader = False
        self._group_drag_start = {}
        super().mouseReleaseEvent(event)
        if was_dragging and hasattr(self.canvas, 'ratsnest_update_requested'):
            self.canvas.ratsnest_update_requested.emit()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)