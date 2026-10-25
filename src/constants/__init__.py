from constants.keys import (
    VK_W, VK_A, VK_S, VK_D,
    VK_ESCAPE, VK_DELETE,
    VK_F1, VK_F2, VK_F3, VK_F11,
    VK_C, VK_V, VK_R, VK_Y, VK_Z, VK_G, VK_L,
    VK_1, VK_2, VK_3, VK_4, VK_5,
    PAN_KEYS,
)
from constants.tools import Tool
from constants.colors import Colors, DARK_COLORS
from constants.sizes import Sizes
from constants.grid import Steps, GRID_SERIES, GRID_SERIES_LABEL
from constants.settings import (
    SETTINGS_ORG, SETTINGS_APP,
    SETTINGS_KEY_LIBS, SETTINGS_KEY_GRID_MODE,
    SETTINGS_KEY_LAST_LIB, SETTINGS_KEY_LAST_MODULE,
    LEFT_PANEL_MIN_WIDTH, LEFT_PANEL_MAX_WIDTH,
    RIGHT_PANEL_MIN_WIDTH, RIGHT_PANEL_MAX_WIDTH,
)
from constants.styles import Styles, DARK_STYLES


def apply_theme():
    for k, v in DARK_COLORS.items():
        setattr(Colors, k, v)
    for k, v in DARK_STYLES.items():
        setattr(Styles, k, v)


apply_theme()