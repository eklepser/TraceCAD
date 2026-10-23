from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont
from PySide6.QtCore import QRectF, QPointF, Qt

from constants import Colors


class BoardModuleGraphicsItem(QGraphicsItem):
    def __init__(self, module, canvas, parent=None):
        super().__init__(parent)
        self.module = module
        self.canvas = canvas
        self.module.graphics_item = self

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setPos(module.x, module.y)
        self.setRotation(module.angle)
        self.setZValue(10)

    def boundingRect(self):
        fp = self.module.footprint
        xs = []
        ys = []
        for pad in fp.pads:
            xs.append(pad.x - pad.width / 2)
            xs.append(pad.x + pad.width / 2)
            ys.append(pad.y - pad.height / 2)
            ys.append(pad.y + pad.height / 2)
        for line in fp.lines:
            xs.extend([line.x, line.x2])
            ys.extend([line.y, line.y2])
        for circle in fp.circles:
            xs.extend([circle.x - circle.radius, circle.x + circle.radius])
            ys.extend([circle.y - circle.radius, circle.y + circle.radius])

        if not xs:
            return QRectF(-10, -10, 20, 20)

        left = min(xs)
        right = max(xs)
        top = min(ys)
        bottom = max(ys)
        extra = 1.0
        return QRectF(left - extra, top - extra,
                      right - left + 2 * extra, bottom - top + 2 * extra)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget):
        fp = self.module.footprint

        if option.state & QStyle.StateFlag.State_Selected:
            outline_color = QColor(*Colors.SELECTED)
        else:
            outline_color = QColor(200, 200, 200)

        pen = QPen(outline_color, 0.15)
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for line in fp.lines:
            painter.drawLine(QPointF(line.x, line.y), QPointF(line.x2, line.y2))

        for circle in fp.circles:
            painter.drawEllipse(QPointF(circle.x, circle.y), circle.radius, circle.radius)

        for pad in fp.pads:
            pad_color = QColor(*Colors.PAD)
            if option.state & QStyle.StateFlag.State_Selected:
                pad_color = QColor(*Colors.SELECTED)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(pad_color))
            painter.drawEllipse(QRectF(pad.x - pad.width / 2, pad.y - pad.height / 2,
                                       pad.width, pad.height))
            if pad.drill and pad.drill > 0:
                painter.setBrush(QColor(*Colors.BACKGROUND))
                painter.drawEllipse(QRectF(pad.x - pad.drill / 2, pad.y - pad.drill / 2,
                                           pad.drill, pad.drill))

        font = QFont()
        font.setPointSizeF(1.2)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor(150, 220, 150), 0.2))
        painter.drawText(QPointF(0, 0), self.module.reference)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)