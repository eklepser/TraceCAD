from PySide6.QtCore import QEvent, Qt
from constants import (
    Tool, PAN_KEYS,
    VK_ESCAPE, VK_DELETE, VK_F1, VK_F2, VK_F3, VK_F11,
    VK_C, VK_V, VK_S, VK_R, VK_Y, VK_Z,
    VK_1, VK_2, VK_3, VK_4, VK_5,
)


class KeyboardService:
    def handle_global_key(self, event):
        vk = event.nativeVirtualKey()
        ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

        if event.type() == QEvent.Type.KeyPress:
            if self._handle_ctrl_key(vk, ctrl, shift):
                return True
            if self._handle_tool_key(vk):
                return True
            if self._handle_nav_key(vk):
                return True

        elif event.type() == QEvent.Type.KeyRelease:
            if vk in PAN_KEYS:
                self.canvas.pressed_keys.discard(vk)
                if not self.canvas.pressed_keys:
                    self.canvas.pan_timer.stop()
                return True

        return False

    def _handle_ctrl_key(self, vk, ctrl, shift):
        if not ctrl:
            return False
        if shift and vk == VK_Z:
            self.redo(); return True
        if vk == VK_Z:
            self.undo(); return True
        if vk == VK_Y:
            self.redo(); return True
        if vk == VK_C:
            self.commands.copy_selected(); return True
        if vk == VK_V:
            self.commands.paste(); return True
        if vk == VK_S:
            self.commands.save_current(); return True
        return True

    def _handle_tool_key(self, vk):
        tool_map = {
            VK_1: Tool.ADD_LINE,
            VK_2: Tool.ADD_PAD,
            VK_3: Tool.ADD_CIRCLE,
            VK_4: Tool.ADD_ARC,
            VK_5: Tool.ADD_TEXT,
        }
        if vk in tool_map:
            tool = tool_map[vk]
            self._on_drawing_tool(tool)
            self.tool_bar.set_active(tool)
            return True
        return False

    def _handle_nav_key(self, vk):
        if vk == VK_R:
            self.commands.rotate_selected(); return True
        if vk == VK_F11:
            self.toggle_fullscreen(); return True
        if vk in PAN_KEYS:
            self.canvas.pressed_keys.add(vk)
            if not self.canvas.pan_timer.isActive():
                self.canvas.pan_timer.start()
            return True
        if vk == VK_ESCAPE:
            self.finish_drawing()
            self.canvas.scene.clearSelection()
            self._set_tool(Tool.SELECT)
            return True
        if vk == VK_DELETE:
            self.commands.delete_selected(); return True
        if vk == VK_F1:
            self._change_grid_step(-1); return True
        if vk == VK_F2:
            self._change_grid_step(1); return True
        if vk == VK_F3:
            self._toggle_grid_series(); return True
        return False