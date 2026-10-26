from pbe_editor.ui.commands.drawing import DrawingCommandsMixin
from pbe_editor.ui.commands.editing import EditingCommandsMixin
from pbe_editor.ui.commands.selection import SelectionCommandsMixin


class CommandHandler(DrawingCommandsMixin, EditingCommandsMixin, SelectionCommandsMixin):
    def __init__(self, window):
        from PySide6.QtCore import QPointF
        self.w = window
        self._current_mouse_pos = QPointF(0, 0)
        self._clipboard = []