from PySide6.QtWidgets import QMessageBox
from pbe_editor.ui.dialogs.pairwise_dialog import PairwiseDialog
from pbe_editor.ui.dialogs.pairwise_result_dialog import PairwiseResultDialog
from pbe_editor.core.pairwise_placer import PairwiseParams, run_pairwise_placement


class PairwiseCommandsMixin:
    def __init__(self):
        self._last_pairwise_params = PairwiseParams()

    def _apply_pairwise_positions(self, positions):
        for i, module in enumerate(self.w.board.modules):
            if i in positions:
                module.x, module.y = positions[i]
                module.angle = 0.0
                item = self.w.manager.items.get(module.uid)
                if item:
                    item.setPos(module.x, module.y)
                    item.setRotation(0.0)
                    item.prepareGeometryChange()
                    item.update()

    def _restore_pairwise_initial_positions(self, initial_positions):
        for i, (x, y, angle) in initial_positions.items():
            module = self.w.board.modules[i]
            module.x = x
            module.y = y
            module.angle = angle
            item = self.w.manager.items.get(module.uid)
            if item:
                item.setPos(module.x, module.y)
                item.setRotation(angle)
                item.prepareGeometryChange()
                item.update()
        self.w.manager.rebuild_ratsnest()

    def on_pairwise_autoplace(self):
        if not self.w.board.modules:
            QMessageBox.information(self.w, "Информация", "На плате нет модулей для размещения.")
            return

        has_edge = any(line.layer == "Edge.Cuts" for line in self.w.board.lines)
        if not has_edge:
            QMessageBox.warning(
                self.w,
                "Ошибка",
                "На плате не нарисован контур (Edge.Cuts). Авторазмещение невозможно.",
            )
            return

        initial_positions = {i: (m.x, m.y, m.angle) for i, m in enumerate(self.w.board.modules)}

        while True:
            dlg = PairwiseDialog(self.w, self._last_pairwise_params)
            if dlg.exec() != PairwiseDialog.Accepted:
                return

            params = dlg.get_params()
            self._last_pairwise_params = params

            self._restore_pairwise_initial_positions(initial_positions)

            try:
                result, before_euc, before_man = run_pairwise_placement(self.w.board, params)
            except Exception as e:
                QMessageBox.critical(self.w, "Ошибка", str(e))
                self._restore_pairwise_initial_positions(initial_positions)
                return

            self._apply_pairwise_positions(result.positions)
            self.w.manager.rebuild_ratsnest()
            self.w.commit_snapshot()
            self.w.show_log(
                f"Парные перестановки выполнены (сдвинуто с границы: {result.shifted_count})"
            )

            result_dlg = PairwiseResultDialog(
                result, params, before_euc, before_man, self.w
            )
            result_dlg.exec()

            if result_dlg.get_code() == PairwiseResultDialog.RESULT_REPEAT:
                continue
            return