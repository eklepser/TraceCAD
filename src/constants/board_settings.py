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

LAYER_NAMES_RU = {
    "F.Cu":      "Front",
    "B.Cu":      "Back",
    "F.Adhes":   "Adhes_Front",
    "B.Adhes":   "Adhes_Back",
    "F.Paste":   "SoldP_Front",
    "B.Paste":   "SoldP_Back",
    "F.SilkS":   "SilkS_Front",
    "B.SilkS":   "SilkS_Back",
    "F.Mask":    "Mask_Front",
    "B.Mask":    "Mask_Back",
    "Dwgs.User": "Чертёж",
    "Cmts.User": "Комментарии",
    "Eco1.User": "Eco1",
    "Eco2.User": "Eco2",
    "Edge.Cuts": "Контур платы",
}

DRAWABLE_LAYERS = [
    ("F.Adhes",   (200, 100, 200)),
    ("B.Adhes",   (150,  80, 150)),
    ("F.Paste",   (200,  80, 200)),
    ("B.Paste",   ( 80, 200, 200)),
    ("F.SilkS",   ( 80, 160, 160)),
    ("B.SilkS",   (200, 100, 200)),
    ("F.Mask",    (200,  80, 200)),
    ("B.Mask",    (160, 160,  60)),
    ("Dwgs.User", (220, 220, 220)),
    ("Cmts.User", (200, 200, 200)),
    ("Eco1.User", ( 80,  80, 200)),
    ("Eco2.User", (120, 220, 120)),
    ("Edge.Cuts", (255, 255,  80)),
]

LAYER_COLORS = {name: color for name, color in DRAWABLE_LAYERS}

DEFAULT_LINE_LAYER = "Edge.Cuts"
DEFAULT_LINE_WIDTH = 0.381