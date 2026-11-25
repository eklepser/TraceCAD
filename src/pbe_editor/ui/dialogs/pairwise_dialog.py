from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QPushButton,
    QFormLayout,
    QGroupBox,
    QListView,
)
from constants import Styles
from common.ui.dialogs.headerless_dialog import HeaderlessDialog
from common.ui.qss import inline_combo_qss
from pbe_editor.core.autoplacer import Metric, OptimizationMode
from pbe_editor.core.pairwise_placer import (
    PairwiseParams,
    PairwiseAlgoVersion,
    PairwiseDirectiveMode,
)

LAYER_LIST_QSS = (
    "QListView { background-color: #2b2b2b; color: #a9b7c6;"
    " border: 1px solid #555555; outline: 0; }"
    "QListView::item { padding: 4px 8px; }"
    "QListView::item:hover { background-color: #3c3f41; }"
    "QListView::item:selected { background-color: #365880; color: #ffffff; }"
)


def _styled_combo(items):
    combo = QComboBox()
    for label, data in items:
        combo.addItem(label, data)
    view = QListView()
    view.setStyleSheet(LAYER_LIST_QSS)
    combo.setView(view)
    combo.setStyleSheet(inline_combo_qss())
    combo.setMinimumHeight(24)
    return combo


class PairwiseDialog(HeaderlessDialog):
    def __init__(self, parent=None, initial_params: PairwiseParams = None):
        super().__init__(parent, title="Авторазмещение (парные перестановки)")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("Авторазмещение методом парных перестановок")
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)

        columns = QHBoxLayout()
        columns.setSpacing(16)

        left_col = QVBoxLayout()
        right_col = QVBoxLayout()

        group_geom = QGroupBox("Геометрия")
        group_geom.setStyleSheet(Styles.MAIN_WINDOW)
        form_geom = QFormLayout(group_geom)
        form_geom.setSpacing(6)

        self.sb_A = QDoubleSpinBox()
        self.sb_A.setRange(0.1, 100.0)
        self.sb_A.setValue(2.0)
        self.sb_A.setSuffix(" мм")
        self.sb_A.setStyleSheet(Styles.INPUT_BG)
        form_geom.addRow("Отступ A:", self.sb_A)

        self.sb_B = QDoubleSpinBox()
        self.sb_B.setRange(0.1, 100.0)
        self.sb_B.setValue(2.0)
        self.sb_B.setSuffix(" мм")
        self.sb_B.setStyleSheet(Styles.INPUT_BG)
        form_geom.addRow("Зазор B:", self.sb_B)

        self.sb_C = QDoubleSpinBox()
        self.sb_C.setRange(0.1, 10.0)
        self.sb_C.setValue(1.25)
        self.sb_C.setSuffix(" мм")
        self.sb_C.setStyleSheet(Styles.INPUT_BG)
        form_geom.addRow("Шаг сетки C:", self.sb_C)

        left_col.addWidget(group_geom)

        group_algo = QGroupBox("Алгоритм")
        group_algo.setStyleSheet(Styles.MAIN_WINDOW)
        form_algo = QFormLayout(group_algo)
        form_algo.setSpacing(6)

        self.cb_version = _styled_combo(
            [
                ("Реализация 1 (матричная)", PairwiseAlgoVersion.VERSION_1),
                ("Реализация 2 (упорядоченная)", PairwiseAlgoVersion.VERSION_2),
            ]
        )
        form_algo.addRow("Реализация алгоритма:", self.cb_version)

        self.cb_metric = _styled_combo(
            [
                ("Евклидова", Metric.EUCLIDEAN),
                ("Ортогональная", Metric.MANHATTAN),
            ]
        )
        form_algo.addRow("Используемая метрика:", self.cb_metric)

        self.cb_directive = _styled_combo(
            [
                ("Отсутствует", PairwiseDirectiveMode.NONE),
                ("Самый крупный", PairwiseDirectiveMode.LARGEST),
                ("Самый связанный", PairwiseDirectiveMode.MOST_CONNECTED),
            ]
        )
        form_algo.addRow("Директивный элемент:", self.cb_directive)

        self.cb_opt_mode = _styled_combo(
            [
                ("Без оптимизации", OptimizationMode.NONE),
                ("d = C", OptimizationMode.D_C),
                ("d = C/2", OptimizationMode.D_C2),
                ("d = C/4", OptimizationMode.D_C4),
            ]
        )
        self.cb_opt_mode.setCurrentIndex(2)
        form_algo.addRow("Локальная оптимизация:", self.cb_opt_mode)

        right_col.addWidget(group_algo)

        columns.addLayout(left_col, 1)
        columns.addLayout(right_col, 1)
        layout.addLayout(columns)

        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_ok = QPushButton("Запустить")
        self.btn_ok.setStyleSheet(Styles.BUTTON_OK)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setStyleSheet(Styles.BUTTON_CANCEL)
        self.btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        if initial_params:
            self.set_params(initial_params)

    def set_params(self, p: PairwiseParams):
        self.sb_A.setValue(p.A)
        self.sb_B.setValue(p.B)
        self.sb_C.setValue(p.C)

        idx = self.cb_version.findData(p.algo_version)
        if idx >= 0:
            self.cb_version.setCurrentIndex(idx)

        idx = self.cb_metric.findData(p.metric)
        if idx >= 0:
            self.cb_metric.setCurrentIndex(idx)

        idx = self.cb_directive.findData(p.directive_mode)
        if idx >= 0:
            self.cb_directive.setCurrentIndex(idx)

        idx = self.cb_opt_mode.findData(p.optimization_mode)
        if idx >= 0:
            self.cb_opt_mode.setCurrentIndex(idx)

    def get_params(self) -> PairwiseParams:
        return PairwiseParams(
            A=self.sb_A.value(),
            B=self.sb_B.value(),
            C=self.sb_C.value(),
            algo_version=self.cb_version.currentData(),
            metric=self.cb_metric.currentData(),
            directive_mode=self.cb_directive.currentData(),
            optimization_mode=self.cb_opt_mode.currentData(),
        )