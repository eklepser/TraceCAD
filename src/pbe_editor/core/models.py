from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import copy
from constants import Sizes


class PadShape(Enum):
    CIRCLE = "circle"
    RECT = "rect"
    OVAL = "oval"


class PadType(Enum):
    STANDARD = "standard"
    SMD = "smd"
    CONN = "conn"


class TextType(Enum):
    NORMAL = "normal"
    REFERENCE = "reference"
    VALUE = "value"


AVAILABLE_LAYERS = [
    "F.Cu", "B.Cu",
    "F.Adhes", "B.Adhes",
    "F.Paste", "B.Paste",
    "F.SilkS", "B.SilkS",
    "F.Mask", "B.Mask",
    "Cmts.User", "Eco1.User", "Eco2.User",
    "Edge.Cuts",
]

DEFAULT_LAYERS = {
    PadType.STANDARD: ["F.Cu", "B.Cu", "F.Mask", "B.Mask"],
    PadType.SMD:      ["F.Cu", "F.Paste", "F.Mask"],
    PadType.CONN:     ["F.Cu", "F.Mask"],
}


def default_layers_for_pad_type(pad_type):
    return list(DEFAULT_LAYERS.get(pad_type, DEFAULT_LAYERS[PadType.STANDARD]))


_next_uid = [1]


def new_uid():
    value = _next_uid[0]
    _next_uid[0] += 1
    return value


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
class BaseObject:
    x: float
    y: float
    uid: int = field(default_factory=new_uid, kw_only=True)
    locked: bool = field(default=False, kw_only=True)

    def __deepcopy__(self, memo):
        return _deepcopy_no_graphics(self, memo)


@dataclass
class Pad(BaseObject):
    number: str
    shape: PadShape
    pad_type: PadType
    width: float
    height: float
    drill: Optional[float] = None
    layers: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.layers:
            self.layers = default_layers_for_pad_type(self.pad_type)


@dataclass
class Line(BaseObject):
    x2: float
    y2: float
    width: float = Sizes.DEFAULT_LINE_WIDTH
    layer: str = "F.SilkS"


@dataclass
class Circle(BaseObject):
    radius: float
    width: float = Sizes.DEFAULT_LINE_WIDTH
    layer: str = "F.SilkS"


@dataclass
class Arc(BaseObject):
    sx: float
    sy: float
    angle: float = 90.0
    width: float = Sizes.DEFAULT_LINE_WIDTH
    layer: str = "F.SilkS"


@dataclass
class BaseText(BaseObject):
    text: str
    size: float = 1.0
    visible: bool = True
    layer: str = "F.SilkS"


@dataclass
class Text(BaseText):
    text_type: TextType = TextType.NORMAL


@dataclass
class Footprint:
    name: str
    reference: str = "REF**"
    value: str = "VAL**"
    pads: List[Pad] = field(default_factory=list)
    lines: List[Line] = field(default_factory=list)
    circles: List[Circle] = field(default_factory=list)
    arcs: List[Arc] = field(default_factory=list)
    texts: List[Text] = field(default_factory=list)