from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker
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
        extra = 0.2
        rect = QRectF(self.model.x1, self.model.y1, self.model.x2 - self.model.x1, self.model.y2 - self.model.y1)
        return rect.normalized().adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = QPainterPath()
        path.moveTo(self.model.x1, self.model.y1)
        path.lineTo(self.model.x2, self.model.y2)
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
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if self.is_preview:
            pen.setStyle(Qt.PenStyle.DashLine)
        
        painter.setPen(pen)
        painter.drawLine(QLineF(self.model.x1, self.model.y1, self.model.x2, self.model.y2))

    def apply_drag_delta(self, start, dx, dy):
        if getattr(self.model, 'locked', False):
            return
        self.model.x1 = start[1] + dx
        self.model.y1 = start[2] + dy
        self.model.x2 = start[3] + dx
        self.model.y2 = start[4] + dy
        self.prepareGeometryChange()
        self.update()