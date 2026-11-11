from pbe_editor.ui.commands.drawing import DrawingCommandsMixin
from pbe_editor.ui.commands.editing import EditingCommandsMixin
from pbe_editor.ui.commands.selection import SelectionCommandsMixin
from pbe_editor.ui.commands.autoplace import AutoplaceCommandsMixin

class CommandHandler(DrawingCommandsMixin, EditingCommandsMixin, 
                     SelectionCommandsMixin, AutoplaceCommandsMixin):
    def __init__(self, window):
        from PySide6.QtCore import QPointF
        self.w = window
        self._current_mouse_pos = QPointF(0, 0)
        self._clipboard = []