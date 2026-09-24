from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import QRectF, QPointF, Qt
from footprint_editor.models import PadShape

class PadGraphicsItem(QGraphicsItem):
    def __init__(self, pad, canvas, parent=None):
        super().__init__(parent)
        self.pad = pad
        self.canvas = canvas
        self.pad.graphics_item = self 
        
        self.setPos(pad.x, pad.y)
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        self.pen = QPen(QColor(220, 200, 50), 0.05)
        self.pen.setCosmetic(False)
        self.brush = QBrush(Qt.BrushStyle.NoBrush)
        
        self._drag_start_pos = None
        self._drag_start_mouse = None

    def boundingRect(self):
        w = self.pad.width
        h = self.pad.height
        return QRectF(-w / 2, -h / 2, w, h)

    def paint(self, painter, option, widget):
        if option.state & QStyle.StateFlag.State_Selected:
            self.pen.setColor(QColor(0, 150, 255))
        else:
            self.pen.setColor(QColor(220, 200, 50))
            
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        
        w = self.pad.width
        h = self.pad.height
        rect = QRectF(-w / 2, -h / 2, w, h)
        
        if self.pad.shape == PadShape.CIRCLE:
            painter.drawEllipse(rect)
        elif self.pad.shape == PadShape.RECT:
            painter.drawRect(rect)
        elif self.pad.shape == PadShape.OVAL:
            painter.drawRoundedRect(rect, w / 2, h / 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and (self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable):
            self._drag_start_pos = QPointF(self.pos())
            self._drag_start_mouse = self.mapToScene(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_pos is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            current_mouse = self.mapToScene(event.pos())
            delta = current_mouse - self._drag_start_mouse
            grid = self.canvas.grid_size
            snapped_dx = round(delta.x() / grid) * grid
            snapped_dy = round(delta.y() / grid) * grid
            new_pos = self._drag_start_pos + QPointF(snapped_dx, snapped_dy)
            self.setPos(new_pos)
            self.pad.x = new_pos.x()
            self.pad.y = new_pos.y()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        self._drag_start_mouse = None
        super().mouseReleaseEvent(event)

    def update_geometry(self):
        self.prepareGeometryChange()
        self.setPos(self.pad.x, self.pad.y)
        self.update()