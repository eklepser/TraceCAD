from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QFont, QFontMetrics
from PySide6.QtCore import QRectF, QPointF, Qt
from footprint_editor.graphics.base import BaseGraphicsItem
from constants import Colors, Sizes

class TextGraphicsItem(BaseGraphicsItem):
    def __init__(self, text_model, canvas, parent=None):
        super().__init__(text_model, canvas, parent)

    def boundingRect(self):
        font = QFont()
        font.setPointSizeF(self.model.size * Sizes.TEXT_FONT_MULTIPLIER)
        metrics = QFontMetrics(font)
        rect = metrics.boundingRect(self.model.text)
        return QRectF(self.model.x, self.model.y - rect.height(), rect.width(), rect.height()).adjusted(-0.5, -0.5, 0.5, 0.5)

    def paint(self, painter, option, widget):
        font = QFont()
        font.setPointSizeF(self.model.size * Sizes.TEXT_FONT_MULTIPLIER)
        painter.setFont(font)
        
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QColor(*Colors.SELECTED))
        else:
            if self.model.visible:
                painter.setPen(QColor(*Colors.TEXT_VISIBLE))
            else:
                painter.setPen(QColor(*Colors.TEXT_HIDDEN))
            
        painter.drawText(QPointF(self.model.x, self.model.y), self.model.text)

    def apply_drag_delta(self, start, dx, dy):
        self.model.x = start[1] + dx
        self.model.y = start[2] + dy
        self.prepareGeometryChange()
        self.update()