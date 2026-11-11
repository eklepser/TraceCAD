from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QPushButton, QHeaderView, QWidget)
from constants import Styles
from common.ui.dialogs.headerless_dialog import HeaderlessDialog
from common.ui.qss import TABLE_QSS
from pbe_editor.core.autoplacer import JMethod


J_METHOD_LABELS = {
    JMethod.M_331: "3.3.1 (Макс. связь)",
    JMethod.M_333: "3.3.3 (Сумма связей)",
    JMethod.M_335: "3.3.5 (Разность связей)",
    JMethod.M_336: "3.3.6 (Отн. связность)",
}


class AutoPlaceResultDialog(HeaderlessDialog):
    RESULT_OK = 1
    RESULT_REPEAT = 2

    def __init__(self, result, params, threads,
                 initial_wire_euc, initial_wire_man, parent=None):
        super().__init__(parent, title="Результаты авторазмещения")
        self.setMinimumSize(700, 540)

        self._result = result
        self._params = params
        self._threads = threads
        self._code = self.RESULT_OK

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        header = QLabel("Результаты авторазмещения")
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)

        metric_text = "Евклидова" if params.metric.value == "euclidean" else "Ортогональная"
        mode_text = "Крупнейший" if params.directive_mode.value == "largest" else "Связнейший"
        pos_text = {
            "center": "Центр",
            "top_left": "Левый верхний",
            "bottom_left": "Левый нижний",
        }.get(params.directive_position.value, "-")
        method_text = J_METHOD_LABELS.get(params.j_method, params.j_method.value)

        scheme_lbl = QLabel(
            "Корпусов: <b>{0}</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Связей: <b>{1}</b>".format(result.num_footprints, result.num_connections)
        )
        scheme_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(scheme_lbl)

        geom_lbl = QLabel(
            "Отступ A: <b>{0:.2f} мм</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Зазор B: <b>{1:.2f} мм</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Шаг сетки C: <b>{2:.2f} мм</b>".format(params.A, params.B, params.C)
        )
        geom_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(geom_lbl)

        metric_lbl = QLabel("Используемая метрика: <b>{0}</b>".format(metric_text))
        metric_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(metric_lbl)

        method_lbl = QLabel("Способ расчета оценки: <b>{0}</b>".format(method_text))
        method_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(method_lbl)

        fix_lbl = QLabel(
            "Режим фиксации: <b>{0}</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Позиция: <b>{1}</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Элемент: <b>{2}</b>".format(mode_text, pos_text, result.directive_ref or "-")
        )
        fix_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(fix_lbl)

        spacer_top = QWidget()
        spacer_top.setFixedHeight(8)
        layout.addWidget(spacer_top)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Показатель", "До размещения", "После размещения", "Сравнение"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(TABLE_QSS)
        layout.addWidget(self.table)

        rows = [
            ("Длина по Евклиду, мм",
             f"{initial_wire_euc:.2f}",
             f"{result.wire_euclidean:.2f}",
             self._delta(initial_wire_euc, result.wire_euclidean)),
            ("Длина по Манхэттену, мм",
             f"{initial_wire_man:.2f}",
             f"{result.wire_manhattan:.2f}",
             self._delta(initial_wire_man, result.wire_manhattan)),
        ]

        self.table.setRowCount(len(rows))
        for i, (k, before, after, cmp) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(k))
            self.table.setItem(i, 1, QTableWidgetItem(before))
            self.table.setItem(i, 2, QTableWidgetItem(after))
            self.table.setItem(i, 3, QTableWidgetItem(cmp))

        spacer_bottom = QWidget()
        spacer_bottom.setFixedHeight(6)
        layout.addWidget(spacer_bottom)

        time_lbl = QLabel("Время размещения: <b>{0:.1f} мс</b>".format(result.time_seconds * 1000))
        time_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(time_lbl)

        threads_lbl = QLabel("Использовано потоков: <b>{0}</b>".format(threads))
        threads_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(threads_lbl)

        btns = QHBoxLayout()
        btns.addStretch()

        self.btn_repeat = QPushButton("Повторить")
        self.btn_repeat.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_repeat.clicked.connect(self._on_repeat)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setStyleSheet(Styles.BUTTON_OK)
        self.btn_ok.clicked.connect(self.accept)

        btns.addWidget(self.btn_repeat)
        btns.addWidget(self.btn_ok)
        layout.addLayout(btns)

    def _delta(self, before, after):
        if before <= 0:
            return "-"
        diff = after - before
        pct = diff / before * 100
        return f"{diff:+.2f} ({pct:+.1f} %)"

    def _on_repeat(self):
        self._code = self.RESULT_REPEAT
        self.accept()

    def get_code(self):
        return self._code