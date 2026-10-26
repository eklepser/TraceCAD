import copy


class HistoryService:
    def snapshot(self):
        return {
            "modules": copy.deepcopy(self.board.modules),
            "lines": copy.deepcopy(self.board.lines),
            "circles": copy.deepcopy(self.board.circles),
            "arcs": copy.deepcopy(self.board.arcs),
            "texts": copy.deepcopy(self.board.texts),
            "nets": copy.deepcopy(self.board.nets),
        }

    def restore_snapshot(self, snap):
        self.board.modules = copy.deepcopy(snap["modules"])
        self.board.lines = copy.deepcopy(snap["lines"])
        self.board.circles = copy.deepcopy(snap["circles"])
        self.board.arcs = copy.deepcopy(snap["arcs"])
        self.board.texts = copy.deepcopy(snap.get("texts", []))
        self.board.nets = copy.deepcopy(snap["nets"])
        self.manager.clear()
        self.manager.board = self.board
        for m in self.board.modules:
            self.manager.add_module(m)
        for l in self.board.lines:
            self.manager.add_line(l)
        for c in self.board.circles:
            self.manager.add_circle(c)
        for a in self.board.arcs:
            self.manager.add_arc(a)
        for t in self.board.texts:
            self.manager.add_text(t)
        if self.current_tool != "select":
            self._set_selectable_all(False)
        self.manager.rebuild_ratsnest()
        self.refresh_module_list()

    def _reset_history(self):
        self._undo_stack = []
        self._redo_stack = []
        self._current_snapshot = self.snapshot()
        self._update_history_buttons()

    def commit_snapshot(self):
        self._modified = True
        if self._current_snapshot is None:
            self._current_snapshot = self.snapshot()
            return
        self._undo_stack.append(self._current_snapshot)
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._current_snapshot = self.snapshot()
        self._update_history_buttons()

    def undo(self):
        if not self._undo_stack:
            return
        self._redo_stack.append(self._current_snapshot)
        self._current_snapshot = self._undo_stack.pop()
        self.restore_snapshot(self._current_snapshot)
        self._update_history_buttons()
        self._modified = True
        self.show_log("отменено")

    def redo(self):
        if not self._redo_stack:
            return
        self._undo_stack.append(self._current_snapshot)
        self._current_snapshot = self._redo_stack.pop()
        self.restore_snapshot(self._current_snapshot)
        self._update_history_buttons()
        self._modified = True
        self.show_log("повторено")

    def _update_history_buttons(self):
        self.aux_bar.set_undo_enabled(bool(self._undo_stack))
        self.aux_bar.set_redo_enabled(bool(self._redo_stack))