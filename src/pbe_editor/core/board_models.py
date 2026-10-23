from dataclasses import dataclass, field
from typing import Dict, List, Optional
import copy

from footprint_editor.core.models import Footprint


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