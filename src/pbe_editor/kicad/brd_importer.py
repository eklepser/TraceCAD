import re
import math
from pathlib import Path
from typing import Dict, List, Optional

from footprint_editor.core.models import (
    Footprint, Pad, PadShape, PadType, Line, Circle, Arc, Text, TextType,
    default_layers_for_pad_type,
)
from footprint_editor.kicad.units import kicad_to_mm
from footprint_editor.kicad.layers import (
    KICAD_LAYER_TO_INTERNAL, LAYER_ID_TO_INTERNAL, layer_from_id,
)
from pbe_editor.core.board_models import Board, BoardModule, PadNet, Net


def parse_brd(filepath: str) -> Board:
    content = Path(filepath).read_text(encoding='utf-8', errors='ignore')
    return parse_brd_content(content)


def parse_brd_content(content: str) -> Board:
    board = Board()
    board.filename = None

    nets_section = re.findall(
        r'\$EQUIPOT\s+Na\s+(\d+)\s+"([^"]*)"',
        content
    )
    for code_str, name in nets_section:
        code = int(code_str)
        if code > 0:
            board.nets[code] = Net(code=code, name=name)

    modules = re.findall(r'\$MODULE\s+(\S+)(.*?)\$EndMODULE', content, re.DOTALL)
    next_uid = 1

    for name, body in modules:
        module = parse_module(name, body, next_uid)
        if module is None:
            continue
        next_uid += 1
        board.modules.append(module)

    return board


def parse_module(name: str, body: str, uid: int) -> Optional[BoardModule]:
    po_match = re.search(
        r'^Po\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)',
        body, re.MULTILINE
    )
    if not po_match:
        return None

    x = kicad_to_mm(po_match.group(1))
    y = kicad_to_mm(po_match.group(2))
    angle = float(po_match.group(3)) / 10.0

    fp = Footprint(name=name)

    reference = "REF**"
    value = "VAL**"

    t0_match = re.search(r'^T0\s+([^\r\n]+)', body, re.MULTILINE)
    t1_match = re.search(r'^T1\s+([^\r\n]+)', body, re.MULTILINE)

    if t0_match:
        ref_text = _parse_text_line(t0_match.group(1), TextType.REFERENCE)
        ref_text.locked = True
        fp.texts.append(ref_text)
        reference = ref_text.text
        fp.reference = reference

    if t1_match:
        val_text = _parse_text_line(t1_match.group(1), TextType.VALUE)
        val_text.locked = True
        fp.texts.append(val_text)
        value = val_text.text
        fp.value = value

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
        cx, cy, sx, sy, angle_a, thickness, layer_id = da_match.groups()
        arc = Arc(
            x=kicad_to_mm(cx), y=kicad_to_mm(cy),
            sx=kicad_to_mm(sx), sy=kicad_to_mm(sy),
            angle=float(angle_a) / 10.0,
            width=kicad_to_mm(thickness),
            layer=layer_from_id(layer_id),
        )
        fp.arcs.append(arc)

    module = BoardModule(
        footprint=fp,
        reference=reference,
        value=value,
        x=x, y=y, angle=angle,
        layer="F.Cu",
        uid=uid,
    )

    pad_pattern = re.compile(r'\$PAD(.*?)\$EndPAD', re.DOTALL)
    for pad_match in pad_pattern.finditer(body):
        pad, pad_net = _parse_pad(pad_match.group(1))
        if pad is not None:
            fp.pads.append(pad)
            if pad_net is not None:
                module.pad_nets[pad.number] = pad_net

    return module


def _parse_text_line(text_str: str, text_type: TextType) -> Text:
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


def _parse_pad(pad_body: str):
    sh_match = re.search(r'Sh\s+"([^"]*)"\s+(\w+)\s+(\d+)\s+(\d+)', pad_body)
    dr_match = re.search(r'Dr\s+(\d+)', pad_body)
    po_match = re.search(r'Po\s+(-?\d+)\s+(-?\d+)', pad_body)
    at_match = re.search(r'At\s+(\w+)', pad_body)
    ne_match = re.search(r'^Ne\s+(\d+)\s+"([^"]*)"', pad_body, re.MULTILINE)

    if not sh_match or not po_match:
        return None, None

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

    pad = Pad(
        x=x, y=y,
        number=number, shape=shape, pad_type=pad_type,
        width=size_x, height=size_y,
        drill=drill if drill > 0 else None,
        layers=default_layers_for_pad_type(pad_type),
    )

    pad_net = None
    if ne_match:
        code = int(ne_match.group(1))
        name = ne_match.group(2)
        if code > 0 and name:
            pad_net = PadNet(pad_number=number, net_code=code, net_name=name)

    return pad, pad_net