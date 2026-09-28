from constants import GRID_SERIES, GRID_SERIES_LABEL


class GridService:
    def _grid_series(self):
        return GRID_SERIES

    def _apply_grid_series(self, mode, initial=False):
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

    def _toggle_grid_series(self):
        self._apply_grid_series("1.27x" if self.grid_mode == "1x" else "1x")

    def _on_grid_changed(self, text):
        if not text:
            return
        self.canvas.set_grid_size(float(text))
        self.canvas.setFocus()

    def _change_grid_step(self, direction):
        i = self.grid_combo.currentIndex() + direction
        if 0 <= i < self.grid_combo.count():
            self.grid_combo.setCurrentIndex(i)

    def _update_zoom_label(self, zoom):
        self.zoom_label.setText(f" {int(zoom * 100)}% ")