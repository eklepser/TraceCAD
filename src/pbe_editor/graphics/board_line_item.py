from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker
from PySide6.QtCore import QLineF, QRectF, QPointF, Qt

from constants import Colors, Sizes
from constants.board_settings import LAYER_COLORS
from footprint_editor.core.arc_geometry import arc_sample_points
from footprint_editor.graphics.text_path import build_text_path


def _layer_color(layer):
    if layer in LAYER_COLORS:
        return QColor(*LAYER_COLORS[layer])
    return QColor(*Colors.TEXT_VISIBLE)


def _snap(value, grid):
    if grid <= 0:
        return value
    return round(value / grid) * grid


class BoardLineGraphicsItem(QGraphicsItem):
    def __init__(self, line, canvas, parent=None):
        super().__init__(parent)
        self.model = line
        self.canvas = canvas
        self.model.graphics_item = self
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(2)
        self.setPos(line.x1, line.y1)

    def boundingRect(self):
        w = self.model.width + 0.5
        x2 = self.model.x2 - self.model.x1
        y2 = self.model.y2 - self.model.y1
        return QRectF(QPointF(0.0, 0.0), QPointF(x2, y2)).normalized().adjusted(-w, -w, w, w)

    def shape(self):
        path = QPainterPath()
        path.moveTo(0.0, 0.0)
        path.lineTo(self.model.x2 - self.model.x1, self.model.y2 - self.model.y1)
        stroker = QPainterPathStroker()
        stroker.setWidth(max(0.4, self.model.width * 2.0))
        return stroker.createStroke(path)

    def paint(self, painter, option, widget):
        color = QColor(*Colors.SELECTED) if (option.state & QStyle.StateFlag.State_Selected) else _layer_color(self.model.layer)
        pen = QPen(color, max(0.05, self.model.width))
        pen.setCosmetic(False)
        painter.setPen(pen)
        painter.drawLine(QLineF(0.0, 0.0,
                                self.model.x2 - self.model.x1,
                                self.model.y2 - self.model.y1))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            grid = self.canvas.grid_size
            return QPointF(_snap(value.x(), grid), _snap(value.y(), grid))
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            dx = value.x() - self.model.x1
            dy = value.y() - self.model.y1
            self.model.x1 = value.x()
            self.model.y1 = value.y()
            self.model.x2 += dx
            self.model.y2 += dy
            self.prepareGeometryChange()
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)


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