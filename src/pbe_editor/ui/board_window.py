from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QPointF

from constants import apply_theme
from pbe_editor.core.board_models import Board
from constants.board_settings import DEFAULT_LINE_LAYER
from pbe_editor.ui.commands import CommandHandler
from pbe_editor.ui.panels.drawing_tool_bar import BoardTool
from pbe_editor.ui.window import (
    SessionService, HistoryService, GridService, StatusService,
    KeyboardService, ToolsService, BoardFilesService, BoardStateService,
    ModuleListService, LibrariesService, UiSetupService,
)


class BoardEditorWindow(
    SessionService, HistoryService, GridService, StatusService,
    KeyboardService, ToolsService, BoardFilesService, BoardStateService,
    ModuleListService, LibrariesService, UiSetupService,
    QMainWindow,
):
    def __init__(self):
        super().__init__()

        self._init_session()
        apply_theme()

        self.board = Board()
        self.library_paths = []
        self.library_modules = {}
        self.current_library_path = None

        self._line_layer = DEFAULT_LINE_LAYER
        self._selected_footprint = None

        self.grid_mode = self._load_grid_mode()

        self.current_tool = BoardTool.SELECT
        self._line_start = None
        self._circle_center_point = None
        self._arc_center_point = None
        self._arc_start_point = None
        self._text_position = None
        self._net_start = None

        self._current_mouse_pos = QPointF(0, 0)

        self._modified = False
        self._undo_stack = []
        self._redo_stack = []
        self._current_snapshot = None

        self.setWindowTitle("TraceCad PBE")
        self.resize(1200, 800)

        self._apply_startup_geometry()

        self.commands = CommandHandler(self)

        self.init_canvas()
        self.init_toolbars()
        self.init_menu()
        self.init_docks()
        self.init_statusbar()
        self.installEventFilter(self)
        self.apply_theme()
        self.wire_panels()

        self.load_library_paths()
        self.refresh_library_modules()
        self.refresh_module_list()
        self.apply_grid_series(self.grid_mode, initial=True)

        self.set_tool(BoardTool.SELECT)

        self._restore_last_board()