from footprint_editor.core.models import Pad, Line, Circle, Text
from footprint_editor.graphics.pad_item import PadGraphicsItem
from footprint_editor.graphics.line_item import LineGraphicsItem
from footprint_editor.graphics.circle_item import CircleGraphicsItem
from footprint_editor.graphics.text_item import TextGraphicsItem

class GraphicsFactory:
    @staticmethod
    def create(model, canvas, is_preview=False):
        if isinstance(model, Pad):
            return PadGraphicsItem(model, canvas)
        elif isinstance(model, Line):
            return LineGraphicsItem(model, canvas, is_preview)
        elif isinstance(model, Circle):
            return CircleGraphicsItem(model, canvas, is_preview)
        elif isinstance(model, Text):
            return TextGraphicsItem(model, canvas)
        raise ValueError(f"Unknown model type: {type(model)}")