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

PAN_KEYS = (VK_W, VK_A, VK_S, VK_D)

class Tool:
    SELECT = "select"
    ADD_PAD = "add_pad"
    ADD_LINE = "add_line"
    ADD_CIRCLE = "add_circle"
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
    GRID = ["5.000", "2.500", "1.000", "0.500", "0.250", "0.200", "0.100", "0.050", "0.025", "0.010"]
    DEFAULT_GRID = "1.000"

class Styles:
    DIALOG_BG = "background-color: #2b2b2b; color: #a9b7c6; border: 1px solid #555555;"
    INPUT_BG = "background-color: #3c3f41; color: white; border: 1px solid #555555; padding: 5px;"
    BUTTON_OK = "background-color: #365880; color: white; border: none;"
    BUTTON_CANCEL = "background-color: #555555; color: white; border: none;"
    LOG_LABEL = "background-color: rgba(40, 40, 40, 220); color: #a9b7c6; padding: 5px; border-radius: 3px;"
    RIGHT_PANEL = "background-color: #3c3f41; color: white;"
    APPLY_BUTTON = "background-color: #365880; color: white; padding: 5px;"
    TOOL_BUTTON = "font-size: 20px; border: 2px solid transparent;"
    TOOL_BUTTON_ACTIVE = "font-size: 20px; border: 2px solid #0096ff; background-color: #2a4d6e;"
    TOOL_BUTTON_INACTIVE = "font-size: 20px; border: 2px solid transparent; background-color: #3c3f41;"