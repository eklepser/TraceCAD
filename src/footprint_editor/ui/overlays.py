from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath
from constants import Colors, Sizes
from common.graphics.text_path import build_text_path
from common.arc_geometry import arc_sample_points


MAX_GRID_POINTS_VISUAL = 60


def _effective_step(span, grid_size, max_points):
    if span <= 0 or grid_size <= 0:
        return grid_size
    if span / grid_size <= max_points:
        return grid_size
    factor = 1
    while span / (grid_size * factor) > max_points:
        factor *= 2
    return grid_size * factor


def draw_grid(painter, rect, view):
    grid_size = view.grid_size
    scale = view.transform().m11()
    if grid_size * scale < Sizes.MIN_CELL_PX:
        return

    left = int(rect.left() // grid_size) * grid_size
    right = int(rect.right() // grid_size) * grid_size
    top = int(rect.top() // grid_size) * grid_size
    bottom = int(rect.bottom() // grid_size) * grid_size

    step_x = _effective_step(right - left, grid_size, MAX_GRID_POINTS_VISUAL)
    step_y = _effective_step(bottom - top, grid_size, MAX_GRID_POINTS_VISUAL)

    pen = QPen(view.grid_color, 0)
    pen.setCosmetic(True)
    painter.setPen(pen)

    y = top
    while y <= bottom:
        x = left
        while x <= right:
            painter.drawPoint(QPointF(x, y))
            x += step_x
        y += step_y


def draw_axes(painter, rect, view):
    pen = QPen(QColor(*Colors.AXIS), 0)
    pen.setCosmetic(True)
    painter.setPen(pen)
    painter.drawLine(QPointF(rect.left(), 0), QPointF(rect.right(), 0))
    painter.drawLine(QPointF(0, rect.top()), QPointF(0, rect.bottom()))
    return Sizes.CROSS_SIZE / view.transform().m11()


def draw_snap_marker(painter, pos, cross_size):
    pen = QPen(QColor(*Colors.SNAP_CROSS), 0)
    pen.setCosmetic(True)
    painter.setPen(pen)
    x, y = pos.x(), pos.y()
    painter.drawLine(QPointF(x - cross_size, y), QPointF(x + cross_size, y))
    painter.drawLine(QPointF(x, y - cross_size), QPointF(x, y + cross_size))


def draw_ghost_line(painter, start, end):
    if not start or not end:
        return
    pen = QPen(QColor(*Colors.GHOST_LINE), 0)
    pen.setCosmetic(True)
    pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.drawLine(start, end)


def draw_ghost_circle(painter, center, radius):
    if not center or radius <= 0:
        return
    pen = QPen(QColor(*Colors.GHOST_LINE), 0)
    pen.setCosmetic(True)
    pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(center, radius, radius)


def draw_ghost_arc(painter, cx, cy, sx, sy, angle):
    if cx is None or sx is None:
        return
    pts = arc_sample_points(cx, cy, sx, sy, angle, 64)
    if len(pts) < 2:
        return
    path = QPainterPath()
    path.moveTo(pts[0][0], pts[0][1])
    for px, py in pts[1:]:
        path.lineTo(px, py)

    pen = QPen(QColor(*Colors.GHOST_LINE), 0)
    pen.setCosmetic(True)
    pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(path)


def draw_ghost_text(painter, pos, text, size, visible):
    if not pos or not text:
        return
    path = build_text_path(text, size * Sizes.TEXT_FONT_MULTIPLIER, center=True)
    if path.isEmpty():
        return
    color = QColor(*Colors.GHOST_TEXT)
    if not visible:
        color = color.lighter(50)
    painter.save()
    painter.translate(pos)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawPath(path)
    painter.restore()