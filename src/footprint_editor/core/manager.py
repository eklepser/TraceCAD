from PySide6.QtWidgets import QGraphicsItem
from footprint_editor.graphics.factory import GraphicsFactory


class FootprintManager:
    def __init__(self, footprint, scene, canvas):
        self.footprint = footprint
        self.scene = scene
        self.canvas = canvas
        self.items = {}

    def add_model(self, model):
        item = GraphicsFactory.create(model, self.canvas)
        self.scene.addItem(item)
        self.items[model.uid] = item
        return item

    def remove_model(self, model):
        item = self.items.pop(model.uid, None)
        if item is None:
            return
        item.setSelected(False)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
        item.setEnabled(False)
        item.setVisible(False)
        if item.scene() is self.scene:
            self.scene.removeItem(item)
        self.scene.update()
        self.canvas.viewport().update()

    def get_next_pad_number(self):
        numbers = []
        for p in self.footprint.pads:
            try:
                numbers.append(int(p.number))
            except (ValueError, TypeError):
                pass
        return str(max(numbers) + 1) if numbers else "1"