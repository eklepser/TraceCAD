from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, Signal, QTimer
from PySide6.QtGui import QPen, QColor, QWheelEvent, QMouseEvent, QPainter, QFont
from constants import VK_W, VK_A, VK_S, VK_D, PAN_KEYS, Colors, Sizes, Steps

class FootprintCanvas(QGraphicsView):
    zoom_changed = Signal(float)
    canvas_clicked = Signal(float, float)
    mouse_moved = Signal(float, float)
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
        
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        self.grid_size = float(Steps.DEFAULT_GRID)
        self.grid_color = QColor(*Colors.GRID)
        self.background_color = QColor(*Colors.BACKGROUND)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(self.background_color)
        
        self.base_scale = Sizes.BASE_SCALE
        self.scale(self.base_scale, self.base_scale)
        
        self.zoom_steps = Steps.ZOOM
        self.zoom_index = self.zoom_steps.index(1.0)
        self.zoom_level = 1.0
        
        self.pressed_keys = set()
        self.pan_speed_px = Sizes.PAN_SPEED_PX
        self.pan_timer = QTimer(self)
        self.pan_timer.setInterval(Sizes.PAN_TIMER_INTERVAL)
        self.pan_timer.timeout.connect(self._pan_step)
        
        self._scroll_acc_px_x = 0.0
        self._scroll_acc_px_y = 0.0

        self._snap_pos = None
        self.show_snap = True
        self._ghost_line_start = None
        self._ghost_line_end = None
        self._ghost_circle_center = None
        self._ghost_circle_radius = 0.0
        
        self._ghost_text_pos = None
        self._ghost_text_content = ""
        self._ghost_text_size = 1.0
        self._ghost_text_visible = True

    def set_grid_size(self, size_mm):
        self.grid_size = size_mm
        self.viewport().update()

    def snap_to_grid(self, x, y):
        return QPointF(round(x / self.grid_size) * self.grid_size, round(y / self.grid_size) * self.grid_size)

    def set_show_snap(self, show):
        self.show_snap = show
        self.viewport().update()

    def set_ghost_line(self, x1, y1, x2, y2):
        self._ghost_line_start = QPointF(x1, y1)
        self._ghost_line_end = QPointF(x2, y2)
        self.viewport().update()

    def clear_ghost_line(self):
        self._ghost_line_start = None
        self._ghost_line_end = None
        self.viewport().update()

    def set_ghost_circle(self, cx, cy, r):
        self._ghost_circle_center = QPointF(cx, cy)
        self._ghost_circle_radius = r
        self.viewport().update()

    def clear_ghost_circle(self):
        self._ghost_circle_center = None
        self._ghost_circle_radius = 0.0
        self.viewport().update()

    def set_ghost_text(self, x, y, text, size, visible):
        self._ghost_text_pos = QPointF(x, y)
        self._ghost_text_content = text
        self._ghost_text_size = size
        self._ghost_text_visible = visible
        self.viewport().update()

    def clear_ghost_text(self):
        self._ghost_text_pos = None
        self._ghost_text_content = ""
        self._ghost_text_size = 1.0
        self._ghost_text_visible = True
        self.viewport().update()

    def set_interaction_enabled(self, enabled):
        for item in self.scene.items():
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled)
        if not enabled:
            self.scene.clearSelection()

    def set_drag_mode(self, mode):
        self.setDragMode(mode)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        scale_factor = self.transform().m11()
        cell_px = self.grid_size * scale_factor
        
        if cell_px < Sizes.MIN_CELL_PX:
            return

        left = int(rect.left() // self.grid_size) * self.grid_size
        right = int(rect.right() // self.grid_size) * self.grid_size
        top = int(rect.top() // self.grid_size) * self.grid_size
        bottom = int(rect.bottom() // self.grid_size) * self.grid_size
        
        draw_step = self.grid_size
        max_points = Sizes.MAX_GRID_POINTS
        
        if (right - left) / draw_step > max_points:
            factor = 2
            while (right - left) / (draw_step * factor) > max_points: factor *= 2
            draw_step = self.grid_size * factor
        if (bottom - top) / draw_step > max_points:
            factor = 2
            while (bottom - top) / (draw_step * factor) > max_points: factor *= 2
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
        cross_size = Sizes.CROSS_SIZE / scale

        axis_pen = QPen(QColor(*Colors.AXIS), 0)
        axis_pen.setCosmetic(True)
        painter.setPen(axis_pen)
        painter.drawLine(QPointF(rect.left(), 0), QPointF(rect.right(), 0))
        painter.drawLine(QPointF(0, rect.top()), QPointF(0, rect.bottom()))

        if self._snap_pos and self.show_snap:
            pen = QPen(QColor(*Colors.SNAP_CROSS), 0)
            pen.setCosmetic(True)
            painter.setPen(pen)
            x, y = self._snap_pos.x(), self._snap_pos.y()
            painter.drawLine(QPointF(x - cross_size, y), QPointF(x + cross_size, y))
            painter.drawLine(QPointF(x, y - cross_size), QPointF(x, y + cross_size))

        if self._ghost_line_start and self._ghost_line_end:
            pen = QPen(QColor(*Colors.GHOST_LINE), 0)
            pen.setCosmetic(True)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(self._ghost_line_start, self._ghost_line_end)

        if self._ghost_circle_center and self._ghost_circle_radius > 0:
            pen = QPen(QColor(*Colors.GHOST_LINE), 0)
            pen.setCosmetic(True)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(self._ghost_circle_center, self._ghost_circle_radius, self._ghost_circle_radius)

        if self._ghost_text_pos and self._ghost_text_content:
            font = QFont()
            font.setPointSizeF(self._ghost_text_size * Sizes.TEXT_FONT_MULTIPLIER)
            painter.setFont(font)
            
            if self._ghost_text_visible:
                painter.setPen(QColor(*Colors.GHOST_TEXT))
            else:
                painter.setPen(QColor(*Colors.GHOST_TEXT).lighter(50))
            
            painter.drawText(self._ghost_text_pos, self._ghost_text_content)

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
            item = self.itemAt(event.position().toPoint())
            if item is not None and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                item.setSelected(not item.isSelected())
                return
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
        self.mouse_moved.emit(snapped_pos.x(), snapped_pos.y())
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