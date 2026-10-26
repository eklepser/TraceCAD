KICAD_LAYER_TO_INTERNAL = {
    "F.Cu": "F.Cu", "B.Cu": "B.Cu", "*.Cu": "F.Cu",
    "F.SilkS": "F.SilkS", "B.SilkS": "B.SilkS",
    "F.Mask": "F.Mask", "B.Mask": "B.Mask",
    "F.Paste": "F.Paste", "B.Paste": "B.Paste",
    "F.Adhes": "F.Adhes", "B.Adhes": "B.Adhes",
    "Edge.Cuts": "Edge.Cuts",
    "Cmts.User": "Cmts.User",
    "Eco1.User": "Eco1.User", "Eco2.User": "Eco2.User",
}

INTERNAL_TO_KICAD_LAYER = {
    "F.Cu": "F.Cu", "B.Cu": "B.Cu",
    "F.SilkS": "F.SilkS", "B.SilkS": "B.SilkS",
    "F.Mask": "F.Mask", "B.Mask": "B.Mask",
    "F.Paste": "F.Paste", "B.Paste": "B.Paste",
    "F.Adhes": "F.Adhes", "B.Adhes": "B.Adhes",
    "Edge.Cuts": "Edge.Cuts",
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
    "B.Adhes": 22,
    "F.Adhes": 23,
    "Edge.Cuts": 28,
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
    22: "B.Adhes",
    23: "F.Adhes",
    24: "B.Paste",
    25: "F.Mask",
    26: "B.Mask",
    27: "B.SilkS",
    28: "Edge.Cuts",
    29: "F.SilkS",
    40: "Cmts.User",
    41: "Eco1.User",
    42: "Eco2.User",
}


def layer_from_id(layer_id):
    try:
        lid = int(layer_id)
    except (TypeError, ValueError):
        print(f"[layer_from_id] неверный id: {layer_id!r}, fallback=Edge.Cuts")
        return "Edge.Cuts"
    if lid not in LAYER_ID_TO_INTERNAL:
        print(f"[layer_from_id] id {lid} НЕ НАЙДЕН в словаре, fallback=Edge.Cuts")
        return "Edge.Cuts"
    name = LAYER_ID_TO_INTERNAL[lid]
    print(f"[layer_from_id] id={lid} -> {name}")
    return name


def layer_to_id(layer):
    lid = LAYER_ID.get(layer)
    if lid is None:
        print(f"[layer_to_id] слой {layer!r} не найден, fallback=28 (Edge.Cuts)")
        return 28
    return lid