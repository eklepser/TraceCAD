from footprint_editor.core.models import PadShape, PadType, TextType
from footprint_editor.kicad.units import mm_to_kicad
from footprint_editor.kicad.layers import layer_to_id


PAD_ATTR_MAP = {
    PadType.STANDARD: ('STD', '00E0FFFF'),
    PadType.SMD:      ('SMD', '00888000'),
    PadType.CONN:     ('CONN', '00808000'),
}


def _pad_block(pad):
    shape_map = {PadShape.RECT: 'R', PadShape.CIRCLE: 'C', PadShape.OVAL: 'O'}
    shape_char = shape_map.get(pad.shape, 'C')
    attr, mask = PAD_ATTR_MAP.get(pad.pad_type, PAD_ATTR_MAP[PadType.STANDARD])

    if pad.pad_type == PadType.STANDARD:
        drill_val = pad.drill if pad.drill else 0.8
        dr_line = f"Dr {mm_to_kicad(drill_val)} 0 0"
    else:
        dr_line = "Dr 0 0 0"

    return [
        "$PAD",
        f'Sh "{pad.number}" {shape_char} '
        f'{mm_to_kicad(pad.width)} {mm_to_kicad(pad.height)} 0 0 0',
        dr_line,
        f"At {attr} N {mask}",
        'Ne 0 ""',
        f"Po {mm_to_kicad(pad.x)} {mm_to_kicad(pad.y)}",
        "$EndPAD",
    ]


def _text_block(text, idx):
    x_k = mm_to_kicad(text.x)
    y_k = mm_to_kicad(text.y)
    size_k = mm_to_kicad(text.size)
    vis = 'V' if text.visible else 'I'
    lid = layer_to_id(text.layer)
    value = text.text if text.text else "Text"
    return (
        f'T{idx} {x_k} {y_k} {size_k} {size_k} 0 120 N {vis} {lid} N "{value}"'
    )


def _line_block(line):
    lid = layer_to_id(line.layer)
    return (
        f"DS {mm_to_kicad(line.x)} {mm_to_kicad(line.y)} "
        f"{mm_to_kicad(line.x2)} {mm_to_kicad(line.y2)} "
        f"{mm_to_kicad(line.width)} {lid}"
    )


def _circle_block(circle):
    x_c = mm_to_kicad(circle.x)
    y_c = mm_to_kicad(circle.y)
    r_k = mm_to_kicad(circle.radius)
    lid = layer_to_id(circle.layer)
    return f"DC {x_c} {y_c} {x_c + r_k} {y_c} {mm_to_kicad(circle.width)} {lid}"


def _arc_block(arc):
    lid = layer_to_id(arc.layer)
    return (
        f"DA {mm_to_kicad(arc.x)} {mm_to_kicad(arc.y)} "
        f"{mm_to_kicad(arc.sx)} {mm_to_kicad(arc.sy)} "
        f"{int(round(arc.angle * 10))} {mm_to_kicad(arc.width)} {lid}"
    )


def _texts_blocks(fp):
    lines = []
    text_idx = 2
    for text in fp.texts:
        if text.text_type == TextType.REFERENCE:
            idx = 0
        elif text.text_type == TextType.VALUE:
            idx = 1
        else:
            idx = text_idx
            text_idx += 1
        lines.append(_text_block(text, idx))
    return lines


def build_kicad_module_text(fp):
    lines = [
        f"$MODULE {fp.name}",
        "Po 0 0 0 15 00000000 00000000 ~~",
        f"Li {fp.name}",
        "Sc 00000000",
        "AR",
        "Op 0 0 0",
    ]

    lines.extend(_texts_blocks(fp))

    for line in fp.lines:
        lines.append(_line_block(line))

    for circle in fp.circles:
        lines.append(_circle_block(circle))

    for arc in fp.arcs:
        lines.append(_arc_block(arc))

    for pad in fp.pads:
        lines.extend(_pad_block(pad))

    lines.append(f"$EndMODULE  {fp.name}")
    return "\n".join(lines)