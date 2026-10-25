from PySide6.QtCore import QPointF

from pbe_editor.core.board_models import is_gnd_net, is_power_net
from pbe_editor.core.ratsnest_mst import build_mst_edges
from pbe_editor.graphics.module_item import BoardModuleGraphicsItem
from pbe_editor.graphics.ratsnest_item import RatsnestGraphicsItem


class BoardManager:
    def __init__(self, board, scene, canvas):
        self.board = board
        self.scene = scene
        self.canvas = canvas
        self.items = {}
        self.ratsnest_items = []
        self.show_ratsnest = True

    def add_module(self, module):
        item = BoardModuleGraphicsItem(module, self.canvas)
        self.scene.addItem(item)
        self.items[module.uid] = item
        return item

    def clear(self):
        for item in list(self.items.values()):
            try:
                if item.scene() is self.scene:
                    self.scene.removeItem(item)
            except RuntimeError:
                pass
        self.items.clear()
        self.clear_ratsnest()

    def clear_ratsnest(self):
        for item in self.ratsnest_items:
            try:
                if item.scene() is self.scene:
                    self.scene.removeItem(item)
            except RuntimeError:
                pass
        self.ratsnest_items.clear()

    def rebuild_ratsnest(self):
        self.clear_ratsnest()
        if not self.show_ratsnest:
            return

        net_pins = self.board.collect_net_pins()
        for code, pins in net_pins.items():
            if len(pins) < 2:
                continue

            net_name = pins[0][0].pad_nets.get(pins[0][1])
            net_name = net_name.net_name if net_name else ""
            is_gnd = is_gnd_net(net_name)
            is_power = is_power_net(net_name) and not is_gnd

            points = [p[2] for p in pins]
            edges = build_mst_edges(points)

            for a_idx, b_idx in edges:
                module_a, pad_a, pos_a = pins[a_idx]
                module_b, pad_b, pos_b = pins[b_idx]
                label_a = f"{module_a.reference}.{pad_a}"
                label_b = f"{module_b.reference}.{pad_b}"
                item = RatsnestGraphicsItem(
                    QPointF(*pos_a), QPointF(*pos_b),
                    net_code=code, net_name=net_name,
                    is_power=is_power, is_gnd=is_gnd,
                    label_a=label_a, label_b=label_b,
                )
                self.scene.addItem(item)
                self.ratsnest_items.append(item)

    def refresh_ratsnest_for_module(self, module):
        self.rebuild_ratsnest()