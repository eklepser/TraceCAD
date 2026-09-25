from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QFont, QPainterPath, QTransform
from PySide6.QtCore import QRectF, QPointF, Qt
from footprint_editor.graphics.base import BaseGraphicsItem
from footprint_editor.core.models import TextType
from constants import Colors, Sizes


class TextGraphicsItem(BaseGraphicsItem):
    def __init__(self, text_model, canvas, parent=None):
        super().__init__(text_model, canvas, parent)
        self._text_path = None
        self._text_path_key = None

    def _build_text_path(self):
        text = self.model.text
        target_h = self.model.size * Sizes.TEXT_FONT_MULTIPLIER
        key = (text, target_h)
        if self._text_path_key == key and self._text_path is not None:
            return self._text_path

        path = QPainterPath()
        if text and target_h > 0:
            font = QFont()
            font.setPointSizeF(20.0)
            path.addText(0, 0, font, text)
            bounds = path.boundingRect()
            if bounds.height() > 0:
                scale = target_h / bounds.height()
                transform = QTransform()
                transform.scale(scale, scale)
                path = transform.map(path)
        self._text_path = path
        self._text_path_key = key
        return path

    def boundingRect(self):
        path = self._build_text_path()
        if path.isEmpty():
            return QRectF(self.model.x, self.model.y, 0.01, 0.01)
        b = path.boundingRect()
        return QRectF(
            self.model.x + b.left(),
            self.model.y + b.top(),
            b.width(),
            b.height()
        ).adjusted(-0.5, -0.5, 0.5, 0.5)

    def paint(self, painter, option, widget):
        if option.state & QStyle.StateFlag.State_Selected:
            color = QColor(*Colors.SELECTED)
        elif self.model.text_type == TextType.REFERENCE:
            color = QColor(*Colors.REFERENCE)
        elif self.model.text_type == TextType.VALUE:
            color = QColor(*Colors.VALUE)
        else:
            if self.model.visible:
                color = QColor(*Colors.TEXT_VISIBLE)
            else:
                color = QColor(*Colors.TEXT_HIDDEN)

        path = self._build_text_path()
        if path.isEmpty():
            return

        painter.save()
        if not self.model.visible:
            painter.setOpacity(0.3)
        painter.translate(self.model.x, self.model.y)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPath(path)
        painter.restore()

    def apply_drag_delta(self, start, dx, dy):
        self.model.x = start[1] + dx
        self.model.y = start[2] + dy
        self.prepareGeometryChange()
        self.update()