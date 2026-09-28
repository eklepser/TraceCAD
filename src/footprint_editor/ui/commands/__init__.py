from footprint_editor.ui.commands.drawing import DrawingCommandsMixin
from footprint_editor.ui.commands.editing import EditingCommandsMixin
from footprint_editor.ui.commands.module_files import ModuleFilesMixin
from footprint_editor.ui.commands.libraries import LibrariesMixin


class CommandHandler(DrawingCommandsMixin, EditingCommandsMixin,
                     ModuleFilesMixin, LibrariesMixin):
    def __init__(self, window):
        from PySide6.QtCore import QPointF
        self.w = window
        self.clipboard = []
        self._current_mouse_pos = QPointF(0, 0)