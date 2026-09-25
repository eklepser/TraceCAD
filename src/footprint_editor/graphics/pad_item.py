from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath, QTransform
from PySide6.QtCore import QRectF, QPointF, Qt
from footprint_editor.core.models import PadShape, PadType
from footprint_editor.graphics.base import BaseGraphicsItem
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
        return QRectF(-w/2-extra, -h/2-extra, w+2*extra, h+2*extra)

    def _build_text_path(self):
        text = self.model.number
        target_h = min(self.model.width, self.model.height) * Sizes.PAD_NUMBER_FONT_RATIO
        key = (text, target_h)
        if self._text_path_key == key and self._text_path is not None:
            return self._text_path

        path = QPainterPath()
        if text and target_h > 0:
            font = QFont()
            font.setPointSizeF(20.0)
            font.setBold(True)
            path.addText(0, 0, font, text)
            bounds = path.boundingRect()
            if bounds.height() > 0:
                scale = target_h / bounds.height()
                transform = QTransform()
                transform.scale(scale, scale)
                path = transform.map(path)
                bounds = path.boundingRect()
                path.translate(-bounds.center())
        self._text_path = path
        self._text_path_key = key
        return path

    def paint(self, painter, option, widget):
        if option.state & QStyle.StateFlag.State_Selected:
            color = QColor(*Colors.SELECTED)
        else:
            color = QColor(*Colors.PAD)

        w = self.model.width
        h = self.model.height
        drill = self.model.drill or 0.0

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)

        if self.model.shape == PadShape.CIRCLE:
            painter.drawEllipse(QRectF(-w/2, -h/2, w, h))
        elif self.model.shape == PadShape.RECT:
            painter.drawRect(QRectF(-w/2, -h/2, w, h))
        elif self.model.shape == PadShape.OVAL:
            painter.drawRoundedRect(QRectF(-w/2, -h/2, w, h), w/2, h/2)

        if drill > 0:
            painter.setBrush(QColor(*Colors.BACKGROUND))
            painter.drawEllipse(QRectF(-drill/2, -drill/2, drill, drill))

        path = self._build_text_path()
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