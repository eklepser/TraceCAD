KICAD_LAYER_TO_INTERNAL = {
    "F.Cu": "F.Cu", "B.Cu": "B.Cu", "*.Cu": "F.Cu",
    "F.SilkS": "F.SilkS", "B.SilkS": "B.SilkS",
    "F.Mask": "F.Mask", "B.Mask": "B.Mask",
    "F.Paste": "F.Paste", "B.Paste": "B.Paste",
    "F.Adhes": "F.Adhes", "B.Adhes": "B.Adhes",
    "Cmts.User": "Cmts.User",
    "Eco1.User": "Eco1.User", "Eco2.User": "Eco2.User",
}

INTERNAL_TO_KICAD_LAYER = {
    "F.Cu": "F.Cu", "B.Cu": "B.Cu",
    "F.SilkS": "F.SilkS", "B.SilkS": "B.SilkS",
    "F.Mask": "F.Mask", "B.Mask": "B.Mask",
    "F.Paste": "F.Paste", "B.Paste": "B.Paste",
    "F.Adhes": "F.Adhes", "B.Adhes": "B.Adhes",
    "Cmts.User": "Cmts.User",
    "Eco1.User": "Eco1.User", "Eco2.User": "Eco2.User",
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
    "Cmts.User": 40,
    "Eco1.User": 41,
    "Eco2.User": 42,
}

LAYER_ID_TO_INTERNAL = {v: k for k, v in LAYER_ID.items()}


def layer_from_id(layer_id):
    return LAYER_ID_TO_INTERNAL.get(int(layer_id), "F.SilkS")


def layer_to_id(layer):
    return LAYER_ID.get(layer, 21)