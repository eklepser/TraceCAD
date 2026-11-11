from PySide6.QtWidgets import QMessageBox
from pbe_editor.ui.dialogs.autoplace_dialog import AutoPlaceDialog
from pbe_editor.ui.dialogs.autoplace_result_dialog import AutoPlaceResultDialog
from pbe_editor.core.autoplacer import run_auto_placement


class AutoplaceCommandsMixin:
    def __init__(self):
        self._last_params = None
        self._last_threads = 1

    def _apply_positions(self, positions):
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

    def _restore_initial_positions(self, initial_positions):
        for i, (x, y) in initial_positions.items():
            module = self.w.board.modules[i]
            module.x = x
            module.y = y
            module.angle = 0.0
            item = self.w.manager.items.get(module.uid)
            if item:
                item.setPos(module.x, module.y)
                item.setRotation(0.0)
                item.prepareGeometryChange()
                item.update()
        self.w.manager.rebuild_ratsnest()

    def on_autoplace(self):
        if not self.w.board.modules:
            QMessageBox.information(self.w, "Информация", "На плате нет модулей для размещения.")
            return

        has_edge = any(line.layer == "Edge.Cuts" for line in self.w.board.lines)
        if not has_edge:
            QMessageBox.warning(self.w, "Ошибка",
                                "На плате не нарисован контур (Edge.Cuts). Авторазмещение невозможно.")
            return

        initial_positions = {i: (m.x, m.y) for i, m in enumerate(self.w.board.modules)}

        dlg = AutoPlaceDialog(self.w, self._last_params, self._last_threads)

        while True:
            if dlg.exec() != AutoPlaceDialog.Accepted:
                return

            params = dlg.get_params()
            threads = dlg.get_threads()
            self._last_params = params
            self._last_threads = threads

            self._restore_initial_positions(initial_positions)

            try:
                result, before_euc, before_man = run_auto_placement(self.w.board, params, threads)
            except Exception as e:
                QMessageBox.critical(self.w, "Ошибка", str(e))
                self._restore_initial_positions(initial_positions)
                return

            self._apply_positions(result.positions)
            self.w.manager.rebuild_ratsnest()
            self.w.commit_snapshot()
            self.w.show_log("Авторазмещение выполнено")

            result_dlg = AutoPlaceResultDialog(
                result, params, result.threads_used, before_euc, before_man, self.w
            )
            result_dlg.exec()

            if result_dlg.get_code() == AutoPlaceResultDialog.RESULT_REPEAT:
                dlg = AutoPlaceDialog(self.w, self._last_params, self._last_threads)
                continue
            return

    def on_reset_placement(self):
        if not self.w.board.modules:
            QMessageBox.information(self.w, "Информация", "На плате нет модулей.")
            return

        for module in self.w.board.modules:
            module.x = 0.0
            module.y = 0.0
            module.angle = 0.0
            item = self.w.manager.items.get(module.uid)
            if item:
                item.setPos(0.0, 0.0)
                item.setRotation(0.0)
                item.prepareGeometryChange()
                item.update()

        self.w.manager.rebuild_ratsnest()
        self.w.commit_snapshot()
        self.w.show_log("Размещение сброшено: все элементы в (0, 0)")