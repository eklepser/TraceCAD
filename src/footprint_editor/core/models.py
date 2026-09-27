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
    SMD = "smd"
    THT = "thru_hole"


class TextType(Enum):
    NORMAL = "normal"
    REFERENCE = "reference"
    VALUE = "value"


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
class Pad:
    number: str
    shape: PadShape
    pad_type: PadType
    x: float
    y: float
    width: float
    height: float
    drill: Optional[float] = None
    locked: bool = False
    uid: int = field(default_factory=new_uid)

    __deepcopy__ = _deepcopy_no_graphics


@dataclass
class Line:
    x1: float
    y1: float
    x2: float
    y2: float
    width: float = Sizes.DEFAULT_LINE_WIDTH
    locked: bool = False
    uid: int = field(default_factory=new_uid)

    __deepcopy__ = _deepcopy_no_graphics


@dataclass
class Circle:
    x: float
    y: float
    radius: float
    width: float = Sizes.DEFAULT_LINE_WIDTH
    locked: bool = False
    uid: int = field(default_factory=new_uid)

    __deepcopy__ = _deepcopy_no_graphics


@dataclass
class Arc:
    cx: float
    cy: float
    sx: float
    sy: float
    angle: float = 90.0
    width: float = Sizes.DEFAULT_LINE_WIDTH
    locked: bool = False
    uid: int = field(default_factory=new_uid)

    __deepcopy__ = _deepcopy_no_graphics


@dataclass
class Text:
    x: float
    y: float
    text: str
    size: float = 1.0
    visible: bool = True
    text_type: TextType = TextType.NORMAL
    locked: bool = False
    uid: int = field(default_factory=new_uid)

    __deepcopy__ = _deepcopy_no_graphics


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