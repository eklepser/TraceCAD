from dataclasses import dataclass, field
from typing import Dict, List, Optional
import copy
import math

from footprint_editor.core.models import Footprint


POWER_NET_NAMES = {"GND", "VCC", "VDD", "VSS", "+5V", "+3V3", "+3.3V", "-5V", "-12V", "+12V"}

GND_NET_NAMES = {"GND"}


def is_power_net(name: str) -> bool:
    if not name:
        return False
    return name.upper() in {n.upper() for n in POWER_NET_NAMES}


def is_gnd_net(name: str) -> bool:
    if not name:
        return False
    return name.upper() in {n.upper() for n in GND_NET_NAMES}


@dataclass
class PadNet:
    pad_number: str
    net_code: int
    net_name: str


@dataclass
class Net:
    code: int
    name: str


@dataclass
class BoardModule:
    footprint: Footprint
    reference: str
    value: str
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    layer: str = "F.Cu"
    pad_nets: Dict[str, PadNet] = field(default_factory=dict)
    uid: int = 0
    graphics_item: object = None

    def get_pad_absolute(self, pad_number: str):
        pad = None
        for p in self.footprint.pads:
            if p.number == pad_number:
                pad = p
                break
        if pad is None:
            return None

        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        lx = pad.x
        ly = pad.y
        gx = self.x + lx * cos_a - ly * sin_a
        gy = self.y + lx * sin_a + ly * cos_a
        return gx, gy

    def get_footprint_copy(self) -> Footprint:
        return copy.deepcopy(self.footprint)


@dataclass
class Board:
    name: str = "Untitled"
    modules: List[BoardModule] = field(default_factory=list)
    nets: Dict[int, Net] = field(default_factory=dict)
    filename: Optional[str] = None

    def get_net_by_name(self, name: str) -> Optional[Net]:
        for net in self.nets.values():
            if net.name == name:
                return net
        return None

    def get_or_create_net(self, name: str) -> Net:
        net = self.get_net_by_name(name)
        if net is not None:
            return net
        code = max(self.nets.keys()) + 1 if self.nets else 1
        net = Net(code=code, name=name)
        self.nets[code] = net
        return net

    def get_net_by_code(self, code: int) -> Optional[Net]:
        return self.nets.get(code)

    def collect_net_pins(self):
        result = {}
        for module in self.modules:
            for pad_number, pad_net in module.pad_nets.items():
                if pad_net.net_code <= 0:
                    continue
                if not pad_net.net_name:
                    continue
                pos = module.get_pad_absolute(pad_number)
                if pos is None:
                    continue
                result.setdefault(pad_net.net_code, []).append((module, pad_number, pos))

        for code in result:
            result[code].sort(key=lambda x: (x[0].reference, x[1]))

        return result