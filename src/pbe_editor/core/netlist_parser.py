import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class NetlistComponent:
    timestamp: str
    footprint: str
    reference: str
    value: str
    pins: Dict[str, str] = field(default_factory=dict)


def parse_netlist(filepath: str) -> List[NetlistComponent]:
    content = Path(filepath).read_text(encoding='utf-8', errors='ignore')
    return parse_netlist_content(content)


def parse_netlist_content(content: str) -> List[NetlistComponent]:
    components: List[NetlistComponent] = []
    lines = content.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        if not line.startswith('( /'):
            i += 1
            continue

        match = re.match(
            r'^\(\s+(/\S+)\s+(\S+)\s+(\S+)\s+(.*?)\s*$',
            line
        )
        if not match:
            i += 1
            continue

        timestamp = match.group(1)
        footprint = match.group(2)
        reference = match.group(3)
        value = match.group(4).strip()

        component = NetlistComponent(
            timestamp=timestamp,
            footprint=footprint,
            reference=reference,
            value=value,
        )

        i += 1
        while i < n:
            pin_line = lines[i].strip()
            if pin_line == ')':
                break
            pin_match = re.match(r'^\(\s*(\S+)\s+(.+?)\s*\)\s*$', pin_line)
            if pin_match:
                pin_number = pin_match.group(1)
                net_name = pin_match.group(2).strip().strip('"')
                component.pins[pin_number] = net_name
            i += 1

        components.append(component)
        i += 1

    return components