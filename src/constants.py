VK_W = 0x57
VK_A = 0x41
VK_S = 0x53
VK_D = 0x44

VK_ESCAPE = 0x1B
VK_DELETE = 0x2E
VK_F1 = 0x70
VK_F2 = 0x71
VK_C = 0x43
VK_V = 0x56
VK_R = 0x52

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


class Steps:
    ZOOM = [0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
    GRID = [
        "5.000", "2.540", "2.500", "1.270", "1.000",
        "0.635", "0.500", "0.254", "0.250", "0.200",
        "0.127", "0.100", "0.050", "0.025", "0.010",
    ]
    DEFAULT_GRID = "1.000"


class Styles:
    DIALOG_BG = ""
    INPUT_BG = ""
    BUTTON_OK = ""
    BUTTON_CANCEL = ""
    LOG_LABEL = ""
    RIGHT_PANEL = ""
    APPLY_BUTTON = ""
    TOOL_BUTTON = ""
    TOOL_BUTTON_ACTIVE = ""
    TOOL_BUTTON_INACTIVE = ""
    LIST_BG = ""
    TOOLTIP = ""
    MAIN_WINDOW = ""


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

LIGHT_COLORS = {
    "GRID": (210, 210, 210),
    "BACKGROUND": (248, 248, 248),
    "PAD": (200, 170, 70),
    "SELECTED": (0, 100, 220),
    "AXIS": (200, 60, 60, 200),
    "GHOST_LINE": (40, 140, 40, 255),
    "SNAP_CROSS": (0, 0, 0, 180),
    "TEXT_VISIBLE": (30, 30, 30),
    "TEXT_HIDDEN": (30, 30, 30, 60),
    "PAD_NUMBER": (0, 0, 0),
    "GHOST_TEXT": (80, 80, 80, 180),
    "REFERENCE": (0, 130, 0),
    "VALUE": (180, 30, 30),
}

DARK_STYLES = {
    "DIALOG_BG": "background-color: #2b2b2b; color: #a9b7c6; border: 1px solid #555555;",
    "INPUT_BG": "background-color: #3c3f41; color: white; border: 1px solid #555555; padding: 5px;",
    "BUTTON_OK": "background-color: #365880; color: white; border: none; padding: 4px 8px;",
    "BUTTON_CANCEL": "background-color: #555555; color: white; border: none; padding: 4px 8px;",
    "LOG_LABEL": "background-color: rgba(40, 40, 40, 220); color: #a9b7c6; padding: 5px; border-radius: 3px;",
    "RIGHT_PANEL": "background-color: #3c3f41; color: white;",
    "APPLY_BUTTON": "background-color: #365880; color: white; padding: 5px;",
    "TOOL_BUTTON": "font-size: 20px; border: 2px solid transparent;",
    "TOOL_BUTTON_ACTIVE": "font-size: 20px; border: 2px solid #0096ff; background-color: #2a4d6e; color: white;",
    "TOOL_BUTTON_INACTIVE": "font-size: 20px; border: 2px solid transparent; background-color: #3c3f41; color: white;",
    "LIST_BG": "background-color: #2b2b2b; color: #a9b7c6;",
    "TOOLTIP": "QToolTip { font-size: 10px; background-color: #2b2b2b; color: #a9b7c6; border: 1px solid #555555; padding: 2px; }",
    "MAIN_WINDOW": (
        "QMainWindow { background-color: #3c3f41; }"
        "QDockWidget { background-color: #3c3f41; color: #a9b7c6; }"
        "QMenuBar { background-color: #2b2b2b; color: #a9b7c6; }"
        "QMenuBar::item:selected { background-color: #365880; }"
        "QMenu { background-color: #2b2b2b; color: #a9b7c6; }"
        "QMenu::item:selected { background-color: #365880; }"
        "QStatusBar { background-color: #2b2b2b; color: #a9b7c6; }"
        "QToolBar { background-color: #2b2b2b; color: #a9b7c6; }"
        "QGroupBox { color: #a9b7c6; border: 1px solid #555555; margin-top: 8px; padding-top: 6px; }"
        "QGroupBox::title { subcontrol-origin: margin; left: 8px; }"
        "QLabel { color: #a9b7c6; }"
    ),
}

LIGHT_STYLES = {
    "DIALOG_BG": "background-color: #f4f4f4; color: #202020; border: 1px solid #c0c0c0;",
    "INPUT_BG": "background-color: #ffffff; color: #202020; border: 1px solid #c0c0c0; padding: 5px;",
    "BUTTON_OK": "background-color: #4a90d9; color: white; border: none; padding: 4px 8px;",
    "BUTTON_CANCEL": "background-color: #c0c0c0; color: #202020; border: none; padding: 4px 8px;",
    "LOG_LABEL": "background-color: rgba(240, 240, 240, 220); color: #202020; padding: 5px; border-radius: 3px;",
    "RIGHT_PANEL": "background-color: #f4f4f4; color: #202020;",
    "APPLY_BUTTON": "background-color: #4a90d9; color: white; padding: 5px;",
    "TOOL_BUTTON": "font-size: 20px; border: 2px solid transparent;",
    "TOOL_BUTTON_ACTIVE": "font-size: 20px; border: 2px solid #4a90d9; background-color: #d0e4f5; color: #202020;",
    "TOOL_BUTTON_INACTIVE": "font-size: 20px; border: 2px solid transparent; background-color: #e6e6e6; color: #202020;",
    "LIST_BG": "background-color: #ffffff; color: #202020;",
    "TOOLTIP": "QToolTip { font-size: 10px; background-color: #f4f4f4; color: #202020; border: 1px solid #c0c0c0; padding: 2px; }",
    "MAIN_WINDOW": (
        "QMainWindow { background-color: #f4f4f4; }"
        "QDockWidget { background-color: #f4f4f4; color: #202020; }"
        "QMenuBar { background-color: #e6e6e6; color: #202020; }"
        "QMenuBar::item:selected { background-color: #d0e4f5; }"
        "QMenu { background-color: #f4f4f4; color: #202020; }"
        "QMenu::item:selected { background-color: #4a90d9; color: white; }"
        "QStatusBar { background-color: #e6e6e6; color: #202020; }"
        "QToolBar { background-color: #e6e6e6; color: #202020; }"
        "QGroupBox { color: #202020; border: 1px solid #c0c0c0; margin-top: 8px; padding-top: 6px; }"
        "QGroupBox::title { subcontrol-origin: margin; left: 8px; }"
        "QLabel { color: #202020; }"
    ),
}


def apply_theme(theme_name):
    if theme_name == "light":
        colors = LIGHT_COLORS
        styles = LIGHT_STYLES
    else:
        colors = DARK_COLORS
        styles = DARK_STYLES

    for k, v in colors.items():
        setattr(Colors, k, v)
    for k, v in styles.items():
        setattr(Styles, k, v)


apply_theme("dark")