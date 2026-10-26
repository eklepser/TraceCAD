class BoardStateService:
    def next_module_uid(self):
        if not self.board.modules:
            return 1
        return max(m.uid for m in self.board.modules) + 1

    def next_line_uid(self):
        if not self.board.lines:
            return 1
        return max(l.uid for l in self.board.lines) + 1

    def next_circle_uid(self):
        if not self.board.circles:
            return 1
        return max(c.uid for c in self.board.circles) + 1

    def next_arc_uid(self):
        if not self.board.arcs:
            return 1
        return max(a.uid for a in self.board.arcs) + 1

    def next_text_uid(self):
        if not self.board.texts:
            return 1
        return max(t.uid for t in self.board.texts) + 1