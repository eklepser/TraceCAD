from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QWheelEvent, QMouseEvent, QPainter, QPen

from constants import Colors, Sizes, Steps


class BoardCanvas(QGraphicsView):
    zoom_changed = Signal(float)
    mouse_moved = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._panning = False
        self._pan_start = None

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFrameShape(QGraphicsView.Shape.Box)
        self.setFrameShadow(QGraphicsView.Shadow.Plain)
        self.setLineWidth(1)
        self.setStyleSheet("QGraphicsView { border: 1px solid #ffffff; }")

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(-500, -500, 1000, 1000)

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

    def apply_theme(self):
        self.grid_color = QColor(*Colors.GRID)
        self.background_color = QColor(*Colors.BACKGROUND)
        self.setBackgroundBrush(self.background_color)
        self.viewport().update()

    def snap_to_grid(self, x, y):
        g = self.grid_size
        return QPointF(round(x / g) * g, round(y / g) * g)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        g = self.grid_size
        scale = self.transform().m11()
        if g * scale < Sizes.MIN_CELL_PX:
            return

        left = int(rect.left() // g) * g
        right = int(rect.right() // g) * g
        top = int(rect.top() // g) * g
        bottom = int(rect.bottom() // g) * g

        pen = QPen(self.grid_color, 0)
        pen.setCosmetic(True)
        painter.setPen(pen)

        x = left
        while x <= right:
            y = top
            while y <= bottom:
                painter.drawPoint(QPointF(x, y))
                y += g
            x += g

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