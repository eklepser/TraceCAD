from PySide6.QtCore import QEvent, Qt

from constants import (
    PAN_KEYS,
    VK_ESCAPE, VK_DELETE, VK_F1, VK_F2, VK_F3, VK_F11, VK_G,
    VK_R, VK_L, VK_O,
)


class KeyboardService:
    def handle_key_press(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.exit_to_select_mode()
            return True
        vk = event.nativeVirtualKey()
        if vk == VK_O:
            self.act_show_values.setChecked(not self.act_show_values.isChecked())
            self.toggle_values()
            return True
        if vk == VK_DELETE:
            self.commands.delete_selected()
            return True
        if vk == VK_R:
            self.commands.rotate_selected()
            return True
        if vk == VK_L:
            self.act_show_ratsnest.setChecked(not self.act_show_ratsnest.isChecked())
            self.on_toggle_ratsnest()
            return True
        if vk == VK_G:
            self.act_show_grid.setChecked(not self.act_show_grid.isChecked())
            self.toggle_grid()
            return True
        if vk == VK_F11:
            self.toggle_fullscreen()
            return True
        if vk == VK_F1:
            self.change_grid_step(-1)
            return True
        if vk == VK_F2:
            self.change_grid_step(1)
            return True
        if vk == VK_F3:
            self.toggle_grid_series()
            return True
        if vk in PAN_KEYS:
            self.canvas.pressed_keys.add(vk)
            if not self.canvas.pan_timer.isActive():
                self.canvas.pan_timer.start()
            return True
        return False

    def handle_key_release(self, event):
        vk = event.nativeVirtualKey()
        if vk in PAN_KEYS:
            self.canvas.pressed_keys.discard(vk)
            if not self.canvas.pressed_keys:
                self.canvas.pan_timer.stop()
            return True
        return False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if self.handle_key_press(event):
                return True
        elif event.type() == QEvent.Type.KeyRelease:
            if self.handle_key_release(event):
                return True
        return super().eventFilter(obj, event)