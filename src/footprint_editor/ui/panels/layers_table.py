from PySide6.QtWidgets import QWidget, QGridLayout, QCheckBox
from PySide6.QtCore import Signal


LAYER_LABELS = {
    "F.Cu": "Front",
    "B.Cu": "Back",
    "F.Adhes": "Adhes_Front",
    "B.Adhes": "Adhes_Back",
    "F.Paste": "SoldP_Front",
    "B.Paste": "SoldP_Back",
    "F.SilkS": "SilkS_Front",
    "B.SilkS": "SilkS_Back",
    "F.Mask": "Mask_Front",
    "B.Mask": "Mask_Back",
    "Cmts.User": "Чертёж",
    "Eco1.User": "Eco1",
    "Eco2.User": "Eco2",
}


CHECKBOX_QSS = (
    "QCheckBox { color: #d8d8d8; spacing: 8px; background: transparent; }"
    "QCheckBox::indicator { width: 14px; height: 14px;"
    " border: 1px solid #d8d8d8; background-color: #2b2b2b;"
    " border-radius: 2px; }"
    "QCheckBox::indicator:hover { border: 1px solid #ffffff; }"
    "QCheckBox::indicator:checked {"
    " border: 1px solid #ffffff; background-color: #365880; }"
)


class LayersTable(QWidget):
    layers_changed = Signal(list)

    def __init__(self, parent=None, multi=True):
        super().__init__(parent)
        self.multi = multi
        self._updating = False

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(4)

        self.checkboxes = {}

        rows = [
            ("F.Cu", "B.Cu"),
            ("F.Adhes", "B.Adhes"),
            ("F.Paste", "B.Paste"),
            ("F.SilkS", "B.SilkS"),
            ("F.Mask", "B.Mask"),
            ("Cmts.User", None),
            ("Eco1.User", None),
            ("Eco2.User", None),
        ]

        for row, (left, right) in enumerate(rows):
            cb_left = self._make_cb(left)
            layout.addWidget(cb_left, row, 0)
            if right is not None:
                cb_right = self._make_cb(right)
                layout.addWidget(cb_right, row, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

    def _make_cb(self, layer):
        cb = QCheckBox(LAYER_LABELS.get(layer, layer))
        cb.setProperty("layer_id", layer)
        cb.setStyleSheet(CHECKBOX_QSS)
        cb.stateChanged.connect(self._on_changed)
        self.checkboxes[layer] = cb
        return cb

    def set_layers(self, layers):
        self._updating = True
        try:
            layers = set(layers or [])
            for layer, cb in self.checkboxes.items():
                cb.blockSignals(True)
                cb.setChecked(layer in layers)
                cb.blockSignals(False)
        finally:
            self._updating = False

    def selected_layers(self):
        return [l for l, cb in self.checkboxes.items() if cb.isChecked()]

    def _on_changed(self, _state):
        if self._updating:
            return
        if not self.multi:
            sender = self.sender()
            if sender.isChecked():
                self._updating = True
                for cb in self.checkboxes.values():
                    if cb is not sender:
                        cb.blockSignals(True)
                        cb.setChecked(False)
                        cb.blockSignals(False)
                self._updating = False
        self.layers_changed.emit(self.selected_layers())