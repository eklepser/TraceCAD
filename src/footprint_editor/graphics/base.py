from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QPointF


class BaseGraphicsItem(QGraphicsItem):
    def __init__(self, model, canvas, parent=None):
        super().__init__(parent)
        self.model = model
        self.canvas = canvas
        self.model.graphics_item = self

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)

        self._drag_start_mouse = None
        self._is_drag_leader = False
        self._drag_moved = False
        self._group_drag_start = {}

        self._handle_radius = 1.0
        self._active_handle = None
        self._hover_handle = None
        self.setAcceptHoverEvents(True)

    def is_selected(self):
        return self.isSelected()

    def _collect_selected_items(self):
        self._group_drag_start = {}
        scene = self.scene()
        if scene is None:
            return
        for item in scene.selectedItems():
            cls_name = type(item).__name__
            if cls_name == 'PadGraphicsItem':
                self._group_drag_start[item] = ('pad', item.model.x, item.model.y)
            elif cls_name == 'LineGraphicsItem':
                self._group_drag_start[item] = ('line', item.model.x, item.model.y, item.model.x2, item.model.y2)
            elif cls_name == 'CircleGraphicsItem':
                self._group_drag_start[item] = ('circle', item.model.x, item.model.y)
            elif cls_name == 'ArcGraphicsItem':
                self._group_drag_start[item] = ('arc', item.model.x, item.model.y, item.model.sx, item.model.sy)
            elif cls_name == 'TextGraphicsItem':
                self._group_drag_start[item] = ('text', item.model.x, item.model.y)

    def get_handles(self):
        return []

    def update_handle_from_drag(self, handle_idx, pos):
        pass

    def _hit_test_handle(self, scene_pos):
        if not self.isSelected():
            return None
        handles = self.get_handles()
        view = self.canvas
        if not view:
            return None
        scale = view.transform().m11()
        if scale <= 0:
            return None
        radius = self._handle_radius * 3.0 / scale

        best_idx = None
        best_dist = float('inf')

        for i, pt in enumerate(handles):
            dx = scene_pos.x() - pt.x()
            dy = scene_pos.y() - pt.y()
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < radius and dist < best_dist:
                best_idx = i
                best_dist = dist

        return best_idx

    def _notify_properties_panel(self):
        if hasattr(self.canvas, 'properties_changed'):
            self.canvas.properties_changed.emit(self.model)

    def hoverMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        idx = self._hit_test_handle(scene_pos)
        if idx != self._hover_handle:
            self._hover_handle = idx
            self.update()
        if idx is not None:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.unsetCursor()
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            handle_idx = self._hit_test_handle(scene_pos)

            if handle_idx is not None:
                self._active_handle = handle_idx
                self._drag_start_mouse = scene_pos
                self._is_drag_leader = True
                self._drag_moved = False
                self._group_drag_start = {}
                self.update()
                event.accept()
                return

            super().mousePressEvent(event)
            if self.isSelected():
                if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                    self._drag_start_mouse = scene_pos
                    self._is_drag_leader = True
                    self._drag_moved = False
                    self._collect_selected_items()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_drag_leader and (event.buttons() & Qt.MouseButton.LeftButton):
            current_mouse = self.mapToScene(event.pos())

            if self._active_handle is not None:
                grid = self.canvas.grid_size
                snapped_x = round(current_mouse.x() / grid) * grid
                snapped_y = round(current_mouse.y() / grid) * grid
                self.update_handle_from_drag(self._active_handle, QPointF(snapped_x, snapped_y))
                self._drag_moved = True
                self._notify_properties_panel()
                event.accept()
                return

            delta = current_mouse - self._drag_start_mouse
            grid = self.canvas.grid_size
            snapped_dx = round(delta.x() / grid) * grid
            snapped_dy = round(delta.y() / grid) * grid

            if snapped_dx != 0 or snapped_dy != 0:
                self._drag_moved = True

            for item, start in self._group_drag_start.items():
                item.apply_drag_delta(start, snapped_dx, snapped_dy)
            self._notify_properties_panel()
            event.accept()
        else:
            self._is_drag_leader = False
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        was_dragging = self._is_drag_leader and self._drag_moved
        self._is_drag_leader = False
        self._drag_moved = False
        self._drag_start_mouse = None
        self._active_handle = None
        self._group_drag_start = {}
        self.update()
        super().mouseReleaseEvent(event)
        if was_dragging and hasattr(self.canvas, 'content_changed'):
            self.canvas.content_changed.emit()

    def update_geometry(self):
        self.prepareGeometryChange()
        self.update()

    def apply_drag_delta(self, start, dx, dy):
        raise NotImplementedError