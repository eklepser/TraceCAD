from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid
import copy

class PadShape(Enum):
    CIRCLE = "circle"
    RECT = "rect"
    OVAL = "oval"

class PadType(Enum):
    SMD = "smd"
    THT = "thru_hole"

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
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __deepcopy__(self, memo):
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
class Line:
    x1: float
    y1: float
    x2: float
    y2: float
    width: float = 0.075
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __deepcopy__(self, memo):
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
class Circle:
    x: float
    y: float
    radius: float
    width: float = 0.075
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __deepcopy__(self, memo):
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
class Footprint:
    name: str
    reference: str = "REF**"
    value: str = ""
    pads: List[Pad] = field(default_factory=list)
    lines: List[Line] = field(default_factory=list)
    circles: List[Circle] = field(default_factory=list)