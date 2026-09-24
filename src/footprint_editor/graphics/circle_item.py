from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker
from PySide6.QtCore import QRectF, QPointF, Qt
from footprint_editor.graphics.base import BaseGraphicsItem
from constants import Colors

class CircleGraphicsItem(BaseGraphicsItem):
    def __init__(self, circle_model, canvas, is_preview=False, parent=None):
        super().__init__(circle_model, canvas, parent)
        self.is_preview = is_preview

    def boundingRect(self):
        r = self.model.radius
        extra = 0.2
        return QRectF(self.model.x - r, self.model.y - r, 2*r, 2*r).adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(QPointF(self.model.x, self.model.y), self.model.radius, self.model.radius)
        stroker = QPainterPathStroker()
        stroker.setWidth(0.3)
        return stroker.createStroke(path)

    def paint(self, painter, option, widget):
        if option.state & QStyle.StateFlag.State_Selected:
            color = QColor(*Colors.SELECTED)
        else:
            color = QColor(*Colors.TEXT_VISIBLE)
        
        pen = QPen(color, self.model.width if not self.is_preview else 0.05)
        pen.setCosmetic(False)
        if self.is_preview:
            pen.setStyle(Qt.PenStyle.DashLine)
        
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(self.model.x, self.model.y), self.model.radius, self.model.radius)

    def apply_drag_delta(self, start, dx, dy):
        self.model.x = start[1] + dx
        self.model.y = start[2] + dy
        self.prepareGeometryChange()
        self.update()