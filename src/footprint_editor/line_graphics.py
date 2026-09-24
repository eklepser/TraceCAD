from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker
from PySide6.QtCore import QLineF, QRectF, QPointF, Qt

class LineGraphicsItem(QGraphicsItem):
    def __init__(self, line_model, canvas, is_preview=False, parent=None):
        super().__init__(parent)
        self.line_model = line_model
        self.canvas = canvas
        if not is_preview:
            self.line_model.graphics_item = self
            
        self.is_preview = is_preview
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        self.pen = QPen(QColor(200, 200, 200), line_model.width)
        self.pen.setCosmetic(False)
        self.pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        self._drag_start_mouse = None
        self._drag_start_coords = None

    def boundingRect(self):
        extra = 0.2
        rect = QRectF(self.line_model.x1, self.line_model.y1, self.line_model.x2 - self.line_model.x1, self.line_model.y2 - self.line_model.y1)
        return rect.normalized().adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = QPainterPath()
        path.moveTo(self.line_model.x1, self.line_model.y1)
        path.lineTo(self.line_model.x2, self.line_model.y2)
        stroker = QPainterPathStroker()
        stroker.setWidth(0.3)
        return stroker.createStroke(path)

    def paint(self, painter, option, widget):
        if option.state & QStyle.StateFlag.State_Selected:
            self.pen.setColor(QColor(0, 150, 255))
        else:
            self.pen.setColor(QColor(200, 200, 200))
            
        if self.is_preview:
            self.pen.setWidthF(0.05)
            self.pen.setStyle(Qt.PenStyle.DashLine)
        else:
            self.pen.setWidthF(self.line_model.width)
            self.pen.setStyle(Qt.PenStyle.SolidLine)
            
        painter.setPen(self.pen)
        painter.drawLine(QLineF(self.line_model.x1, self.line_model.y1, self.line_model.x2, self.line_model.y2))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and (self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable) and not self.is_preview:
            self._drag_start_mouse = self.mapToScene(event.pos())
            self._drag_start_coords = (self.line_model.x1, self.line_model.y1, self.line_model.x2, self.line_model.y2)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_mouse is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            current_mouse = self.mapToScene(event.pos())
            delta = current_mouse - self._drag_start_mouse
            grid = self.canvas.grid_size
            snapped_dx = round(delta.x() / grid) * grid
            snapped_dy = round(delta.y() / grid) * grid
            self.line_model.x1 = self._drag_start_coords[0] + snapped_dx
            self.line_model.y1 = self._drag_start_coords[1] + snapped_dy
            self.line_model.x2 = self._drag_start_coords[2] + snapped_dx
            self.line_model.y2 = self._drag_start_coords[3] + snapped_dy
            self.prepareGeometryChange()
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_mouse = None
        self._drag_start_coords = None
        super().mouseReleaseEvent(event)

    def update_geometry(self):
        self.prepareGeometryChange()
        self.update()