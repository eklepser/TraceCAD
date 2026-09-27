VK_W = 0x57
VK_A = 0x41
VK_S = 0x53
VK_D = 0x44

VK_ESCAPE = 0x1B
VK_DELETE = 0x2E
VK_F1 = 0x70
VK_F2 = 0x71
VK_F3 = 0x72
VK_F11 = 0x7A
VK_C = 0x43
VK_V = 0x56
VK_R = 0x52
VK_Y = 0x59
VK_Z = 0x5A
VK_1 = 0x31
VK_2 = 0x32
VK_3 = 0x33
VK_4 = 0x34
VK_5 = 0x35

PAN_KEYS = (VK_W, VK_A, VK_S, VK_D)


class Tool:
    SELECT = "select"
    ADD_PAD = "add_pad"
    ADD_LINE = "add_line"
    ADD_CIRCLE = "add_circle"
    ADD_ARC = "add_arc"
    ADD_TEXT = "add_text"


class Colors:
    GRID = (80, 80, 80)
    BACKGROUND = (30, 30, 30)
    PAD = (180, 160, 80)
    SELECTED = (0, 150, 255)
    AXIS = (255, 100, 100, 150)
    GHOST_LINE = (100, 200, 100, 255)
    SNAP_CROSS = (255, 255, 255, 150)
    TEXT_VISIBLE = (200, 200, 200)
    TEXT_HIDDEN = (200, 200, 200, 50)
    PAD_NUMBER = (255, 255, 255)
    GHOST_TEXT = (150, 150, 150, 180)
    REFERENCE = (100, 200, 100)
    VALUE = (200, 100, 100)


class Sizes:
    BASE_SCALE = 50.0
    PAN_SPEED_PX = 15.0
    PAN_TIMER_INTERVAL = 16
    CROSS_SIZE = 8.0
    MAX_GRID_POINTS = 150
    MIN_CELL_PX = 2.0
    TEXT_FONT_MULTIPLIER = 1.415
    PAD_NUMBER_FONT_RATIO = 0.2
    DEFAULT_LINE_WIDTH = 0.381


class Steps:
    ZOOM = [0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
    GRID_1X = [
        "5.000", "2.500", "2.000", "1.000",
        "0.500", "0.250", "0.200", "0.100",
        "0.050", "0.025", "0.010",
    ]
    GRID_127X = [
        "5.080", "2.540", "1.270", "0.635",
        "0.508", "0.254", "0.127", "0.0508",
    ]
    DEFAULT_GRID = "1.000"


class Styles:
    DIALOG_BG = ""
    INPUT_BG = ""
    BUTTON_OK = ""
    BUTTON_CANCEL = ""
    BUTTON_DISABLED = ""
    LOG_LABEL = ""
    RIGHT_PANEL = ""
    APPLY_BUTTON = ""
    RESET_BUTTON = ""
    TOOL_BUTTON_ACTIVE = ""
    TOOL_BUTTON_INACTIVE = ""
    LIST_BG = ""
    TOOLTIP = ""
    MAIN_WINDOW = ""
    SECTION_LABEL = ""
    OBJECT_TITLE = ""
    AUX_BAR = ""


DARK_COLORS = {
    "GRID": (80, 80, 80),
    "BACKGROUND": (30, 30, 30),
    "PAD": (180, 160, 80),
    "SELECTED": (0, 150, 255),
    "AXIS": (255, 100, 100, 150),
    "GHOST_LINE": (100, 200, 100, 255),
    "SNAP_CROSS": (255, 255, 255, 150),
    "TEXT_VISIBLE": (200, 200, 200),
    "TEXT_HIDDEN": (200, 200, 200, 50),
    "PAD_NUMBER": (255, 255, 255),
    "GHOST_TEXT": (150, 150, 150, 180),
    "REFERENCE": (100, 200, 100),
    "VALUE": (200, 100, 100),
}

DARK_STYLES = {
    "DIALOG_BG": (
        "QDialog { background-color: #2b2b2b; color: #d8d8d8; }"
        "QLabel { color: #d8d8d8; }"
        "QLineEdit, QDoubleSpinBox {"
        "  background-color: #3c3f41; color: #ffffff;"
        "  border: 1px solid #555555; padding: 5px; }"
        "QLineEdit:focus, QDoubleSpinBox:focus { border: 1px solid #365880; }"
        "QCheckBox { color: #d8d8d8; spacing: 6px; }"
    ),
    "INPUT_BG": (
        "background-color: #3c3f41; color: #ffffff;"
        "border: 1px solid #555555; padding: 5px;"
    ),
    "BUTTON_OK": "background-color: #365880; color: white; border: none; padding: 5px 14px;",
    "BUTTON_CANCEL": "background-color: #555555; color: white; border: none; padding: 5px 14px;",
    "BUTTON_DISABLED": "background-color: #3a3a3a; color: #707070; border: none; padding: 5px 14px;",
    "LOG_LABEL": "background-color: rgba(40, 40, 40, 220); color: #a9b7c6; padding: 5px; border-radius: 3px;",
    "RIGHT_PANEL": "background-color: #3c3f41; color: white;",
    "APPLY_BUTTON": "background-color: #365880; color: white; padding: 5px; border: none;",
    "RESET_BUTTON": "background-color: #555555; color: white; padding: 5px; border: none;",
    "TOOL_BUTTON_ACTIVE": (
        "QPushButton { font-size: 18px; border: 2px solid #0096ff;"
        " background-color: #365880; color: white; }"
        " QPushButton:hover { background-color: #2a4a6b; }"
    ),
    "TOOL_BUTTON_INACTIVE": (
        "QPushButton { font-size: 18px; border: 2px solid transparent;"
        " background-color: #3c3f41; color: white; }"
        " QPushButton:hover { background-color: #2a4a6b; }"
    ),
    "LIST_BG": (
        "QListWidget { background-color: #2b2b2b; color: #a9b7c6;"
        " border: 1px solid #555555; }"
        " QListWidget::item { padding: 3px 6px; }"
        " QListWidget::item:selected { background-color: #365880; color: white; }"
        " QListWidget::item:hover { background-color: #3c3f41; }"
    ),
    "TOOLTIP": "QToolTip { font-size: 10px; background-color: #2b2b2b; color: #a9b7c6; border: 1px solid #555555; padding: 2px; }",
    "MAIN_WINDOW": (
        "QMainWindow { background-color: #3c3f41; }"
        "QDockWidget { background-color: #3c3f41; color: #a9b7c6; }"
        "QMenuBar { background-color: #2b2b2b; color: #a9b7c6; }"
        "QMenuBar::item { padding: 6px 10px; background: transparent; }"
        "QMenuBar::item:selected { background-color: #365880; }"
        "QMenu { background-color: #2b2b2b; color: #a9b7c6; }"
        "QMenu::item { padding: 4px 20px; }"
        "QMenu::item:selected { background-color: #365880; }"
        "QStatusBar { background-color: #2b2b2b; color: #a9b7c6; }"
        "QToolBar { background-color: #2b2b2b; color: #a9b7c6; padding: 0px; spacing: 4px; }"
        "QGroupBox { color: #a9b7c6; border: 1px solid #555555; margin-top: 8px; padding-top: 6px; }"
        "QGroupBox::title { subcontrol-origin: margin; left: 8px; }"
        "QLabel { color: #a9b7c6; }"
        "QComboBox { background-color: #3c3f41; color: white;"
        " border: 1px solid #555555; padding: 3px 8px; min-height: 20px; }"
        "QComboBox::drop-down { border: none; width: 18px; }"
        "QComboBox QAbstractItemView { background-color: #2b2b2b;"
        " color: #a9b7c6; selection-background-color: #365880; }"
    ),
    "SECTION_LABEL": "color: #a9b7c6; font-weight: bold; padding: 2px 0px;",
    "OBJECT_TITLE": "color: #7a9cc6; font-weight: bold; font-size: 10pt; padding: 2px 0px;",
    "AUX_BAR": (
        "QWidget#AuxBar { background-color: #2b2b2b;"
        " border-top: 1px solid #1e1e1e; }"
    ),
}


def apply_theme():
    for k, v in DARK_COLORS.items():
        setattr(Colors, k, v)
    for k, v in DARK_STYLES.items():
        setattr(Styles, k, v)


apply_theme()