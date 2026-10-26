from constants import GRID_SERIES, GRID_SERIES_LABEL


SETTINGS_KEY_BRD_GRID_MODE = "brd_grid_mode"


class GridService:
    def _load_grid_mode(self):
        mode = self._settings.value(SETTINGS_KEY_BRD_GRID_MODE, "1x", type=str)
        return mode if mode in GRID_SERIES else "1x"

    def _persist_grid_mode(self, mode):
        self._settings.setValue(SETTINGS_KEY_BRD_GRID_MODE, mode)
        self._settings.sync()

    def apply_grid_series(self, mode, initial=False):
        if mode not in GRID_SERIES:
            return
        self.grid_mode = mode
        self._persist_grid_mode(mode)
        for m, act in self._grid_actions.items():
            act.setChecked(m == mode)
        idx = self.grid_series_combo.findData(mode)
        if idx >= 0 and self.grid_series_combo.currentIndex() != idx:
            self.grid_series_combo.blockSignals(True)
            self.grid_series_combo.setCurrentIndex(idx)
            self.grid_series_combo.blockSignals(False)
        values = GRID_SERIES[mode]
        self.grid_combo.blockSignals(True)
        self.grid_combo.clear()
        self.grid_combo.addItems(values)
        default = "1.000" if mode == "1x" else "1.270"
        self.grid_combo.setCurrentText(default if default in values else values[0])
        self.grid_combo.blockSignals(False)
        self.canvas.set_grid_size(float(self.grid_combo.currentText()))
        if not initial:
            self.show_log(f"Ряд сетки: {GRID_SERIES_LABEL[mode]}")

    def toggle_grid_series(self):
        self.apply_grid_series("1.27x" if self.grid_mode == "1x" else "1x")

    def toggle_grid(self):
        self.canvas.show_grid = self.act_show_grid.isChecked()
        self.canvas.viewport().update()

    def on_grid_changed(self, text):
        if not text:
            return
        self.canvas.set_grid_size(float(text))
        self.canvas.setFocus()

    def change_grid_step(self, direction):
        i = self.grid_combo.currentIndex() + direction
        if 0 <= i < self.grid_combo.count():
            self.grid_combo.setCurrentIndex(i)

    def update_zoom_label(self, zoom):
        self.zoom_label.setText(f" {int(zoom * 100)}% ")