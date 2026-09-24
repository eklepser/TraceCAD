from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QFont, QFontMetrics
from PySide6.QtCore import QRectF, QPointF, Qt

class TextGraphicsItem(QGraphicsItem):
    def __init__(self, text_model, canvas, parent=None):
        super().__init__(parent)
        self.text_model = text_model
        self.canvas = canvas
        self.text_model.graphics_item = self
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        self._drag_start_mouse = None
        self._is_drag_leader = False
        self._group_drag_start = {}

    def boundingRect(self):
        font = QFont()
        font.setPointSizeF(self.text_model.size * 2.83)
        metrics = QFontMetrics(font)
        rect = metrics.boundingRect(self.text_model.text)
        return QRectF(self.text_model.x, self.text_model.y - rect.height(), rect.width(), rect.height()).adjusted(-0.5, -0.5, 0.5, 0.5)

    def paint(self, painter, option, widget):
        font = QFont()
        font.setPointSizeF(self.text_model.size * 2.83)
        painter.setFont(font)
        
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QColor(0, 150, 255))
        else:
            if self.text_model.visible:
                painter.setPen(QColor(200, 200, 200))
            else:
                painter.setPen(QColor(200, 200, 200, 50))
            
        painter.drawText(QPointF(self.text_model.x, self.text_model.y), self.text_model.text)

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
        self.update()