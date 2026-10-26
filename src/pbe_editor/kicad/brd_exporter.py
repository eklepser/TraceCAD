from datetime import datetime

from pbe_editor.core.models import PadShape, PadType, TextType
from pbe_editor.kicad.units import mm_to_kicad
from pbe_editor.kicad.pbe_layers import layer_to_id, drawseg_layer_to_id


def _pad_block(pad, net_code, net_name):
    shape_map = {PadShape.RECT: 'R', PadShape.CIRCLE: 'C', PadShape.OVAL: 'O'}
    shape_char = shape_map.get(pad.shape, 'C')
    if pad.pad_type == PadType.STANDARD:
        drill_val = pad.drill if pad.drill else 0.8
        dr_line = f"Dr {mm_to_kicad(drill_val)} 0 0"
        at_attr = 'STD'; at_mask = '00E0FFFF'
    elif pad.pad_type == PadType.SMD:
        dr_line = "Dr 0 0 0"; at_attr = 'SMD'; at_mask = '00888000'
    else:
        dr_line = "Dr 0 0 0"; at_attr = 'CONN'; at_mask = '00808000'
    ne_line = f'Ne {net_code} "{net_name}"' if net_code > 0 and net_name else 'Ne 0 ""'
    return [
        "$PAD",
        f'Sh "{pad.number}" {shape_char} '
        f'{mm_to_kicad(pad.width)} {mm_to_kicad(pad.height)} 0 0 0',
        dr_line,
        f"At {at_attr} N {at_mask}",
        ne_line,
        f"Po {mm_to_kicad(pad.x)} {mm_to_kicad(pad.y)}",
        "$EndPAD",
    ]


def _module_block(module, board):
    fp = module.footprint
    lines = [
        f"$MODULE {fp.name}",
        f"Po {mm_to_kicad(module.x)} {mm_to_kicad(module.y)} "
        f"{int(round(module.angle * 10))} 15 00000000 00000000 ~~",
        f"Li {fp.name}",
        "Sc 00000000",
        "AR",
        "Op 0 0 0",
    ]
    for text in fp.texts:
        if text.text_type == TextType.REFERENCE:
            idx = 0; value = module.reference
        elif text.text_type == TextType.VALUE:
            idx = 1; value = module.value
        else:
            continue
        x_k = mm_to_kicad(text.x); y_k = mm_to_kicad(text.y)
        size_k = mm_to_kicad(text.size)
        vis = 'V' if text.visible else 'I'
        lid = layer_to_id(text.layer)
        lines.append(f'T{idx} {x_k} {y_k} {size_k} {size_k} 0 120 N {vis} {lid} N "{value}"')
    for line in fp.lines:
        lid = layer_to_id(line.layer)
        lines.append(
            f"DS {mm_to_kicad(line.x)} {mm_to_kicad(line.y)} "
            f"{mm_to_kicad(line.x2)} {mm_to_kicad(line.y2)} "
            f"{mm_to_kicad(line.width)} {lid}"
        )
    for circle in fp.circles:
        x_c = mm_to_kicad(circle.x); y_c = mm_to_kicad(circle.y)
        r_k = mm_to_kicad(circle.radius); lid = layer_to_id(circle.layer)
        lines.append(f"DC {x_c} {y_c} {x_c + r_k} {y_c} {mm_to_kicad(circle.width)} {lid}")
    for arc in fp.arcs:
        lid = layer_to_id(arc.layer)
        lines.append(
            f"DA {mm_to_kicad(arc.x)} {mm_to_kicad(arc.y)} "
            f"{mm_to_kicad(arc.sx)} {mm_to_kicad(arc.sy)} "
            f"{int(round(arc.angle * 10))} {mm_to_kicad(arc.width)} {lid}"
        )
    for pad in fp.pads:
        pad_net = module.pad_nets.get(pad.number)
        net_code = pad_net.net_code if pad_net else 0
        net_name = pad_net.net_name if pad_net else ""
        lines.extend(_pad_block(pad, net_code, net_name))
    lines.append(f"$EndMODULE  {fp.name}")
    return lines


def _drawsegment_line(line):
    lid = drawseg_layer_to_id(line.layer)
    return [
        "$DRAWSEGMENT",
        f"Po 0 {mm_to_kicad(line.x1)} {mm_to_kicad(line.y1)} "
        f"{mm_to_kicad(line.x2)} {mm_to_kicad(line.y2)} {mm_to_kicad(line.width)}",
        f"De {lid} 0 900 0 0",
        "$EndDRAWSEGMENT",
    ]


def _drawsegment_circle(circle):
    lid = drawseg_layer_to_id(circle.layer)
    xc = mm_to_kicad(circle.x); yc = mm_to_kicad(circle.y)
    xp = mm_to_kicad(circle.x + circle.radius); yp = mm_to_kicad(circle.y)
    return [
        "$DRAWSEGMENT",
        f"Po 3 {xc} {yc} {xp} {yp} {mm_to_kicad(circle.width)}",
        f"De {lid} 0 900 0 0",
        "$EndDRAWSEGMENT",
    ]


def _drawsegment_arc(arc):
    lid = drawseg_layer_to_id(arc.layer)
    angle10 = int(round(arc.angle * 10))
    return [
        "$DRAWSEGMENT",
        f"Po 2 {mm_to_kicad(arc.x)} {mm_to_kicad(arc.y)} "
        f"{mm_to_kicad(arc.sx)} {mm_to_kicad(arc.sy)} {mm_to_kicad(arc.width)}",
        f"De {lid} 0 {angle10} 0 0",
        "$EndDRAWSEGMENT",
    ]


def _textpcb_block(text):
    lid = drawseg_layer_to_id(text.layer)
    x_k = mm_to_kicad(text.x); y_k = mm_to_kicad(text.y)
    size_k = mm_to_kicad(text.size)
    return [
        "$TEXTPCB",
        f'Te "{text.text}"',
        f"Po {x_k} {y_k} {size_k} {size_k} 120 0",
        f"De {lid} 1 0 Normal",
        "$EndTEXTPCB",
    ]


def build_brd_text(board):
    lines = []
    lines.append(f"PCBNEW-BOARD Version 1 date {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    lines.append("")
    lines.append("# Created by TraceCAD")
    lines.append("")
    lines.append("$GENERAL")
    lines.append("encoding utf-8")
    lines.append("LayerCount 2")
    lines.append("Ly 1FFF8001")
    lines.append("EnabledLayers 1FFF8001")
    lines.append("Links 0")
    lines.append("NoConn 0")
    lines.append("Di 0 0 117000 82670")
    lines.append(f"Ndraw {len(board.lines) + len(board.circles) + len(board.arcs)}")
    lines.append("Ntrack 0")
    lines.append("Nzone 0")
    lines.append("BoardThickness 630")
    lines.append(f"Nmodule {len(board.modules)}")
    lines.append(f"Nnets {len(board.nets) + 1}")
    lines.append("$EndGENERAL")
    lines.append("")
    lines.append("$SHEETDESCR")
    lines.append("Sheet A4 11700 8267")
    lines.append('Title ""')
    lines.append(f'Date "{datetime.now().strftime("%d %b %Y")}"')
    lines.append('Rev ""')
    lines.append('Comp ""')
    lines.append('Comment1 ""')
    lines.append('Comment2 ""')
    lines.append('Comment3 ""')
    lines.append('Comment4 ""')
    lines.append("$EndSHEETDESCR")
    lines.append("")
    lines.append("$SETUP")
    lines.append("InternalUnit 0.000100 INCH")
    lines.append("Layers 2")
    lines.append("Layer[0] Back signal")
    lines.append("Layer[15] Front signal")
    lines.append("TrackWidth 80")
    lines.append("TrackClearence 100")
    lines.append("ZoneClearence 200")
    lines.append("TrackMinWidth 80")
    lines.append("DrawSegmWidth 150")
    lines.append("EdgeSegmWidth 150")
    lines.append("ViaSize 350")
    lines.append("ViaDrill 250")
    lines.append("ViaMinSize 350")
    lines.append("ViaMinDrill 200")
    lines.append("MicroViaSize 200")
    lines.append("MicroViaDrill 50")
    lines.append("MicroViasAllowed 0")
    lines.append("MicroViaMinSize 200")
    lines.append("MicroViaMinDrill 50")
    lines.append("TextPcbWidth 120")
    lines.append("TextPcbSize 600 800")
    lines.append("EdgeModWidth 150")
    lines.append("TextModSize 600 600")
    lines.append("TextModWidth 120")
    lines.append("PadSize 600 600")
    lines.append("PadDrill 320")
    lines.append("Pad2MaskClearance 100")
    lines.append("AuxiliaryAxisOrg 0 0")
    lines.append("$EndSETUP")
    lines.append("")
    lines.append("$EQUIPOT")
    lines.append('Na 0 ""')
    lines.append("St ~")
    lines.append("$EndEQUIPOT")
    for code in sorted(board.nets.keys()):
        net = board.nets[code]
        lines.append("$EQUIPOT")
        lines.append(f'Na {net.code} "{net.name}"')
        lines.append("St ~")
        lines.append("$EndEQUIPOT")
    lines.append("$NCLASS")
    lines.append('Name "Default"')
    lines.append('Desc "Это класс цепей по умолчанию."')
    lines.append("Clearance 100")
    lines.append("TrackWidth 80")
    lines.append("ViaDia 350")
    lines.append("ViaDrill 250")
    lines.append("uViaDia 200")
    lines.append("uViaDrill 50")
    lines.append('AddNet ""')
    for code in sorted(board.nets.keys()):
        lines.append(f'AddNet "{board.nets[code].name}"')
    lines.append("$EndNCLASS")
    lines.append("")
    for module in board.modules:
        lines.extend(_module_block(module, board))
    for text in board.texts:
        lines.extend(_textpcb_block(text))
    for line in board.lines:
        lines.extend(_drawsegment_line(line))
    for circle in board.circles:
        lines.extend(_drawsegment_circle(circle))
    for arc in board.arcs:
        lines.extend(_drawsegment_arc(arc))
    lines.append("$TRACK")
    lines.append("$EndTRACK")
    lines.append("$ZONE")
    lines.append("$EndZONE")
    lines.append("$EndBOARD")
    return "\n".join(lines)