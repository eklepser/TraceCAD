from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, Signal, QTimer
from PySide6.QtGui import QColor, QWheelEvent, QMouseEvent, QPainter, QPen

from constants import Colors, Sizes, Steps, VK_W, VK_A, VK_S, VK_D


class BoardCanvas(QGraphicsView):
    zoom_changed = Signal(float)
    mouse_moved = Signal(float, float)
    ratsnest_update_requested = Signal()
    canvas_clicked = Signal(float, float)
    canvas_right_clicked = Signal()
    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._panning = False
        self._pan_start = None
        self.show_grid = True

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
        self.scene.setSceneRect(-500, -500, 1000, 1000)
        self.scene.selectionChanged.connect(self.selection_changed.emit)

        self.grid_size = float(Steps.DEFAULT_GRID)
        self.grid_color = QColor(*Colors.GRID)
        self.background_color = QColor(*Colors.BACKGROUND)
        self.setBackgroundBrush(self.background_color)

        self.base_scale = Sizes.BASE_SCALE
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

    def apply_theme(self):
        self.grid_color = QColor(*Colors.GRID)
        self.background_color = QColor(*Colors.BACKGROUND)
        self.setBackgroundBrush(self.background_color)
        self.viewport().update()

    def set_grid_size(self, size_mm):
        self.grid_size = size_mm
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

        if self._snap_pos:
            cross = Sizes.CROSS_SIZE / self.transform().m11()
            p = QPen(QColor(*Colors.SNAP_CROSS), 0)
            p.setCosmetic(True)
            painter.setPen(p)
            x = self._snap_pos.x()
            y = self._snap_pos.y()
            painter.drawLine(QPointF(x - cross, y), QPointF(x + cross, y))
            painter.drawLine(QPointF(x, y - cross), QPointF(x, y + cross))

        if self._ghost_line_start and self._ghost_line_end:
            gp = QPen(QColor(*Colors.GHOST_LINE), 0)
            gp.setCosmetic(True)
            gp.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(gp)
            painter.drawLine(self._ghost_line_start, self._ghost_line_end)

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
            # Если текущий dragMode — RubberBand (режим выделения) — пусть Qt сам обрабатывает
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
            # Иначе — рисование: клик по пустому месту
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
        self._snap_pos = QPointF(snapped.x(), snapped.y())
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