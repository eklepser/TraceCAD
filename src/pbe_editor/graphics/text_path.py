from PySide6.QtGui import QFont, QPainterPath, QTransform


def build_text_path(text, target_height, bold=False, center=False):
    path = QPainterPath()
    if not text or target_height <= 0:
        return path
    font = QFont()
    font.setPointSizeF(20.0)
    font.setBold(bold)
    path.addText(0, 0, font, text)
    bounds = path.boundingRect()
    if bounds.height() > 0:
        scale = target_height / bounds.height()
        t = QTransform()
        t.scale(scale, scale)
        path = t.map(path)
        if center:
            b = path.boundingRect()
            path.translate(-b.center().x(), -b.center().y())
    return path