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
        
        self.pen = QPen(QColor(220, 200, 50), 0.1)
        self.pen.setCosmetic(False)
        self.brush = QBrush(Qt.BrushStyle.NoBrush)
        
        self._drag_start_mouse = None
        self._is_drag_leader = False
        self._group_drag_start = {}

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
        if event.button() == Qt.MouseButton.LeftButton and self.isSelected():
            self._drag_start_mouse = self.mapToScene(event.pos())
            self._is_drag_leader = True
            self._group_drag_start = {}
            for item in self.scene().selectedItems():
                cls_name = type(item).__name__
                if cls_name == 'PadGraphicsItem':
                    self._group_drag_start[item] = ('pad', item.pad.x, item.pad.y)
                elif cls_name == 'LineGraphicsItem':
                    self._group_drag_start[item] = ('line', item.line_model.x1, item.line_model.y1, item.line_model.x2, item.line_model.y2)
                elif cls_name == 'CircleGraphicsItem':
                    self._group_drag_start[item] = ('circle', item.circle_model.x, item.circle_model.y)
                elif cls_name == 'TextGraphicsItem':
                    self._group_drag_start[item] = ('text', item.text_model.x, item.text_model.y)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_drag_leader and (event.buttons() & Qt.MouseButton.LeftButton):
            current_mouse = self.mapToScene(event.pos())
            delta = current_mouse - self._drag_start_mouse
            grid = self.canvas.grid_size
            snapped_dx = round(delta.x() / grid) * grid
            snapped_dy = round(delta.y() / grid) * grid
            
            for item, start in self._group_drag_start.items():
                if start[0] == 'pad':
                    item.pad.x = start[1] + snapped_dx
                    item.pad.y = start[2] + snapped_dy
                    item.setPos(item.pad.x, item.pad.y)
                elif start[0] == 'line':
                    item.line_model.x1 = start[1] + snapped_dx
                    item.line_model.y1 = start[2] + snapped_dy
                    item.line_model.x2 = start[3] + snapped_dx
                    item.line_model.y2 = start[4] + snapped_dy
                    item.prepareGeometryChange()
                    item.update()
                elif start[0] == 'circle':
                    item.circle_model.x = start[1] + snapped_dx
                    item.circle_model.y = start[2] + snapped_dy
                    item.prepareGeometryChange()
                    item.update()
                elif start[0] == 'text':
                    item.text_model.x = start[1] + snapped_dx
                    item.text_model.y = start[2] + snapped_dy
                    item.prepareGeometryChange()
                    item.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_drag_leader = False
        self._group_drag_start = {}
        super().mouseReleaseEvent(event)

    def update_geometry(self):
        self.prepareGeometryChange()
        self.setPos(self.pad.x, self.pad.y)
        self.update()