from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, QBrush
from PySide6.QtCore import QLineF, QRectF, QPointF, Qt

from constants import Colors
from constants.board_settings import LAYER_COLORS


def _layer_color(layer):
    if layer in LAYER_COLORS:
        return QColor(*LAYER_COLORS[layer])
    return QColor(*Colors.TEXT_VISIBLE)


def _snap(value, grid):
    if grid <= 0:
        return value
    return round(value / grid) * grid


class BoardLineGraphicsItem(QGraphicsItem):
    HANDLE_RADIUS_PX = 4.0
    HOVER_RADIUS_PX = 5.0
    ACTIVE_RADIUS_PX = 6.0

    def __init__(self, line, canvas, parent=None):
        super().__init__(parent)
        self.model = line
        self.canvas = canvas
        self.model.graphics_item = self

        self._active_handle = None
        self._hover_handle = None

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)
        self.setPos(0.0, 0.0)

    def get_handles(self):
        return [QPointF(self.model.x1, self.model.y1),
                QPointF(self.model.x2, self.model.y2)]

    def _hit_test_handle(self, scene_pos):
        if not self.isSelected():
            return None
        scale = self.canvas.transform().m11() if self.canvas else 1.0
        if scale <= 0:
            scale = 1.0
        radius = self.HANDLE_RADIUS_PX * 3.0 / scale
        best_idx = None
        best_dist = float('inf')
        for i, pt in enumerate(self.get_handles()):
            dx = scene_pos.x() - pt.x()
            dy = scene_pos.y() - pt.y()
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < radius and dist < best_dist:
                best_idx = i
                best_dist = dist
        return best_idx

    def boundingRect(self):
        w = self.model.width + 0.5
        rect = QRectF(self.model.x1, self.model.y1,
                      self.model.x2 - self.model.x1,
                      self.model.y2 - self.model.y1).normalized()
        return rect.adjusted(-w, -w, w, w)

    def shape(self):
        path = QPainterPath()
        path.moveTo(self.model.x1, self.model.y1)
        path.lineTo(self.model.x2, self.model.y2)
        stroker = QPainterPathStroker()
        stroker.setWidth(max(0.4, self.model.width * 2.0))
        return stroker.createStroke(path)

    def paint(self, painter, option, widget):
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        color = QColor(*Colors.SELECTED) if selected else _layer_color(self.model.layer)
        pen = QPen(color, max(0.05, self.model.width))
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QLineF(self.model.x1, self.model.y1,
                                self.model.x2, self.model.y2))

        if selected:
            scale = self.canvas.transform().m11() if self.canvas else 1.0
            if scale <= 0:
                scale = 1.0
            for i, pt in enumerate(self.get_handles()):
                active = (i == self._active_handle)
                hover = (i == self._hover_handle)
                if active:
                    fill = QColor(0, 200, 0)
                    border = QColor(255, 255, 255)
                    r_px = self.ACTIVE_RADIUS_PX
                elif hover:
                    fill = QColor(255, 255, 255)
                    border = QColor(0, 150, 255)
                    r_px = self.HOVER_RADIUS_PX
                else:
                    fill = QColor(*Colors.SELECTED)
                    border = QColor(255, 255, 255)
                    r_px = self.HANDLE_RADIUS_PX
                radius = r_px / scale
                p = QPen(border, 0)
                p.setCosmetic(True)
                painter.setPen(p)
                painter.setBrush(QBrush(fill))
                painter.drawEllipse(pt, radius, radius)

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

    def hoverLeaveEvent(self, event):
        if self._hover_handle is not None:
            self._hover_handle = None
            self.update()
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            handle_idx = self._hit_test_handle(scene_pos)
            if handle_idx is not None:
                self._active_handle = handle_idx
                self.update()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._active_handle is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            current = self.mapToScene(event.pos())
            grid = self.canvas.grid_size
            sx = _snap(current.x(), grid)
            sy = _snap(current.y(), grid)
            if self._active_handle == 0:
                self.model.x1 = sx
                self.model.y1 = sy
            else:
                self.model.x2 = sx
                self.model.y2 = sy
            self.prepareGeometryChange()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._active_handle is not None:
            self._active_handle = None
            self.update()
            if hasattr(self.canvas, 'content_changed'):
                self.canvas.content_changed.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class BoardCircleGraphicsItem(QGraphicsItem):
    def __init__(self, circle, canvas, parent=None):
        super().__init__(parent)
        self.model = circle
        self.canvas = canvas
        self.model.graphics_item = self
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(2)
        self.setPos(circle.x, circle.y)

    def boundingRect(self):
        r = self.model.radius
        extra = self.model.width + 0.5
        return QRectF(-r, -r, 2 * r, 2 * r).adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(QPointF(0.0, 0.0), self.model.radius, self.model.radius)
        stroker = QPainterPathStroker()
        stroker.setWidth(max(0.4, self.model.width * 2.0))
        return stroker.createStroke(path)

    def paint(self, painter, option, widget):
        color = QColor(*Colors.SELECTED) if (option.state & QStyle.StateFlag.State_Selected) else _layer_color(self.model.layer)
        pen = QPen(color, max(0.05, self.model.width))
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(0.0, 0.0), self.model.radius, self.model.radius)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            grid = self.canvas.grid_size
            return QPointF(_snap(value.x(), grid), _snap(value.y(), grid))
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.model.x = value.x()
            self.model.y = value.y()
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)


class BoardArcGraphicsItem(QGraphicsItem):
    def __init__(self, arc, canvas, parent=None):
        super().__init__(parent)
        self.model = arc
        self.canvas = canvas
        self.model.graphics_item = self
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(2)
        self.setPos(arc.x, arc.y)

    def _local_path(self):
        pts = arc_sample_points(
            0.0, 0.0,
            self.model.sx - self.model.x,
            self.model.sy - self.model.y,
            self.model.angle, 64,
        )
        if len(pts) < 2:
            return QPainterPath()
        path = QPainterPath()
        path.moveTo(pts[0][0], pts[0][1])
        for px, py in pts[1:]:
            path.lineTo(px, py)
        return path

    def boundingRect(self):
        b = self._local_path().boundingRect()
        extra = self.model.width + 0.5
        return b.adjusted(-extra, -extra, extra, extra)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(max(0.4, self.model.width * 2.0))
        return stroker.createStroke(self._local_path())

    def paint(self, painter, option, widget):
        color = QColor(*Colors.SELECTED) if (option.state & QStyle.StateFlag.State_Selected) else _layer_color(self.model.layer)
        pen = QPen(color, max(0.05, self.model.width))
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self._local_path())

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            grid = self.canvas.grid_size
            return QPointF(_snap(value.x(), grid), _snap(value.y(), grid))
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            dx = value.x() - self.model.x
            dy = value.y() - self.model.y
            self.model.x = value.x()
            self.model.y = value.y()
            self.model.sx += dx
            self.model.sy += dy
            self.prepareGeometryChange()
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)


class BoardTextGraphicsItem(QGraphicsItem):
    def __init__(self, text, canvas, parent=None):
        super().__init__(parent)
        self.model = text
        self.canvas = canvas
        self.model.graphics_item = self
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(2)
        self.setPos(text.x, text.y)
        self._path_cache = None
        self._path_key = None

    def _path(self):
        target_h = self.model.size * Sizes.TEXT_FONT_MULTIPLIER
        key = (self.model.text, target_h)
        if self._path_key != key:
            self._path_cache = build_text_path(self.model.text, target_h, center=True)
            self._path_key = key
        return self._path_cache

    def boundingRect(self):
        path = self._path()
        if path.isEmpty():
            return QRectF(-1, -1, 2, 2)
        b = path.boundingRect()
        return QRectF(b.left(), b.top(), b.width(), b.height()).adjusted(-1, -1, 1, 1)

    def paint(self, painter, option, widget):
        path = self._path()
        if path.isEmpty():
            return
        color = QColor(*Colors.SELECTED) if (option.state & QStyle.StateFlag.State_Selected) else _layer_color(self.model.layer)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPath(path)
        painter.restore()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            grid = self.canvas.grid_size
            return QPointF(_snap(value.x(), grid), _snap(value.y(), grid))
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.model.x = value.x()
            self.model.y = value.y()
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)