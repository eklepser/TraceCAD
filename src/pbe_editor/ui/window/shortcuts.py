from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QGraphicsView
from constants import (
    PAN_KEYS,
    VK_ESCAPE, VK_DELETE, VK_F1, VK_F2, VK_F3, VK_F11,
    VK_C, VK_V, VK_S, VK_R, VK_Y, VK_Z, VK_G,
)
from pbe_editor.ui.panels.drawing_tool_bar import BoardTool


class KeyboardService:
    def handle_global_key(self, event):
        vk = event.nativeVirtualKey()
        ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

        if event.type() == QEvent.Type.KeyPress:
            if event.matches(QKeySequence.StandardKey.Copy) or (ctrl and not shift and vk == VK_C):
                self.commands.copy_selected()
                return True
            if event.matches(QKeySequence.StandardKey.Paste) or (ctrl and not shift and vk == VK_V):
                self.commands.paste()
                return True
            if event.matches(QKeySequence.StandardKey.Save) or (ctrl and not shift and vk == VK_S):
                self.save_board()
                return True
            if event.matches(QKeySequence.StandardKey.Undo) or (ctrl and not shift and vk == VK_Z):
                self.undo()
                return True
            if event.matches(QKeySequence.StandardKey.Redo) or (ctrl and shift and vk == VK_Z) or (ctrl and vk == VK_Y):
                self.redo()
                return True
            if ctrl and not shift and event.key() == Qt.Key.Key_O:
                self.commands.on_autoplace()
                return True
            if ctrl and not shift and event.key() == Qt.Key.Key_P:
                self.commands.on_pairwise_autoplace()
                return True
            if ctrl:
                return False

            if event.key() == Qt.Key.Key_Escape:
                self.exit_to_select_mode()
                return True

            if self._handle_tool_key(event):
                return True
            if self._handle_nav_key(event, vk):
                return True

        elif event.type() == QEvent.Type.KeyRelease:
            if vk in PAN_KEYS:
                self.canvas.pressed_keys.discard(vk)
                if not self.canvas.pressed_keys:
                    self.canvas.pan_timer.stop()
                return True

        return False

    def _handle_tool_key(self, event):
        key_map = {
            Qt.Key.Key_1: BoardTool.ADD_LINE,
            Qt.Key.Key_2: BoardTool.ADD_PAD,
            Qt.Key.Key_3: BoardTool.ADD_CIRCLE,
            Qt.Key.Key_4: BoardTool.ADD_ARC,
            Qt.Key.Key_5: BoardTool.ADD_TEXT,
        }
        tool = key_map.get(event.key())
        if tool is not None:
            self._on_drawing_tool(tool)
            self.tool_bar.set_active(tool)
            return True
        return False

    def _handle_nav_key(self, event, vk):
        if event.key() == Qt.Key.Key_R or vk == VK_R:
            self.commands.rotate_selected()
            return True
        if event.key() == Qt.Key.Key_G or vk == VK_G:
            self.act_show_grid.setChecked(not self.act_show_grid.isChecked())
            self.toggle_grid()
            return True
        if event.key() == Qt.Key.Key_F11 or vk == VK_F11:
            self.toggle_fullscreen()
            return True
        if vk in PAN_KEYS:
            self.canvas.pressed_keys.add(vk)
            if not self.canvas.pan_timer.isActive():
                self.canvas.pan_timer.start()
            return True
        if event.key() == Qt.Key.Key_Delete or vk == VK_DELETE:
            self.commands.delete_selected()
            return True
        if event.key() == Qt.Key.Key_F1 or vk == VK_F1:
            self._change_grid_step(-1)
            return True
        if event.key() == Qt.Key.Key_F2 or vk == VK_F2:
            self._change_grid_step(1)
            return True
        if event.key() == Qt.Key.Key_F3 or vk == VK_F3:
            self._toggle_grid_series()
            return True
        return False