from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, QBrush
from PySide6.QtCore import QLineF, QRectF, QPointF, Qt
from footprint_editor.graphics.base import BaseGraphicsItem
from constants import Colors


class LineGraphicsItem(BaseGraphicsItem):
    def __init__(self, line_model, canvas, is_preview=False, parent=None):
        super().__init__(line_model, canvas, parent)
        self.is_preview = is_preview
        if not is_preview:
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

    def boundingRect(self):
        extra = 1.0
        rect = QRectF(self.model.x, self.model.y,
                      self.model.x2 - self.model.x,
                      self.model.y2 - self.model.y)
        return rect.normalized().adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = QPainterPath()
        path.moveTo(self.model.x, self.model.y)
        path.lineTo(self.model.x2, self.model.y2)
        stroker = QPainterPathStroker()
        stroker.setWidth(max(0.5, self.model.width * 1.5))
        return stroker.createStroke(path)

    def get_handles(self):
        return [
            QPointF(self.model.x, self.model.y),
            QPointF(self.model.x2, self.model.y2),
        ]

    def update_handle_from_drag(self, handle_idx, pos):
        if handle_idx == 0:
            if self._point_collision(pos.x(), pos.y(), is_start=True):
                return
            self.model.x = pos.x()
            self.model.y = pos.y()
        elif handle_idx == 1:
            if self._point_collision(pos.x(), pos.y(), is_start=False):
                return
            self.model.x2 = pos.x()
            self.model.y2 = pos.y()
        self.prepareGeometryChange()
        self.update()

    def _point_collision(self, x, y, is_start):
        eps = 0.0001
        if is_start:
            return abs(self.model.x - self.model.x2) < eps and abs(self.model.y - self.model.y2) < eps
        else:
            return abs(x - self.model.x) < eps and abs(y - self.model.y) < eps

    def paint(self, painter, option, widget):
        if option.state & QStyle.StateFlag.State_Selected:
            color = QColor(*Colors.SELECTED)
        else:
            color = QColor(*Colors.TEXT_VISIBLE)

        pen = QPen(color, self.model.width if not self.is_preview else 0.05)
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if self.is_preview:
            pen.setStyle(Qt.PenStyle.DashLine)

        painter.setPen(pen)
        painter.drawLine(QLineF(self.model.x, self.model.y, self.model.x2, self.model.y2))

        if self.is_selected() and not self.is_preview:
            for i, pt in enumerate(self.get_handles()):
                is_active = (i == self._active_handle)
                is_hover = (i == self._hover_handle)

                is_colliding = False
                if is_active:
                    if i == 0:
                        is_colliding = self._point_collision(pt.x(), pt.y(), is_start=True)
                    else:
                        is_colliding = self._point_collision(pt.x(), pt.y(), is_start=False)

                if is_colliding:
                    fill = QColor(255, 0, 0)
                    border = QColor(255, 255, 255)
                    radius_px = 6.0
                elif is_active:
                    fill = QColor(0, 200, 0)
                    border = QColor(255, 255, 255)
                    radius_px = 6.0
                elif is_hover:
                    fill = QColor(255, 255, 255)
                    border = QColor(0, 150, 255)
                    radius_px = 5.0
                else:
                    fill = QColor(*Colors.SELECTED)
                    border = QColor(255, 255, 255)
                    radius_px = 4.0

                scale = self.canvas.transform().m11() if self.canvas else 1.0
                radius = radius_px / scale if scale > 0 else radius_px

                p = QPen(border, 0)
                p.setCosmetic(True)
                painter.setPen(p)
                painter.setBrush(QBrush(fill))
                painter.drawEllipse(pt, radius, radius)

    def apply_drag_delta(self, start, dx, dy):
        if getattr(self.model, 'locked', False):
            return
        self.model.x = start[1] + dx
        self.model.y = start[2] + dy
        self.model.x2 = start[3] + dx
        self.model.y2 = start[4] + dy
        self.prepareGeometryChange()
        self.update()