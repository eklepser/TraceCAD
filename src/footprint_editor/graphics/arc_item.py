from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker
from PySide6.QtCore import QRectF, QPointF, Qt
from footprint_editor.graphics.base import BaseGraphicsItem
from footprint_editor.core.arc_geometry import arc_sample_points
from constants import Colors


class ArcGraphicsItem(BaseGraphicsItem):
    def __init__(self, arc_model, canvas, is_preview=False, parent=None):
        super().__init__(arc_model, canvas, parent)
        self.is_preview = is_preview
        self._path_cache = None
        self._path_key = None

    def _build_path(self):
        m = self.model
        key = (m.x, m.y, m.sx, m.sy, m.angle)
        if self._path_key == key and self._path_cache is not None:
            return self._path_cache

        path = QPainterPath()
        pts = arc_sample_points(m.x, m.y, m.sx, m.sy, m.angle, 64)
        if not pts:
            self._path_cache = path
            self._path_key = key
            return path
        path.moveTo(pts[0][0], pts[0][1])
        for px, py in pts[1:]:
            path.lineTo(px, py)
        self._path_cache = path
        self._path_key = key
        return path

    def boundingRect(self):
        b = self._build_path().boundingRect()
        extra = self.model.width / 2.0 + 0.5
        return b.adjusted(-extra, -extra, extra, extra)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(max(0.5, self.model.width * 2.0))
        return stroker.createStroke(self._build_path())

    def paint(self, painter, option, widget):
        if option.state & QStyle.StateFlag.State_Selected:
            color = QColor(*Colors.SELECTED)
        else:
            color = QColor(*Colors.TEXT_VISIBLE)

        pen = QPen(color, self.model.width if not self.is_preview else 0.05)
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if self.is_preview:
            pen.setStyle(Qt.PenStyle.DashLine)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self._build_path())

    def apply_drag_delta(self, start, dx, dy):
        if getattr(self.model, 'locked', False):
            return
        self.model.x = start[1] + dx
        self.model.y = start[2] + dy
        self.model.sx = start[3] + dx
        self.model.sy = start[4] + dy
        self._path_cache = None
        self.prepareGeometryChange()
        self.update()