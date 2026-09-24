from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt

class BaseGraphicsItem(QGraphicsItem):
    def __init__(self, model, canvas, parent=None):
        super().__init__(parent)
        self.model = model
        self.canvas = canvas
        self.model.graphics_item = self
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        self._drag_start_mouse = None
        self._is_drag_leader = False
        self._group_drag_start = {}

    def _collect_selected_items(self):
        self._group_drag_start = {}
        for item in self.scene().selectedItems():
            cls_name = type(item).__name__
            if cls_name == 'PadGraphicsItem':
                self._group_drag_start[item] = ('pad', item.model.x, item.model.y)
            elif cls_name == 'LineGraphicsItem':
                self._group_drag_start[item] = ('line', item.model.x1, item.model.y1, item.model.x2, item.model.y2)
            elif cls_name == 'CircleGraphicsItem':
                self._group_drag_start[item] = ('circle', item.model.x, item.model.y)
            elif cls_name == 'TextGraphicsItem':
                self._group_drag_start[item] = ('text', item.model.x, item.model.y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isSelected():
            self._drag_start_mouse = self.mapToScene(event.pos())
            self._is_drag_leader = True
            self._collect_selected_items()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_drag_leader and (event.buttons() & Qt.MouseButton.LeftButton):
            current_mouse = self.mapToScene(event.pos())
            delta = current_mouse - self._drag_start_mouse
            grid = self.canvas.grid_size
            snapped_dx = round(delta.x() / grid) * grid
            snapped_dy = round(delta.y() / grid) * grid
            
            for item, start in self._group_drag_start.items():
                item.apply_drag_delta(start, snapped_dx, snapped_dy)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_drag_leader = False
        self._group_drag_start = {}
        super().mouseReleaseEvent(event)

    def update_geometry(self):
        self.prepareGeometryChange()
        self.update()

    def apply_drag_delta(self, start, dx, dy):
        raise NotImplementedError