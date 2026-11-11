from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                               QSpinBox, QDoubleSpinBox, QPushButton, QFormLayout)
from constants import Styles
from common.ui.dialogs.headerless_dialog import HeaderlessDialog
from pbe_editor.core.autoplacer import (
    PlacementParams, Metric, DirectiveMode, DirectivePosition, JMethod
)

class AutoPlaceDialog(HeaderlessDialog):
    def __init__(self, parent=None):
        super().__init__(parent, title="Авторазмещение")
        self.setMinimumWidth(380)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        
        header = QLabel("Авторазмещение элементов")
        header.setStyleSheet(Styles.OBJECT_TITLE)
        layout.addWidget(header)
        
        form = QFormLayout()
        form.setSpacing(6)
        
        self.sb_A = QDoubleSpinBox()
        self.sb_A.setRange(0.1, 100.0)
        self.sb_A.setValue(2.0)
        self.sb_A.setSuffix(" мм")
        self.sb_A.setStyleSheet(Styles.INPUT_BG)
        form.addRow("Отступ A:", self.sb_A)
        
        self.sb_B = QDoubleSpinBox()
        self.sb_B.setRange(0.1, 100.0)
        self.sb_B.setValue(2.0)
        self.sb_B.setSuffix(" мм")
        self.sb_B.setStyleSheet(Styles.INPUT_BG)
        form.addRow("Зазор B:", self.sb_B)
        
        self.sb_C = QDoubleSpinBox()
        self.sb_C.setRange(0.1, 10.0)
        self.sb_C.setValue(1.25)
        self.sb_C.setSuffix(" мм")
        self.sb_C.setStyleSheet(Styles.INPUT_BG)
        form.addRow("Шаг сетки C:", self.sb_C)
        
        self.cb_metric = QComboBox()
        self.cb_metric.addItem("Евклидова", Metric.EUCLIDEAN)
        self.cb_metric.addItem("Ортогональная", Metric.MANHATTAN)
        self.cb_metric.setStyleSheet(Styles.INPUT_BG)
        form.addRow("Метрика для F:", self.cb_metric)
        
        self.cb_j = QComboBox()
        self.cb_j.addItem("3.3.1 (Макс. связь с размещ.)", JMethod.M_331)
        self.cb_j.addItem("3.3.3 (Сумма связей)", JMethod.M_333)
        self.cb_j.addItem("3.3.5 (Разность связей)", JMethod.M_335)
        self.cb_j.addItem("3.3.6 (Относительная связность)", JMethod.M_336)
        self.cb_j.setStyleSheet(Styles.INPUT_BG)
        form.addRow("Оценка J:", self.cb_j)
        
        self.cb_mode = QComboBox()
        self.cb_mode.addItem("Самый крупный", DirectiveMode.LARGEST)
        self.cb_mode.addItem("Самый связанный", DirectiveMode.MOST_CONNECTED)
        self.cb_mode.setStyleSheet(Styles.INPUT_BG)
        form.addRow("Фиксированный элемент:", self.cb_mode)
        
        self.cb_pos = QComboBox()
        self.cb_pos.addItem("По центру", DirectivePosition.CENTER)
        self.cb_pos.addItem("Левый верхний угол", DirectivePosition.TOP_LEFT)
        self.cb_pos.addItem("Левый нижний угол", DirectivePosition.BOTTOM_LEFT)
        self.cb_pos.setStyleSheet(Styles.INPUT_BG)
        form.addRow("Позиция фиксации:", self.cb_pos)
        
        self.sb_threads = QSpinBox()
        self.sb_threads.setRange(1, 16)
        self.sb_threads.setValue(1)
        self.sb_threads.setStyleSheet(Styles.INPUT_BG)
        form.addRow("Потоков:", self.sb_threads)
        
        layout.addLayout(form)
        
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
        
    def get_params(self) -> PlacementParams:
        return PlacementParams(
            A=self.sb_A.value(),
            B=self.sb_B.value(),
            C=self.sb_C.value(),
            metric=self.cb_metric.currentData(),
            j_method=self.cb_j.currentData(),
            directive_mode=self.cb_mode.currentData(),
            directive_position=self.cb_pos.currentData()
        )
        
    def get_threads(self) -> int:
        return self.sb_threads.value()