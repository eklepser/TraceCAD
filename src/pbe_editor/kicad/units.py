KICAD_UNIT_MM = 0.00254


def kicad_to_mm(value):
    return float(value) * KICAD_UNIT_MM


def mm_to_kicad(value):
    return int(round(float(value) / KICAD_UNIT_MM))