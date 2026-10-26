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


def _deepcopy_no_graphics(self, memo):
    cls = self.__class__
    result = cls.__new__(cls)
    memo[id(self)] = result
    for k, v in self.__dict__.items():
        if k == 'graphics_item':
            setattr(result, k, None)
        else:
            setattr(result, k, copy.deepcopy(v, memo))
    return result


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

    def __deepcopy__(self, memo):
        return _deepcopy_no_graphics(self, memo)

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
class BoardLine:
    x1: float
    y1: float
    x2: float
    y2: float
    layer: str = "Edge.Cuts"
    width: float = 0.15
    uid: int = 0
    graphics_item: object = None

    def __deepcopy__(self, memo):
        return _deepcopy_no_graphics(self, memo)


@dataclass
class BoardCircle:
    x: float
    y: float
    radius: float
    layer: str = "Edge.Cuts"
    width: float = 0.15
    uid: int = 0
    graphics_item: object = None

    def __deepcopy__(self, memo):
        return _deepcopy_no_graphics(self, memo)


@dataclass
class BoardArc:
    x: float
    y: float
    sx: float
    sy: float
    angle: float = 90.0
    layer: str = "Edge.Cuts"
    width: float = 0.15
    uid: int = 0
    graphics_item: object = None

    def __deepcopy__(self, memo):
        return _deepcopy_no_graphics(self, memo)


@dataclass
class BoardText:
    x: float
    y: float
    text: str = "Text"
    size: float = 1.0
    layer: str = "Edge.Cuts"
    visible: bool = True
    uid: int = 0
    graphics_item: object = None

    def __deepcopy__(self, memo):
        return _deepcopy_no_graphics(self, memo)


@dataclass
class Board:
    name: str = "Untitled"
    modules: List[BoardModule] = field(default_factory=list)
    lines: List[BoardLine] = field(default_factory=list)
    circles: List[BoardCircle] = field(default_factory=list)
    arcs: List[BoardArc] = field(default_factory=list)
    texts: List[BoardText] = field(default_factory=list)
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

    def all_references(self):
        return {m.reference for m in self.modules}

    def auto_reference(self, prefix: str = "REF") -> str:
        existing = self.all_references()
        i = 1
        while True:
            name = f"{prefix}{i}"
            if name not in existing:
                return name
            i += 1

    def find_pad_at(self, scene_x: float, scene_y: float, tolerance: float):
        best = None
        best_dist = tolerance
        for module in self.modules:
            for pad in module.footprint.pads:
                pos = module.get_pad_absolute(pad.number)
                if pos is None:
                    continue
                dx = scene_x - pos[0]
                dy = scene_y - pos[1]
                dist = math.hypot(dx, dy)
                if dist <= best_dist:
                    best_dist = dist
                    best = (module, pad.number)
        return best