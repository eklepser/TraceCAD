from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker
from PySide6.QtCore import QLineF, QRectF, QPointF, Qt

from constants import Colors


class RatsnestGraphicsItem(QGraphicsItem):
    _next_uid = [1]

    def __init__(self, p1: QPointF, p2: QPointF, net_code: int = 0,
                 net_name: str = "", is_power: bool = False,
                 is_gnd: bool = False,
                 label_a: str = "", label_b: str = "", parent=None):
        super().__init__(parent)
        self.p1 = QPointF(p1)
        self.p2 = QPointF(p2)
        self.net_code = net_code
        self.net_name = net_name
        self.is_power = is_power
        self.is_gnd = is_gnd
        self.label_a = label_a
        self.label_b = label_b
        self.uid = RatsnestGraphicsItem._next_uid[0]
        RatsnestGraphicsItem._next_uid[0] += 1
        self.setZValue(1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)

    def boundingRect(self):
        rect = QRectF(self.p1, self.p2).normalized()
        return rect.adjusted(-0.5, -0.5, 0.5, 0.5)

    def shape(self):
        path = QPainterPath()
        path.moveTo(self.p1)
        path.lineTo(self.p2)
        stroker = QPainterPathStroker()
        stroker.setWidth(0.6)
        return stroker.createStroke(path)

    def paint(self, painter, option, widget):
        if option.state & QStyle.StateFlag.State_Selected:
            color = QColor(*Colors.SELECTED)
        elif self.is_gnd:
            color = QColor(220, 70, 70)
        elif self.is_power:
            color = QColor(235, 150, 60)
        else:
            color = QColor(80, 200, 120)
        pen = QPen(color, 0)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawLine(QLineF(self.p1, self.p2))