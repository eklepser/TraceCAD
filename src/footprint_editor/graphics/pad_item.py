from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QColor
from PySide6.QtCore import QRectF, Qt
from footprint_editor.core.models import PadShape, PadType
from footprint_editor.graphics.base import BaseGraphicsItem
from footprint_editor.graphics.text_path import build_text_path
from constants import Colors, Sizes


class PadGraphicsItem(BaseGraphicsItem):
    def __init__(self, pad, canvas, parent=None):
        super().__init__(pad, canvas, parent)
        self.setPos(pad.x, pad.y)
        self._text_path = None
        self._text_path_key = None

    def boundingRect(self):
        w = self.model.width
        h = self.model.height
        extra = 0.5
        return QRectF(-w / 2 - extra, -h / 2 - extra, w + 2 * extra, h + 2 * extra)

    def _text(self):
        target_h = min(self.model.width, self.model.height) * Sizes.PAD_NUMBER_FONT_RATIO
        key = (self.model.number, target_h)
        if self._text_path_key != key:
            self._text_path = build_text_path(self.model.number, target_h, bold=True, center=True)
            self._text_path_key = key
        return self._text_path

    def paint(self, painter, option, widget):
        color = QColor(*(Colors.SELECTED if option.state & QStyle.StateFlag.State_Selected
                         else Colors.PAD))

        w = self.model.width
        h = self.model.height
        drill = self.model.drill or 0.0

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)

        if self.model.shape == PadShape.CIRCLE:
            painter.drawEllipse(QRectF(-w / 2, -h / 2, w, h))
        elif self.model.shape == PadShape.RECT:
            painter.drawRect(QRectF(-w / 2, -h / 2, w, h))
        elif self.model.shape == PadShape.OVAL:
            painter.drawRoundedRect(QRectF(-w / 2, -h / 2, w, h), w / 2, h / 2)

        if drill > 0:
            painter.setBrush(QColor(*Colors.BACKGROUND))
            painter.drawEllipse(QRectF(-drill / 2, -drill / 2, drill, drill))

        path = self._text()
        if not path.isEmpty():
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(*Colors.PAD_NUMBER))
            painter.drawPath(path)
            painter.restore()

    def apply_drag_delta(self, start, dx, dy):
        if getattr(self.model, 'locked', False):
            return
        self.model.x = start[1] + dx
        self.model.y = start[2] + dy
        self.setPos(self.model.x, self.model.y)