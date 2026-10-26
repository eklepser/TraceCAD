from PySide6.QtWidgets import QLineEdit
from PySide6.QtGui import QDoubleValidator


class NumericLineEdit(QLineEdit):
    def __init__(self, value=0.0, decimals=4, min_val=-1e9, max_val=1e9, parent=None):
        super().__init__(parent)
        self._decimals = decimals
        self._min = min_val
        self._max = max_val
        validator = QDoubleValidator(min_val, max_val, decimals, self)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.setValidator(validator)
        self.setText(self._format(value))
        self.setMinimumWidth(100)
        self.setMinimumHeight(24)

    def _format(self, value):
        return f"{value:.{self._decimals}f}"

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()

    def value(self):
        text = self.text().strip().replace(',', '.')
        if not text:
            return 0.0
        try:
            v = float(text)
        except ValueError:
            return 0.0
        return max(self._min, min(v, self._max))

    def setValue(self, value):
        self.setText(self._format(value))