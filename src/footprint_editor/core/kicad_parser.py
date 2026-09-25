import re
import math
from pathlib import Path
from footprint_editor.core.models import (
    Footprint, Pad, PadShape, PadType, Line, Circle, Arc, Text, TextType
)

KICAD_UNIT_MM = 0.00254


def kicad_to_mm(value):
    return float(value) * KICAD_UNIT_MM


def mm_to_kicad(value):
    return int(round(float(value) / KICAD_UNIT_MM))


def parse_kicad_mod(filepath):
    content = Path(filepath).read_text(encoding='utf-8', errors='ignore')
    return parse_kicad_content(content)


def parse_kicad_content(content):
    footprints = []
    pattern = re.compile(r'\$MODULE\s+(\S+)(.*?)\$EndMODULE', re.DOTALL)
    for match in pattern.finditer(content):
        name = match.group(1)
        body = match.group(2)
        fp = parse_module(name, body)
        footprints.append(fp)
    return footprints


def parse_module(name, body):
    fp = Footprint(name=name)

    t0_match = re.search(r'^T0\s+([^\r\n]+)', body, re.MULTILINE)
    t1_match = re.search(r'^T1\s+([^\r\n]+)', body, re.MULTILINE)

    if t0_match:
        ref_text = parse_text_line(t0_match.group(1), TextType.REFERENCE)
        ref_text.locked = True
        fp.texts.append(ref_text)
        fp.reference = ref_text.text

    if t1_match:
        val_text = parse_text_line(t1_match.group(1), TextType.VALUE)
        val_text.locked = True
        fp.texts.append(val_text)
        fp.value = val_text.text

    for ds_match in re.finditer(r'^DS\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)', body, re.MULTILINE):
        x1, y1, x2, y2, thickness = ds_match.groups()
        line = Line(
            x1=kicad_to_mm(x1), y1=kicad_to_mm(y1),
            x2=kicad_to_mm(x2), y2=kicad_to_mm(y2),
            width=kicad_to_mm(thickness)
        )
        fp.lines.append(line)

    for dc_match in re.finditer(r'^DC\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)', body, re.MULTILINE):
        xc, yc, xp, yp, thickness = dc_match.groups()
        xc_mm = kicad_to_mm(xc)
        yc_mm = kicad_to_mm(yc)
        xp_mm = kicad_to_mm(xp)
        yp_mm = kicad_to_mm(yp)
        radius = math.hypot(xp_mm - xc_mm, yp_mm - yc_mm)
        circle = Circle(
            x=xc_mm, y=yc_mm,
            radius=radius,
            width=kicad_to_mm(thickness)
        )
        fp.circles.append(circle)

    # DA cx cy sx sy angle width layer
    # (cx,cy) - центр дуги, (sx,sy) - начальная точка, angle - угол в десятых градуса
    for da_match in re.finditer(r'^DA\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)', body, re.MULTILINE):
        cx, cy, sx, sy, angle, thickness = da_match.groups()
        arc = Arc(
            cx=kicad_to_mm(cx), cy=kicad_to_mm(cy),
            sx=kicad_to_mm(sx), sy=kicad_to_mm(sy),
            angle=float(angle) / 10.0,
            width=kicad_to_mm(thickness)
        )
        fp.arcs.append(arc)

    pad_pattern = re.compile(r'\$PAD(.*?)\$EndPAD', re.DOTALL)
    for pad_match in pad_pattern.finditer(body):
        pad = parse_pad(pad_match.group(1))
        if pad:
            fp.pads.append(pad)

    return fp


def parse_text_line(text_str, text_type):
    text_match = re.search(r'"([^"]*)"', text_str)
    text = text_match.group(1) if text_match else ""

    params_str = text_str[:text_match.start()].strip() if text_match else text_str
    params = params_str.split()

    x = kicad_to_mm(params[0]) if len(params) > 0 else 0
    y = kicad_to_mm(params[1]) if len(params) > 1 else 0
    w = kicad_to_mm(params[2]) if len(params) > 2 else kicad_to_mm(400)
    h = kicad_to_mm(params[3]) if len(params) > 3 else w
    size = max(w, h) if max(w, h) > 0 else 1.0

    visible = True
    if len(params) > 7 and params[7] in ('I', 'i'):
        visible = False

    return Text(
        x=x, y=y, text=text, size=size,
        visible=visible, text_type=text_type, locked=True
    )


def parse_pad(pad_body):
    sh_match = re.search(r'Sh\s+"([^"]*)"\s+(\w+)\s+(\d+)\s+(\d+)', pad_body)
    dr_match = re.search(r'Dr\s+(\d+)', pad_body)
    po_match = re.search(r'Po\s+(-?\d+)\s+(-?\d+)', pad_body)
    at_match = re.search(r'At\s+(\w+)', pad_body)

    if not sh_match or not po_match:
        return None

    number = sh_match.group(1)
    shape_str = sh_match.group(2)
    size_x = kicad_to_mm(sh_match.group(3))
    size_y = kicad_to_mm(sh_match.group(4))
    x = kicad_to_mm(po_match.group(1))
    y = kicad_to_mm(po_match.group(2))
    drill = kicad_to_mm(dr_match.group(1)) if dr_match else 0

    shape_map = {'R': PadShape.RECT, 'C': PadShape.CIRCLE, 'O': PadShape.OVAL}
    shape = shape_map.get(shape_str, PadShape.CIRCLE)

    pad_type = PadType.SMD
    if at_match:
        attr = at_match.group(1)
        if attr in ('STD', 'NPTH'):
            pad_type = PadType.THT

    return Pad(
        number=number, shape=shape, pad_type=pad_type,
        x=x, y=y, width=size_x, height=size_y,
        drill=drill if drill > 0 else None
    )