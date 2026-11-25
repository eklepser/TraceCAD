from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QWidget,
)
from constants import Styles
from common.ui.dialogs.headerless_dialog import HeaderlessDialog
from common.ui.qss import TABLE_QSS
from pbe_editor.core.autoplacer import OptimizationMode
from pbe_editor.core.pairwise_placer import PairwiseAlgoVersion, PairwiseDirectiveMode


VERSION_LABELS = {
    PairwiseAlgoVersion.VERSION_1: "Реализация 1 (матричная)",
    PairwiseAlgoVersion.VERSION_2: "Реализация 2 (упорядоченная)",
}

DIRECTIVE_LABELS = {
    PairwiseDirectiveMode.NONE: "Отсутствует",
    PairwiseDirectiveMode.LARGEST: "Самый крупный",
    PairwiseDirectiveMode.MOST_CONNECTED: "Самый связанный",
}

OPT_MODE_LABELS = {
    OptimizationMode.NONE: "Без оптимизации",
    OptimizationMode.D_C: "d = C",
    OptimizationMode.D_C2: "d = C/2",
    OptimizationMode.D_C4: "d = C/4",
}


class PairwiseResultDialog(HeaderlessDialog):
    RESULT_OK = 1
    RESULT_REPEAT = 2

    def __init__(self, result, params, initial_wire_euc, initial_wire_man, parent=None):
        super().__init__(parent, title="Результаты парных перестановок")
        has_opt = params.optimization_mode != OptimizationMode.NONE
        self.setMinimumSize(720 if has_opt else 620, 580)

        self._result = result
        self._params = params
        self._code = self.RESULT_OK

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        header = QLabel("Результаты авторазмещения (парные перестановки)")
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)

        version_text = VERSION_LABELS.get(params.algo_version, params.algo_version.value)
        metric_text = "Евклидова" if params.metric.value == "euclidean" else "Ортогональная"
        dir_text = DIRECTIVE_LABELS.get(params.directive_mode, params.directive_mode.value)
        opt_text = OPT_MODE_LABELS.get(params.optimization_mode, params.optimization_mode.value)

        board_lbl = QLabel(
            "Ширина платы: <b>{0:.2f} мм</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Длина платы: <b>{1:.2f} мм</b>".format(result.board_width, result.board_length)
        )
        board_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(board_lbl)

        scheme_lbl = QLabel(
            "Корпусов: <b>{0}</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Связей: <b>{1}</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Сдвинуто с границы: <b>{2}</b>".format(
                result.num_footprints, result.num_connections, result.shifted_count
            )
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

        algo_lbl = QLabel(
            "Реализация: <b>{0}</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Метрика: <b>{1}</b>".format(version_text, metric_text)
        )
        algo_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(algo_lbl)

        fix_lbl = QLabel(
            "Директивный элемент: <b>{0}</b> ({1})&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "Локальная оптимизация: <b>{2}</b>".format(
                dir_text, result.directive_ref or "-", opt_text
            )
        )
        fix_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(fix_lbl)

        spacer_top = QWidget()
        spacer_top.setFixedHeight(8)
        layout.addWidget(spacer_top)

        if has_opt:
            headers = ["Показатель", "До размещения", "После перестановок", "После оптимизации"]
        else:
            headers = ["Показатель", "До размещения", "После перестановок"]

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
                (
                    "Длина по Евклиду, мм",
                    f"{initial_wire_euc:.2f}",
                    self._pct_cell(initial_wire_euc, result.pair_wire_euclidean),
                    self._pct_cell(result.pair_wire_euclidean, result.wire_euclidean),
                ),
                (
                    "Длина по Манхэттену, мм",
                    f"{initial_wire_man:.2f}",
                    self._pct_cell(initial_wire_man, result.pair_wire_manhattan),
                    self._pct_cell(result.pair_wire_manhattan, result.wire_manhattan),
                ),
            ]
        else:
            rows = [
                (
                    "Длина по Евклиду, мм",
                    f"{initial_wire_euc:.2f}",
                    self._pct_cell(initial_wire_euc, result.wire_euclidean),
                ),
                (
                    "Длина по Манхэттену, мм",
                    f"{initial_wire_man:.2f}",
                    self._pct_cell(initial_wire_man, result.wire_manhattan),
                ),
            ]

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(val))

        spacer_bottom = QWidget()
        spacer_bottom.setFixedHeight(6)
        layout.addWidget(spacer_bottom)

        pair_time_lbl = QLabel(
            "Время парных перестановок: <b>{0:.1f} мс</b>".format(result.pair_time_seconds * 1000)
        )
        pair_time_lbl.setStyleSheet("color: #a9b7c6;")
        layout.addWidget(pair_time_lbl)

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