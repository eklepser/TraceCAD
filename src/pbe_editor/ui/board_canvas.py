from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, Signal, QTimer
from PySide6.QtGui import QColor, QWheelEvent, QMouseEvent, QPainter, QPen, QPainterPath

from constants import Colors, Sizes, Steps, VK_W, VK_A, VK_S, VK_D
from common.arc_geometry import arc_sample_points
from common.graphics.text_path import build_text_path


class BoardCanvas(QGraphicsView):
    zoom_changed = Signal(float)
    mouse_moved = Signal(float, float)
    ratsnest_update_requested = Signal()
    canvas_clicked = Signal(float, float)
    canvas_right_clicked = Signal()
    selection_changed = Signal()
    content_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._panning = False
        self._pan_start = None
        self.show_grid = True
        self.show_snap = True
        self.show_values = False
        self._highlight_pad_pos = None
        self._highlight_pad_radius = 0.0

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFrameShape(QGraphicsView.Shape.Box)
        self.setFrameShadow(QGraphicsView.Shadow.Plain)
        self.setLineWidth(1)
        self.setStyleSheet("QGraphicsView { border: 1px solid #ffffff; }")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        self.scene.selectionChanged.connect(self.selection_changed.emit)

        self.grid_size = float(Steps.DEFAULT_GRID)
        self.grid_color = QColor(*Colors.GRID)
        self.background_color = QColor(*Colors.BACKGROUND)
        self.setBackgroundBrush(self.background_color)

        self.base_scale = Sizes.BASE_SCALE / 4.0
        self.scale(self.base_scale, self.base_scale)
        self.zoom_steps = Steps.ZOOM
        self.zoom_index = self.zoom_steps.index(1.0)
        self.zoom_level = 1.0

        self._snap_pos = None

        self.pressed_keys = set()
        self.pan_speed_px = Sizes.PAN_SPEED_PX
        self.pan_timer = QTimer(self)
        self.pan_timer.setInterval(Sizes.PAN_TIMER_INTERVAL)
        self.pan_timer.timeout.connect(self._pan_step)
        self._scroll_acc_x = 0.0
        self._scroll_acc_y = 0.0

        self._ghost_line_start = None
        self._ghost_line_end = None
        self._ghost_circle_center = None
        self._ghost_circle_radius = 0.0
        self._ghost_arc = None
        self._ghost_text_pos = None
        self._ghost_text_content = ""
        self._ghost_text_size = 1.0
        self._ghost_text_visible = True

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
        if not show:
            self._snap_pos = None
        self.viewport().update()

    def set_show_values(self, show):
        self.show_values = show
        for item in self.scene.items():
            try:
                item.update()
            except RuntimeError:
                pass
        self.viewport().update()

    def set_highlight_pad(self, pos, radius):
        self._highlight_pad_pos = QPointF(pos)
        self._highlight_pad_radius = radius
        self.viewport().update()

    def clear_highlight_pad(self):
        if self._highlight_pad_pos is not None:
            self._highlight_pad_pos = None
            self._highlight_pad_radius = 0.0
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

    def set_ghost_arc(self, cx, cy, sx, sy, angle):
        self._ghost_arc = (cx, cy, sx, sy, angle)
        self.viewport().update()

    def clear_ghost_arc(self):
        self._ghost_arc = None
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

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self.show_grid:
            return
        g = self.grid_size
        scale = self.transform().m11()
        if g * scale < Sizes.MIN_CELL_PX:
            return

        left = int(rect.left() // g) * g
        right = int(rect.right() // g) * g
        top = int(rect.top() // g) * g
        bottom = int(rect.bottom() // g) * g

        step_x = g
        step_y = g
        max_points = 60
        if (right - left) / g > max_points:
            factor = 1
            while (right - left) / (g * factor) > max_points:
                factor *= 2
            step_x = g * factor
        if (bottom - top) / g > max_points:
            factor = 1
            while (bottom - top) / (g * factor) > max_points:
                factor *= 2
            step_y = g * factor

        pen = QPen(self.grid_color, 0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        y = top
        while y <= bottom:
            x = left
            while x <= right:
                painter.drawPoint(QPointF(x, y))
                x += step_x
            y += step_y

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        pen = QPen(QColor(*Colors.AXIS), 0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawLine(QPointF(rect.left(), 0), QPointF(rect.right(), 0))
        painter.drawLine(QPointF(0, rect.top()), QPointF(0, rect.bottom()))

        if self._snap_pos and self.show_snap:
            cross = Sizes.CROSS_SIZE / self.transform().m11()
            p = QPen(QColor(*Colors.SNAP_CROSS), 0)
            p.setCosmetic(True)
            painter.setPen(p)
            x = self._snap_pos.x()
            y = self._snap_pos.y()
            painter.drawLine(QPointF(x - cross, y), QPointF(x + cross, y))
            painter.drawLine(QPointF(x, y - cross), QPointF(x, y + cross))

        if self._highlight_pad_pos is not None and self._highlight_pad_radius > 0:
            hp = QPen(QColor(255, 200, 0), 0)
            hp.setCosmetic(True)
            hp.setWidth(2)
            painter.setPen(hp)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(self._highlight_pad_pos,
                                self._highlight_pad_radius,
                                self._highlight_pad_radius)

        ghost_pen = QPen(QColor(*Colors.GHOST_LINE), 0)
        ghost_pen.setCosmetic(True)
        ghost_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(ghost_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if self._ghost_line_start and self._ghost_line_end:
            painter.drawLine(self._ghost_line_start, self._ghost_line_end)

        if self._ghost_circle_center and self._ghost_circle_radius > 0:
            painter.drawEllipse(self._ghost_circle_center,
                                self._ghost_circle_radius,
                                self._ghost_circle_radius)

        if self._ghost_arc is not None:
            cx, cy, sx, sy, angle = self._ghost_arc
            pts = arc_sample_points(cx, cy, sx, sy, angle, 64)
            if len(pts) >= 2:
                path = QPainterPath()
                path.moveTo(pts[0][0], pts[0][1])
                for px, py in pts[1:]:
                    path.lineTo(px, py)
                painter.drawPath(path)

        if self._ghost_text_pos and self._ghost_text_content:
            path = build_text_path(
                self._ghost_text_content,
                self._ghost_text_size * Sizes.TEXT_FONT_MULTIPLIER,
                center=True,
            )
            if not path.isEmpty():
                color = QColor(*Colors.GHOST_TEXT)
                if not self._ghost_text_visible:
                    color = color.lighter(50)
                painter.save()
                painter.translate(self._ghost_text_pos)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawPath(path)
                painter.restore()

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
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.RightButton:
            self.canvas_right_clicked.emit()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragMode() == QGraphicsView.DragMode.RubberBandDrag:
                items = self.items(event.position().toPoint())
                selectable = [it for it in items if it.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable]
                if selectable and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                    selectable[0].setSelected(not selectable[0].isSelected())
                    event.accept()
                    return
                if not selectable:
                    scene_pos = self.mapToScene(event.position().toPoint())
                    snapped = self.snap_to_grid(scene_pos.x(), scene_pos.y())
                    self.canvas_clicked.emit(snapped.x(), snapped.y())
                super().mousePressEvent(event)
                return
            items = self.items(event.position().toPoint())
            selectable = [it for it in items if it.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable]
            if not selectable:
                scene_pos = self.mapToScene(event.position().toPoint())
                snapped = self.snap_to_grid(scene_pos.x(), scene_pos.y())
                self.canvas_clicked.emit(snapped.x(), snapped.y())
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton and self._panning:
            self._panning = False
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._panning:
            current_pos = event.position().toPoint()
            delta = current_pos - self._pan_start
            self._pan_start = current_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        snapped = self.snap_to_grid(scene_pos.x(), scene_pos.y())
        if self.show_snap:
            self._snap_pos = QPointF(snapped.x(), snapped.y())
        else:
            self._snap_pos = None
        self.mouse_moved.emit(snapped.x(), snapped.y())
        self.viewport().update()
        super().mouseMoveEvent(event)

    def _pan_step(self):
        dx = dy = 0
        if VK_W in self.pressed_keys:
            dy -= 1
        if VK_S in self.pressed_keys:
            dy += 1
        if VK_A in self.pressed_keys:
            dx -= 1
        if VK_D in self.pressed_keys:
            dx += 1
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