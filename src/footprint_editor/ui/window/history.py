class HistoryService:
    def commit_history(self, *_args):
        self._modified = True
        self.unsaved_modules[self.current_module_name] = self.footprint
        self.refresh_module_list_display()

        self.history.push(self.footprint)
        self._update_history_buttons()

    def undo(self):
        snapshot = self.history.undo()
        if snapshot is None:
            return
        self._restore_footprint(snapshot)
        self._update_history_buttons()
        self.show_log("отменено")

    def redo(self):
        snapshot = self.history.redo()
        if snapshot is None:
            return
        self._restore_footprint(snapshot)
        self._update_history_buttons()
        self.show_log("повторено")

    def _restore_footprint(self, snapshot):
        name = self.current_module_name
        self.footprint = snapshot
        self.footprint.name = name
        self.manager.footprint = self.footprint

        self.canvas.scene.clear()
        self.manager.items.clear()
        self._populate_scene(self.footprint)
        self.commands.ensure_reference_and_value()
        self.right_panel.properties_panel.clear_panel()
        self.unsaved_modules[self.current_module_name] = self.footprint

    def _update_history_buttons(self):
        self.aux_bar.set_undo_enabled(self.history.can_undo())
        self.aux_bar.set_redo_enabled(self.history.can_redo())