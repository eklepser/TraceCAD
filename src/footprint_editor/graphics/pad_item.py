from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from PySide6.QtCore import QRectF, QPointF, Qt
from footprint_editor.core.models import PadShape, PadType
from footprint_editor.graphics.base import BaseGraphicsItem
from constants import Colors, Sizes

class PadGraphicsItem(BaseGraphicsItem):
    def __init__(self, pad, canvas, parent=None):
        super().__init__(pad, canvas, parent)
        self.setPos(pad.x, pad.y)

    def boundingRect(self):
        w = self.model.width
        h = self.model.height
        extra = 0.5
        return QRectF(-w/2-extra, -h/2-extra, w+2*extra, h+2*extra)

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
        
        painter.setPen(QColor(*Colors.PAD_NUMBER))
        font = QFont()
        font_size = min(w, h) * Sizes.PAD_NUMBER_FONT_RATIO
        font.setPointSizeF(font_size * Sizes.TEXT_FONT_MULTIPLIER)
        font.setBold(True)
        painter.setFont(font)
        
        painter.drawText(QRectF(-w/2, -h/2, w, h), Qt.AlignCenter, self.model.number)

    def apply_drag_delta(self, start, dx, dy):
        self.model.x = start[1] + dx
        self.model.y = start[2] + dy
        self.setPos(self.model.x, self.model.y)