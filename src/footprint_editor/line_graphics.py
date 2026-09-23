from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import QLineF, QRectF

class LineGraphicsItem(QGraphicsItem):
    def __init__(self, line_model, is_preview=False, parent=None):
        super().__init__(parent)
        self.line_model = line_model
        if not is_preview:
            self.line_model.graphics_item = self
            
        self.is_preview = is_preview
        
        self.pen = QPen(QColor(200, 200, 200), 2.0)
        self.pen.setCosmetic(True)
        
        if is_preview:
            self.pen.setStyle(Qt.PenStyle.DashLine)
            self.pen.setColor(QColor(100, 200, 100))

    def update_end_point(self, x2, y2):
        self.prepareGeometryChange()
        self.line_model.x2 = x2
        self.line_model.y2 = y2
        self.update()

    def boundingRect(self):
        extra = self.pen.width() + 2
        x1, y1, x2, y2 = self.line_model.x1, self.line_model.y1, self.line_model.x2, self.line_model.y2
        rect = QRectF(x1, y1, x2 - x1, y2 - y1)
        return rect.normalized().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget):
        if self.is_preview:
            self.pen.setWidthF(2.0)
        else:
            self.pen.setWidthF(self.line_model.width * 10) 
            
        painter.setPen(self.pen)
        painter.drawLine(QLineF(self.line_model.x1, self.line_model.y1, self.line_model.x2, self.line_model.y2))

    def update_geometry(self):
        self.prepareGeometryChange()
        self.update()