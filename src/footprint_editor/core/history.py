import copy
from footprint_editor.core.models import Footprint


class History:
    def __init__(self, limit=200):
        self._undo = []
        self._redo = []
        self._limit = limit
        self._current = None

    def reset(self, footprint):
        self._undo.clear()
        self._redo.clear()
        self._current = copy.deepcopy(footprint)

    def push(self, footprint):
        if self._current is None:
            self._current = copy.deepcopy(footprint)
            return
        self._undo.append(self._current)
        if len(self._undo) > self._limit:
            self._undo.pop(0)
        self._redo.clear()
        self._current = copy.deepcopy(footprint)

    def can_undo(self):
        return len(self._undo) > 0

    def can_redo(self):
        return len(self._redo) > 0

    def undo(self):
        if not self.can_undo():
            return None
        self._redo.append(self._current)
        self._current = self._undo.pop()
        return copy.deepcopy(self._current)

    def redo(self):
        if not self.can_redo():
            return None
        self._undo.append(self._current)
        self._current = self._redo.pop()
        return copy.deepcopy(self._current)