KICAD_LAYER_TO_INTERNAL = {
    "F.Cu": "F.Cu", "B.Cu": "B.Cu", "*.Cu": "F.Cu",
    "F.SilkS": "F.SilkS", "B.SilkS": "B.SilkS",
    "F.Mask": "F.Mask", "B.Mask": "B.Mask",
    "F.Paste": "F.Paste", "B.Paste": "B.Paste",
    "F.Adhes": "F.Adhes", "B.Adhes": "B.Adhes",
    "Dwgs.User": "Dwgs.User",
    "Cmts.User": "Cmts.User",
    "Eco1.User": "Eco1.User", "Eco2.User": "Eco2.User",
    "Edge.Cuts": "Edge.Cuts",
}

INTERNAL_TO_KICAD_LAYER = {
    "F.Cu": "F.Cu", "B.Cu": "B.Cu",
    "F.SilkS": "F.SilkS", "B.SilkS": "B.SilkS",
    "F.Mask": "F.Mask", "B.Mask": "B.Mask",
    "F.Paste": "F.Paste", "B.Paste": "B.Paste",
    "F.Adhes": "F.Adhes", "B.Adhes": "B.Adhes",
    "Dwgs.User": "Dwgs.User",
    "Cmts.User": "Cmts.User",
    "Eco1.User": "Eco1.User", "Eco2.User": "Eco2.User",
    "Edge.Cuts": "Edge.Cuts",
}

LAYER_ID = {
    "B.Cu": 0,
    "F.Cu": 15,
    "B.Paste": 16,
    "F.Paste": 17,
    "B.Mask": 18,
    "F.Mask": 19,
    "B.SilkS": 20,
    "F.SilkS": 21,
    "F.Adhes": 22,
    "B.Adhes": 23,
    "Dwgs.User": 24,
    "Cmts.User": 40,
    "Eco1.User": 41,
    "Eco2.User": 42,
}

LAYER_ID_TO_INTERNAL = {
    0: "B.Cu",
    15: "F.Cu",
    16: "B.Paste",
    17: "F.Paste",
    18: "B.Mask",
    19: "F.Mask",
    20: "B.SilkS",
    21: "F.SilkS",
    22: "F.Adhes",
    23: "B.Adhes",
    24: "Dwgs.User",
    40: "Cmts.User",
    41: "Eco1.User",
    42: "Eco2.User",
}

DRAWSEG_LAYER_ID = {
    "B.Cu": 0,
    "F.Cu": 15,
    "B.Adhes": 16,
    "F.Adhes": 17,
    "B.Paste": 18,
    "F.Paste": 19,
    "B.SilkS": 20,
    "F.SilkS": 21,
    "B.Mask": 22,
    "F.Mask": 23,
    "Dwgs.User": 24,
    "Cmts.User": 25,
    "Eco1.User": 26,
    "Eco2.User": 27,
    "Edge.Cuts": 28,
}

DRAWSEG_LAYER_ID_TO_INTERNAL = {
    0: "B.Cu",
    15: "F.Cu",
    16: "B.Adhes",
    17: "F.Adhes",
    18: "B.Paste",
    19: "F.Paste",
    20: "B.SilkS",
    21: "F.SilkS",
    22: "B.Mask",
    23: "F.Mask",
    24: "Dwgs.User",
    25: "Cmts.User",
    26: "Eco1.User",
    27: "Eco2.User",
    28: "Edge.Cuts",
}


def layer_from_id(layer_id):
    try:
        lid = int(layer_id)
    except (TypeError, ValueError):
        return "F.SilkS"
    return LAYER_ID_TO_INTERNAL.get(lid, "F.SilkS")


def layer_to_id(layer):
    return LAYER_ID.get(layer, 40)


def drawseg_layer_from_id(layer_id):
    try:
        lid = int(layer_id)
    except (TypeError, ValueError):
        return "Edge.Cuts"
    return DRAWSEG_LAYER_ID_TO_INTERNAL.get(lid, "Edge.Cuts")


def drawseg_layer_to_id(layer):
    return DRAWSEG_LAYER_ID.get(layer, 28)