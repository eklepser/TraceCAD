import re
import math
from pathlib import Path

from footprint_editor.core.models import (
    Footprint, Pad, PadShape, PadType, Line, Circle, Arc, Text, TextType,
    default_layers_for_pad_type,
)
from footprint_editor.kicad.units import kicad_to_mm
from footprint_editor.kicad.layers import (
    KICAD_LAYER_TO_INTERNAL, LAYER_ID_TO_INTERNAL, layer_from_id,
)


TEXT_PATTERN_SIMPLE = re.compile(
    r'^T(\d+)\s+([^\r\n"]+?)\s+"([^"]*)"',
    re.MULTILINE
)


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

    for text_match in TEXT_PATTERN_SIMPLE.finditer(body):
        idx = int(text_match.group(1))
        if idx in (0, 1):
            continue
        params = text_match.group(2).split()
        text_value = text_match.group(3)

        x = kicad_to_mm(params[0]) if len(params) > 0 else 0
        y = kicad_to_mm(params[1]) if len(params) > 1 else 0
        w = kicad_to_mm(params[2]) if len(params) > 2 else kicad_to_mm(400)
        h = kicad_to_mm(params[3]) if len(params) > 3 else w
        size = max(w, h) if max(w, h) > 0 else 1.0

        visible = 'I' not in params[4:8]

        layer = "F.SilkS"
        for tok in params:
            try:
                layer_id = int(tok)
            except ValueError:
                continue
            if layer_id in LAYER_ID_TO_INTERNAL:
                layer = layer_from_id(layer_id)
                break

        t = Text(
            x=x, y=y,
            text=text_value if text_value else "Text",
            size=size,
            visible=visible,
            text_type=TextType.NORMAL,
            layer=layer,
        )
        fp.texts.append(t)

    for ds_match in re.finditer(
        r'^DS\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)',
        body, re.MULTILINE
    ):
        x1, y1, x2, y2, thickness, layer_id = ds_match.groups()
        line = Line(
            x=kicad_to_mm(x1), y=kicad_to_mm(y1),
            x2=kicad_to_mm(x2), y2=kicad_to_mm(y2),
            width=kicad_to_mm(thickness),
            layer=layer_from_id(layer_id),
        )
        fp.lines.append(line)

    for dc_match in re.finditer(
        r'^DC\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)',
        body, re.MULTILINE
    ):
        xc, yc, xp, yp, thickness, layer_id = dc_match.groups()
        xc_mm = kicad_to_mm(xc)
        yc_mm = kicad_to_mm(yc)
        xp_mm = kicad_to_mm(xp)
        yp_mm = kicad_to_mm(yp)
        radius = math.hypot(xp_mm - xc_mm, yp_mm - yc_mm)
        circle = Circle(
            x=xc_mm, y=yc_mm,
            radius=radius,
            width=kicad_to_mm(thickness),
            layer=layer_from_id(layer_id),
        )
        fp.circles.append(circle)

    for da_match in re.finditer(
        r'^DA\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)',
        body, re.MULTILINE
    ):
        cx, cy, sx, sy, angle, thickness, layer_id = da_match.groups()
        arc = Arc(
            x=kicad_to_mm(cx), y=kicad_to_mm(cy),
            sx=kicad_to_mm(sx), sy=kicad_to_mm(sy),
            angle=float(angle) / 10.0,
            width=kicad_to_mm(thickness),
            layer=layer_from_id(layer_id),
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

    visible = 'I' not in params[4:8]

    layer = "F.SilkS"
    for tok in params:
        try:
            layer_id = int(tok)
        except ValueError:
            continue
        if layer_id in LAYER_ID_TO_INTERNAL:
            layer = layer_from_id(layer_id)
            break

    return Text(
        x=x, y=y, text=text, size=size,
        visible=visible, text_type=text_type, locked=True,
        layer=layer,
    )


def parse_pad(pad_body):
    sh_match = re.search(r'Sh\s+"([^"]*)"\s+(\w+)\s+(\d+)\s+(\d+)', pad_body)
    dr_match = re.search(r'Dr\s+(\d+)', pad_body)
    po_match = re.search(r'Po\s+(-?\d+)\s+(-?\d+)', pad_body)
    at_match = re.search(r'At\s+(\w+)', pad_body)
    la_match = re.search(r'^La\s+([^\r\n]+)', pad_body, re.MULTILINE)

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

    pad_type = PadType.STANDARD
    if at_match:
        attr = at_match.group(1)
        if attr == 'SMD':
            pad_type = PadType.SMD
        elif attr == 'CONN':
            pad_type = PadType.CONN
        else:
            pad_type = PadType.STANDARD

    layers = []
    if la_match:
        for token in la_match.group(1).split():
            internal = KICAD_LAYER_TO_INTERNAL.get(token)
            if internal and internal not in layers:
                layers.append(internal)

    if not layers:
        layers = default_layers_for_pad_type(pad_type)

    return Pad(
        x=x, y=y,
        number=number, shape=shape, pad_type=pad_type,
        width=size_x, height=size_y,
        drill=drill if drill > 0 else None,
        layers=layers,
    )