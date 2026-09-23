from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF, Signal, QTimer
from PySide6.QtGui import QPen, QColor, QWheelEvent, QMouseEvent, QPainter
from constants import VK_W, VK_A, VK_S, VK_D, PAN_KEYS

class FootprintCanvas(QGraphicsView):
    zoom_changed = Signal(float)
    canvas_clicked = Signal(float, float)
    finish_drawing = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(-500, -500, 1000, 1000)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        
        self.grid_size = 1.27
        self.grid_color = QColor(80, 80, 80)
        self.background_color = QColor(30, 30, 30)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(self.background_color)
        
        self.base_scale = 50.0
        self.scale(self.base_scale, self.base_scale)
        
        self.zoom_steps = [0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
        self.zoom_index = self.zoom_steps.index(1.0)
        self.zoom_level = 1.0
        
        self.pressed_keys = set()
        self.pan_speed_px = 7.5
        self.pan_timer = QTimer(self)
        self.pan_timer.setInterval(16)
        self.pan_timer.timeout.connect(self._pan_step)
        
        self._scroll_acc_px_x = 0.0
        self._scroll_acc_px_y = 0.0

        self._snap_pos = None

    def set_grid_size(self, size_mm):
        self.grid_size = size_mm
        self.viewport().update()

    def snap_to_grid(self, x, y):
        snapped_x = round(x / self.grid_size) * self.grid_size
        snapped_y = round(y / self.grid_size) * self.grid_size
        return QPointF(snapped_x, snapped_y)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        scale_factor = self.transform().m11()
        cell_px = self.grid_size * scale_factor
        
        if cell_px < 2.0:
            return

        left = int(rect.left() // self.grid_size) * self.grid_size
        right = int(rect.right() // self.grid_size) * self.grid_size
        top = int(rect.top() // self.grid_size) * self.grid_size
        bottom = int(rect.bottom() // self.grid_size) * self.grid_size
        
        draw_step = self.grid_size
        max_points_per_axis = 150
        
        if (right - left) / draw_step > max_points_per_axis:
            factor = 2
            while (right - left) / (draw_step * factor) > max_points_per_axis: factor *= 2
            draw_step = self.grid_size * factor
        if (bottom - top) / draw_step > max_points_per_axis:
            factor = 2
            while (bottom - top) / (draw_step * factor) > max_points_per_axis: factor *= 2
            draw_step = self.grid_size * factor

        pen = QPen(self.grid_color, 0)
        painter.setPen(pen)
        
        x = left
        while x <= right:
            y = top
            while y <= bottom:
                painter.drawPoint(QPointF(x, y))
                y += draw_step
            x += draw_step

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        scale = self.transform().m11()
        cross_size = 8.0 / scale

        if self._snap_pos:
            pen = QPen(QColor(255, 255, 255, 150), 0)
            pen.setCosmetic(True)
            painter.setPen(pen)
            x, y = self._snap_pos.x(), self._snap_pos.y()
            painter.drawLine(QPointF(x - cross_size, y), QPointF(x + cross_size, y))
            painter.drawLine(QPointF(x, y - cross_size), QPointF(x, y + cross_size))

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            if self.zoom_index < len(self.zoom_steps) - 1: self.zoom_index += 1
        else:
            if self.zoom_index > 0: self.zoom_index -= 1
                
        new_zoom = self.zoom_steps[self.zoom_index]
        factor = (self.base_scale * new_zoom) / self.transform().m11()
        self.scale(factor, factor)
        self.zoom_level = new_zoom
        self.zoom_changed.emit(self.zoom_level)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            snapped_pos = self.snap_to_grid(scene_pos.x(), scene_pos.y())
            self.canvas_clicked.emit(snapped_pos.x(), snapped_pos.y())
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.finish_drawing.emit()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        scene_pos = self.mapToScene(event.position().toPoint())
        snapped_pos = self.snap_to_grid(scene_pos.x(), scene_pos.y())
        self._snap_pos = QPointF(snapped_pos.x(), snapped_pos.y())
        self.viewport().update()
        super().mouseMoveEvent(event)

    def _pan_step(self):
        dx_dir = 0
        dy_dir = 0
        if VK_W in self.pressed_keys: dy_dir -= 1
        if VK_S in self.pressed_keys: dy_dir += 1
        if VK_A in self.pressed_keys: dx_dir -= 1
        if VK_D in self.pressed_keys: dx_dir += 1
            
        if dx_dir == 0 and dy_dir == 0: return
            
        self._scroll_acc_px_x += dx_dir * self.pan_speed_px
        self._scroll_acc_px_y += dy_dir * self.pan_speed_px
        
        dx_px_int = int(self._scroll_acc_px_x)
        dy_px_int = int(self._scroll_acc_px_y)
        
        self._scroll_acc_px_x -= dx_px_int
        self._scroll_acc_px_y -= dy_px_int
        
        if dx_px_int != 0 or dy_px_int != 0:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + dx_px_int)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + dy_px_int)