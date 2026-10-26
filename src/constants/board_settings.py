SETTINGS_KEY_BRD_LIBS = "brd_library_paths"
SETTINGS_KEY_BRD_LAST = "brd_last_file"

BOARD_UNIT_INCH = 0.000100
BOARD_LAYER_COUNT = 2
BOARD_THICKNESS = 630
BOARD_TRACK_WIDTH = 80
BOARD_TRACK_MIN_WIDTH = 80
BOARD_TRACK_CLEARANCE = 100
BOARD_VIA_SIZE = 350
BOARD_VIA_DRILL = 250
BOARD_TEXT_WIDTH = 120
BOARD_TEXT_SIZE = 600
BOARD_PAD_SIZE = 600
BOARD_PAD_DRILL = 320
BOARD_PAGE_WIDTH = 11700
BOARD_PAGE_HEIGHT = 8267

KICAD_EDGE_CUTS_LAYER_ID = 28

DRAWABLE_LAYERS = [
    ("F.Cu",      (200,  60,  60)),
    ("B.Cu",      ( 60, 140,  60)),
    ("F.Adhes",   (200, 100, 200)),
    ("B.Adhes",   (150,  80, 150)),
    ("F.Paste",   (200, 200, 200)),
    ("B.Paste",   (160, 160, 160)),
    ("F.SilkS",   (240, 240, 240)),
    ("B.SilkS",   (140, 200, 255)),
    ("F.Mask",    (200,  80, 200)),
    ("B.Mask",    (160, 160,  60)),
    ("Cmts.User", (180, 180, 180)),
    ("Eco1.User", (120, 220, 120)),
    ("Eco2.User", (255, 170,  80)),
    ("Edge.Cuts", (255, 220,  80)),
]

LAYER_COLORS = {name: color for name, color in DRAWABLE_LAYERS}

DEFAULT_LINE_LAYER = "Edge.Cuts"
DEFAULT_LINE_WIDTH = 0.15