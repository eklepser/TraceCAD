from footprint_editor.core.models import Pad, Line, Circle, Arc, Text


def rotate_point_90(x, y, cx, cy):
    dx, dy = x - cx, y - cy
    return cx - dy, cy + dx


def model_center(m):
    if isinstance(m, Pad):
        return m.x, m.y
    if isinstance(m, Line):
        return (m.x + m.x2) / 2, (m.y + m.y2) / 2
    if isinstance(m, Circle):
        return m.x, m.y
    if isinstance(m, Arc):
        return m.x, m.y
    if isinstance(m, Text):
        return m.x, m.y
    return 0, 0


def translate_model(m, dx, dy):
    if isinstance(m, Pad):
        m.x += dx
        m.y += dy
    elif isinstance(m, Line):
        m.x += dx
        m.y += dy
        m.x2 += dx
        m.y2 += dy
    elif isinstance(m, Circle):
        m.x += dx
        m.y += dy
    elif isinstance(m, Arc):
        m.x += dx
        m.y += dy
        m.sx += dx
        m.sy += dy
    elif isinstance(m, Text):
        m.x += dx
        m.y += dy


def append_model(fp, m):
    if isinstance(m, Pad):
        fp.pads.append(m)
    elif isinstance(m, Line):
        fp.lines.append(m)
    elif isinstance(m, Circle):
        fp.circles.append(m)
    elif isinstance(m, Arc):
        fp.arcs.append(m)
    elif isinstance(m, Text):
        fp.texts.append(m)


def model_bounds(m):
    from footprint_editor.core.arc_geometry import arc_sample_points
    if isinstance(m, Pad):
        return [(m.x - m.width / 2, m.y - m.height / 2),
                (m.x + m.width / 2, m.y + m.height / 2)]
    if isinstance(m, Line):
        return [(m.x, m.y), (m.x2, m.y2)]
    if isinstance(m, Circle):
        return [(m.x - m.radius, m.y - m.radius),
                (m.x + m.radius, m.y + m.radius)]
    if isinstance(m, Arc):
        return arc_sample_points(m.x, m.y, m.sx, m.sy, m.angle, 16)
    if isinstance(m, Text):
        return [(m.x, m.y)]
    return []


def rotate_model(m, cx, cy):
    from footprint_editor.core.models import PadShape
    if isinstance(m, Pad):
        m.x, m.y = rotate_point_90(m.x, m.y, cx, cy)
        if m.shape in (PadShape.RECT, PadShape.OVAL):
            m.width, m.height = m.height, m.width
    elif isinstance(m, Line):
        m.x, m.y = rotate_point_90(m.x, m.y, cx, cy)
        m.x2, m.y2 = rotate_point_90(m.x2, m.y2, cx, cy)
    elif isinstance(m, Circle):
        m.x, m.y = rotate_point_90(m.x, m.y, cx, cy)
    elif isinstance(m, Arc):
        m.x, m.y = rotate_point_90(m.x, m.y, cx, cy)
        m.sx, m.sy = rotate_point_90(m.sx, m.sy, cx, cy)
    elif isinstance(m, Text):
        m.x, m.y = rotate_point_90(m.x, m.y, cx, cy)


def remove_from_footprint(fp, model):
    for bucket in (fp.pads, fp.lines, fp.circles, fp.arcs, fp.texts):
        if model in bucket:
            bucket.remove(model)
            return