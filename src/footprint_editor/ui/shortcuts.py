from PySide6.QtWidgets import QApplication, QLineEdit, QDoubleSpinBox
from PySide6.QtCore import QObject, QEvent


class GlobalKeyFilter(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            fw = QApplication.focusWidget()
            if isinstance(fw, (QLineEdit, QDoubleSpinBox)):
                return super().eventFilter(obj, event)
            return self.window.handle_global_key(event)
        return super().eventFilter(obj, event)