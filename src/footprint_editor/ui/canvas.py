from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, Signal, QTimer
from PySide6.QtGui import QColor, QWheelEvent, QMouseEvent, QPainter
from constants import VK_W, VK_A, VK_S, VK_D, Colors, Sizes, Steps
from footprint_editor.ui import overlays


class FootprintCanvas(QGraphicsView):
    zoom_changed = Signal(float)
    canvas_clicked = Signal(float, float)
    mouse_moved = Signal(float, float)
    finish_drawing = Signal()
    content_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_view()
        self._setup_scene()
        self._setup_zoom()
        self._setup_pan()
        self._reset_ghosts()

    # ---------- setup ----------

    def _setup_view(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    def _setup_scene(self):
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(-500, -500, 1000, 1000)
        self.grid_size = float(Steps.DEFAULT_GRID)
        self.grid_color = QColor(*Colors.GRID)
        self.background_color = QColor(*Colors.BACKGROUND)
        self.setBackgroundBrush(self.background_color)

    def _setup_zoom(self):
        self.base_scale = Sizes.BASE_SCALE
        self.scale(self.base_scale, self.base_scale)
        self.zoom_steps = Steps.ZOOM
        self.zoom_index = self.zoom_steps.index(1.0)
        self.zoom_level = 1.0

    def _setup_pan(self):
        self.pressed_keys = set()
        self.pan_speed_px = Sizes.PAN_SPEED_PX
        self.pan_timer = QTimer(self)
        self.pan_timer.setInterval(Sizes.PAN_TIMER_INTERVAL)
        self.pan_timer.timeout.connect(self._pan_step)
        self._scroll_acc_x = 0.0
        self._scroll_acc_y = 0.0

    def _reset_ghosts(self):
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

    # ---------- public ----------

    def apply_theme(self):
        self.grid_color = QColor(*Colors.GRID)
        self.background_color = QColor(*Colors.BACKGROUND)
        self.setBackgroundBrush(self.background_color)
        self.viewport().update()

    def set_grid_size(self, size_mm):
        self.grid_size = size_mm
        self.viewport().update()

    def set_show_snap(self, show):
        self.show_snap = show
        self.viewport().update()

    def snap_to_grid(self, x, y):
        g = self.grid_size
        return QPointF(round(x / g) * g, round(y / g) * g)

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

    # ---------- rendering ----------

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        overlays.draw_grid(painter, rect, self)

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        cross_size = overlays.draw_axes(painter, rect, self)
        if self._snap_pos and self.show_snap:
            overlays.draw_snap_marker(painter, self._snap_pos, cross_size)
        overlays.draw_ghost_line(painter, self._ghost_line_start, self._ghost_line_end)
        overlays.draw_ghost_circle(painter, self._ghost_circle_center, self._ghost_circle_radius)
        overlays.draw_ghost_text(painter, self._ghost_text_pos, self._ghost_text_content,
                                 self._ghost_text_size, self._ghost_text_visible)

    # ---------- events ----------

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            if self.zoom_index < len(self.zoom_steps) - 1:
                self.zoom_index += 1
        elif self.zoom_index > 0:
            self.zoom_index -= 1

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
            snapped = self.snap_to_grid(scene_pos.x(), scene_pos.y())
            self.canvas_clicked.emit(snapped.x(), snapped.y())
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.finish_drawing.emit()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        scene_pos = self.mapToScene(event.position().toPoint())
        snapped = self.snap_to_grid(scene_pos.x(), scene_pos.y())
        self._snap_pos = QPointF(snapped.x(), snapped.y())
        self.mouse_moved.emit(snapped.x(), snapped.y())
        self.viewport().update()
        super().mouseMoveEvent(event)

    # ---------- pan ----------

    def _pan_step(self):
        dx = dy = 0
        if VK_W in self.pressed_keys: dy -= 1
        if VK_S in self.pressed_keys: dy += 1
        if VK_A in self.pressed_keys: dx -= 1
        if VK_D in self.pressed_keys: dx += 1
        if dx == 0 and dy == 0:
            return

        self._scroll_acc_x += dx * self.pan_speed_px
        self._scroll_acc_y += dy * self.pan_speed_px
        ix = int(self._scroll_acc_x)
        iy = int(self._scroll_acc_y)
        self._scroll_acc_x -= ix
        self._scroll_acc_y -= iy

        if ix or iy:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + ix)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + iy)