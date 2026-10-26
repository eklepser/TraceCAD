from PySide6.QtCore import QPointF

from pbe_editor.core.board_models import is_gnd_net, is_power_net
from pbe_editor.core.ratsnest_mst import build_mst_edges
from pbe_editor.graphics.module_item import BoardModuleGraphicsItem
from pbe_editor.graphics.board_line_item import (
    BoardLineGraphicsItem, BoardCircleGraphicsItem, BoardArcGraphicsItem,
    BoardTextGraphicsItem,
)
from pbe_editor.graphics.ratsnest_item import RatsnestGraphicsItem


class BoardManager:
    def __init__(self, board, scene, canvas):
        self.board = board
        self.scene = scene
        self.canvas = canvas
        self.items = {}
        self.line_items = {}
        self.circle_items = {}
        self.arc_items = {}
        self.text_items = {}
        self.ratsnest_items = []
        self.show_ratsnest = True

    def add_module(self, module):
        item = BoardModuleGraphicsItem(module, self.canvas)
        self.scene.addItem(item)
        self.items[module.uid] = item
        return item

    def add_line(self, line):
        item = BoardLineGraphicsItem(line, self.canvas)
        self.scene.addItem(item)
        self.line_items[line.uid] = item
        return item

    def add_circle(self, circle):
        item = BoardCircleGraphicsItem(circle, self.canvas)
        self.scene.addItem(item)
        self.circle_items[circle.uid] = item
        return item

    def add_arc(self, arc):
        item = BoardArcGraphicsItem(arc, self.canvas)
        self.scene.addItem(item)
        self.arc_items[arc.uid] = item
        return item

    def add_text(self, text):
        item = BoardTextGraphicsItem(text, self.canvas)
        self.scene.addItem(item)
        self.text_items[text.uid] = item
        return item

    def remove_module(self, module):
        item = self.items.pop(module.uid, None)
        if item is not None and item.scene() is self.scene:
            self.scene.removeItem(item)

    def remove_line(self, line):
        item = self.line_items.pop(line.uid, None)
        if item is not None and item.scene() is self.scene:
            self.scene.removeItem(item)

    def remove_circle(self, circle):
        item = self.circle_items.pop(circle.uid, None)
        if item is not None and item.scene() is self.scene:
            self.scene.removeItem(item)

    def remove_arc(self, arc):
        item = self.arc_items.pop(arc.uid, None)
        if item is not None and item.scene() is self.scene:
            self.scene.removeItem(item)

    def remove_text(self, text):
        item = self.text_items.pop(text.uid, None)
        if item is not None and item.scene() is self.scene:
            self.scene.removeItem(item)

    def clear(self):
        all_items = (list(self.items.values()) + list(self.line_items.values())
                     + list(self.circle_items.values()) + list(self.arc_items.values())
                     + list(self.text_items.values()))
        for item in all_items:
            try:
                if item.scene() is self.scene:
                    self.scene.removeItem(item)
            except RuntimeError:
                pass
        self.items.clear()
        self.line_items.clear()
        self.circle_items.clear()
        self.arc_items.clear()
        self.text_items.clear()
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
                item = RatsnestGraphicsItem(
                    QPointF(*pos_a), QPointF(*pos_b),
                    net_code=code, net_name=net_name,
                    is_power=is_power, is_gnd=is_gnd,
                    label_a=f"{module_a.reference}.{pad_a}",
                    label_b=f"{module_b.reference}.{pad_b}",
                )
                self.scene.addItem(item)
                self.ratsnest_items.append(item)

    def refresh_ratsnest_for_module(self, module):
        self.rebuild_ratsnest()