from pbe_editor.graphics.module_item import BoardModuleGraphicsItem


class BoardManager:
    def __init__(self, board, scene, canvas):
        self.board = board
        self.scene = scene
        self.canvas = canvas
        self.items = {}

    def add_module(self, module):
        item = BoardModuleGraphicsItem(module, self.canvas)
        self.scene.addItem(item)
        self.items[module.uid] = item
        return item

    def clear(self):
        for item in list(self.items.values()):
            if item.scene() is self.scene:
                self.scene.removeItem(item)
        self.items.clear()