from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import QRectF, Qt
from footprint_editor.models import PadShape

class PadGraphicsItem(QGraphicsItem):
    def __init__(self, pad, parent=None):
        super().__init__(parent)
        self.pad = pad
        self.pad.graphics_item = self 
        self.setPos(0, 0)
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        self.pen = QPen(QColor(220, 200, 50), 1.5)
        self.pen.setCosmetic(True)
        self.brush = QBrush(Qt.BrushStyle.NoBrush)

    def boundingRect(self):
        w = self.pad.width
        h = self.pad.height
        return QRectF(self.pad.x - w / 2, self.pad.y - h / 2, w, h)

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        
        w = self.pad.width
        h = self.pad.height
        rect = QRectF(self.pad.x - w / 2, self.pad.y - h / 2, w, h)
        
        if self.pad.shape == PadShape.CIRCLE:
            painter.drawEllipse(rect)
        elif self.pad.shape == PadShape.RECT:
            painter.drawRect(rect)
        elif self.pad.shape == PadShape.OVAL:
            painter.drawRoundedRect(rect, w / 2, h / 2)

    def update_geometry(self):
        self.prepareGeometryChange()
        self.update()