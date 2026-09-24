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
        if item:
            self.scene.removeItem(item)

    def get_next_pad_number(self):
        numbers = []
        for p in self.footprint.pads:
            try:
                numbers.append(int(p.number))
            except (ValueError, TypeError):
                pass
        return str(max(numbers) + 1) if numbers else "1"