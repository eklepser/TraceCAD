from PySide6.QtWidgets import QStyle
from PySide6.QtGui import QColor
from PySide6.QtCore import QRectF, Qt
from footprint_editor.graphics.base import BaseGraphicsItem
from common.graphics.text_path import build_text_path
from footprint_editor.core.models import TextType
from constants import Colors, Sizes


class TextGraphicsItem(BaseGraphicsItem):
    def __init__(self, text_model, canvas, parent=None):
        super().__init__(text_model, canvas, parent)
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
            return QRectF(self.model.x, self.model.y, 0.01, 0.01)
        b = path.boundingRect()
        return QRectF(self.model.x + b.left(), self.model.y + b.top(),
                      b.width(), b.height()).adjusted(-0.5, -0.5, 0.5, 0.5)

    def _color(self, selected):
        if selected:
            return QColor(*Colors.SELECTED)
        if self.model.text_type == TextType.REFERENCE:
            return QColor(*Colors.REFERENCE)
        if self.model.text_type == TextType.VALUE:
            return QColor(*Colors.VALUE)
        return QColor(*(Colors.TEXT_VISIBLE if self.model.visible else Colors.TEXT_HIDDEN))

    def paint(self, painter, option, widget):
        path = self._path()
        if path.isEmpty():
            return
        color = self._color(bool(option.state & QStyle.StateFlag.State_Selected))

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