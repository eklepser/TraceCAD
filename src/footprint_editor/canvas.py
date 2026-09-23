from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer
from PySide6.QtGui import QPen, QColor, QWheelEvent, QMouseEvent, QPainter, QKeyEvent
from constants import VK_W, VK_A, VK_S, VK_D, PAN_KEYS

class FootprintCanvas(QGraphicsView):
    zoom_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(-500, -500, 1000, 1000)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.grid_size = 1.27
        self.grid_color = QColor(80, 80, 80)
        self.background_color = QColor(30, 30, 30)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setBackgroundBrush(self.background_color)
        
        self.base_scale = 50.0
        self.scale(self.base_scale, self.base_scale)
        
        self.zoom_steps = [0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
        self.zoom_index = self.zoom_steps.index(1.0)
        self.zoom_level = 1.0
        
        self.pressed_keys = set()
        self.pan_speed_mm = 0.05
        self.pan_timer = QTimer(self)
        self.pan_timer.setInterval(16)
        self.pan_timer.timeout.connect(self._pan_step)

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
        max_points_per_axis = 300
        width = right - left
        height = bottom - top
        
        if width > 0 and width / draw_step > max_points_per_axis:
            factor = 2
            while width / (draw_step * factor) > max_points_per_axis:
                factor *= 2
            draw_step = self.grid_size * factor
            
        if height > 0 and height / draw_step > max_points_per_axis:
            factor = 2
            while height / (draw_step * factor) > max_points_per_axis:
                factor *= 2
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

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            if self.zoom_index < len(self.zoom_steps) - 1:
                self.zoom_index += 1
        else:
            if self.zoom_index > 0:
                self.zoom_index -= 1
                
        new_zoom = self.zoom_steps[self.zoom_index]
        new_real_scale = self.base_scale * new_zoom
        current_real_scale = self.transform().m11()
        factor = new_real_scale / current_real_scale
        self.scale(factor, factor)
        self.zoom_level = new_zoom
        self.zoom_changed.emit(self.zoom_level)

    def mousePressEvent(self, event: QMouseEvent):
        self.setFocus()
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        vk = event.nativeVirtualKey()
        if vk in PAN_KEYS:
            self.pressed_keys.add(vk)
            if not self.pan_timer.isActive():
                self.pan_timer.start()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        vk = event.nativeVirtualKey()
        if vk in PAN_KEYS:
            self.pressed_keys.discard(vk)
            if not self.pressed_keys:
                self.pan_timer.stop()
        else:
            super().keyReleaseEvent(event)

    def _pan_step(self):
        dx_mm = 0
        dy_mm = 0
        if VK_W in self.pressed_keys:
            dy_mm -= self.pan_speed_mm
        if VK_S in self.pressed_keys:
            dy_mm += self.pan_speed_mm
        if VK_A in self.pressed_keys:
            dx_mm -= self.pan_speed_mm
        if VK_D in self.pressed_keys:
            dx_mm += self.pan_speed_mm
            
        if dx_mm == 0 and dy_mm == 0:
            return
            
        scale_factor = self.transform().m11()
        dx_px = int(dx_mm * scale_factor)
        dy_px = int(dy_mm * scale_factor)
        
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + dx_px)
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + dy_px)