from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QPushButton, QHeaderView, QWidget)
from constants import Styles
from common.ui.dialogs.headerless_dialog import HeaderlessDialog
from common.ui.qss import TABLE_QSS
from pbe_editor.core.autoplacer import JMethod, OptimizationMode


J_METHOD_LABELS = {
    JMethod.M_331: "3.3.1 (Макс. связь)",
    JMethod.M_333: "3.3.3 (Сумма связей)",
    JMethod.M_335: "3.3.5 (Разность связей)",
    JMethod.M_336: "3.3.6 (Отн. связность)",
}

OPT_MODE_LABELS = {
    OptimizationMode.NONE: "Без оптимизации",
    OptimizationMode.D_C: "d = C",
    OptimizationMode.D_C2: "d = C/2",
    OptimizationMode.D_C4: "d = C/4",
}


class AutoPlaceResultDialog(HeaderlessDialog):
    RESULT_OK = 1
    RESULT_REPEAT = 2

    def __init__(self, result, params, threads,
                 initial_wire_euc, initial_wire_man, parent=None):
        super().__init__(parent, title="Результаты авторазмещения")
        has_opt = params.optimization_mode != OptimizationMode.NONE
        self.setMinimumSize(720 if has_opt else 620, 580)

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
        mode_text = "Самый крупный" if params.directive_mode.value == "largest" else "Самый связанный"
        pos_text = {
            "center": "Центр",
            "top_left": "Левый верхний",
            "bottom_left": "Левый нижний",
        }.get(params.directive_position.value, "-")
        method_text = J_METHOD_LABELS.get(params.j_method, params.j_method.value)
        opt_text = OPT_MODE_LABELS.get(params.optimization_mode, params.optimization_mode.value)

        board_lbl = QLabel(
            "Ширина платы: <b>{0:.2f} мм</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Длина платы: <b>{1:.2f} мм</b>".format(result.board_width, result.board_length)
        )
        board_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(board_lbl)

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

        method_lbl = QLabel(
            "Способ расчета оценки: <b>{0}</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Локальная оптимизация: <b>{1}</b>".format(method_text, opt_text)
        )
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

        if has_opt:
            headers = ["Показатель", "До размещения", "После размещения", "После оптимизации"]
        else:
            headers = ["Показатель", "До размещения", "После размещения"]

        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for col in range(1, len(headers)):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(TABLE_QSS)
        layout.addWidget(self.table)

        if has_opt:
            rows = [
                ("Длина по Евклиду, мм",
                 f"{initial_wire_euc:.2f}",
                 self._pct_cell(initial_wire_euc, result.seq_wire_euclidean),
                 self._pct_cell(result.seq_wire_euclidean, result.wire_euclidean)),
                ("Длина по Манхэттену, мм",
                 f"{initial_wire_man:.2f}",
                 self._pct_cell(initial_wire_man, result.seq_wire_manhattan),
                 self._pct_cell(result.seq_wire_manhattan, result.wire_manhattan)),
            ]
        else:
            rows = [
                ("Длина по Евклиду, мм",
                 f"{initial_wire_euc:.2f}",
                 self._pct_cell(initial_wire_euc, result.wire_euclidean)),
                ("Длина по Манхэттену, мм",
                 f"{initial_wire_man:.2f}",
                 self._pct_cell(initial_wire_man, result.wire_manhattan)),
            ]

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(val))

        spacer_bottom = QWidget()
        spacer_bottom.setFixedHeight(6)
        layout.addWidget(spacer_bottom)

        seq_time_lbl = QLabel(
            "Время последовательного размещения: <b>{0:.1f} мс</b>".format(result.seq_time_seconds * 1000)
        )
        seq_time_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(seq_time_lbl)

        opt_time_lbl = QLabel(
            "Время локальной оптимизации: <b>{0:.1f} мс</b>".format(result.opt_time_seconds * 1000)
        )
        opt_time_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(opt_time_lbl)

        total_time_lbl = QLabel(
            "Общее время: <b>{0:.1f} мс</b>".format(result.time_seconds * 1000)
        )
        total_time_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(total_time_lbl)

        threads_lbl = QLabel("Использовано потоков: <b>{0}</b>".format(result.threads_used))
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

    def _pct_cell(self, before, after):
        if before <= 0:
            return f"{after:.2f}"
        pct = (after - before) / before * 100
        return f"{after:.2f} ({pct:+.1f} %)"

    def _on_repeat(self):
        self._code = self.RESULT_REPEAT
        self.accept()

    def get_code(self):
        return self._code