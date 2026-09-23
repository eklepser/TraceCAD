from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid

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

@dataclass
class Footprint:
    name: str
    reference: str = "REF**"
    value: str = ""
    pads: List[Pad] = field(default_factory=list)