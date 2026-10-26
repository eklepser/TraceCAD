from pbe_editor.core.board_models import (
    BoardModule, BoardLine, BoardCircle, BoardArc, BoardText,
)
from pbe_editor.core.board_models import prefix_from_footprint_name


def model_center(m):
    if isinstance(m, BoardModule):
        return m.x, m.y
    if isinstance(m, BoardLine):
        return (m.x1 + m.x2) / 2.0, (m.y1 + m.y2) / 2.0
    if isinstance(m, (BoardCircle, BoardArc, BoardText)):
        return m.x, m.y
    return 0.0, 0.0


def translate_model(m, dx, dy):
    if isinstance(m, BoardModule):
        m.x += dx
        m.y += dy
    elif isinstance(m, BoardLine):
        m.x1 += dx
        m.y1 += dy
        m.x2 += dx
        m.y2 += dy
    elif isinstance(m, BoardArc):
        m.x += dx
        m.y += dy
        m.sx += dx
        m.sy += dy
    elif isinstance(m, (BoardCircle, BoardText)):
        m.x += dx
        m.y += dy


def rotate_model_90(m):
    if isinstance(m, BoardModule):
        m.angle = (m.angle + 90.0) % 360.0
    elif isinstance(m, BoardLine):
        cx = (m.x1 + m.x2) / 2.0
        cy = (m.y1 + m.y2) / 2.0
        dx1, dy1 = m.x1 - cx, m.y1 - cy
        dx2, dy2 = m.x2 - cx, m.y2 - cy
        m.x1, m.y1 = cx - dy1, cy + dx1
        m.x2, m.y2 = cx - dy2, cy + dx2
    elif isinstance(m, BoardArc):
        dx, dy = m.sx - m.x, m.sy - m.y
        m.sx = m.x - dy
        m.sy = m.y + dx


def next_uid(items):
    if not items:
        return 1
    return max(x.uid for x in items) + 1


def auto_reference_for(board, fp_name):
    return board.auto_reference(prefix_from_footprint_name(fp_name))