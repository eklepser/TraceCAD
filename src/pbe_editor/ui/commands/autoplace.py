from PySide6.QtWidgets import QMessageBox
from pbe_editor.ui.dialogs.autoplace_dialog import AutoPlaceDialog
from pbe_editor.core.autoplacer import run_auto_placement

class AutoplaceCommandsMixin:
    def on_autoplace(self):
        if not self.w.board.modules:
            QMessageBox.information(self.w, "Информация", "На плате нет модулей для размещения.")
            return
            
        has_edge = any(line.layer == "Edge.Cuts" for line in self.w.board.lines)
        if not has_edge:
            QMessageBox.warning(self.w, "Ошибка", "На плате не нарисован контур (Edge.Cuts). Авторазмещение невозможно.")
            return
            
        dlg = AutoPlaceDialog(self.w)
        if dlg.exec() != AutoPlaceDialog.Accepted:
            return
            
        params = dlg.get_params()
        threads = dlg.get_threads()
        
        try:
            result = run_auto_placement(self.w.board, params, threads)
        except Exception as e:
            QMessageBox.critical(self.w, "Ошибка", str(e))
            return
            
        for i, module in enumerate(self.w.board.modules):
            if i in result.positions:
                module.x, module.y = result.positions[i]
                module.angle = 0.0
                item = self.w.manager.items.get(module.uid)
                if item:
                    item.setPos(module.x, module.y)
                    item.setRotation(0.0)
                    item.prepareGeometryChange()
                    item.update()
                    
        self.w.manager.rebuild_ratsnest()
        self.w.commit_snapshot()
        
        msg = (
            f"Зафиксирован элемент: {result.directive_ref}\n"
            f"Время: {result.time_seconds:.3f} с\n"
            f"Корпусов: {result.num_footprints}\n"
            f"Связей: {result.num_connections}\n"
            f"Длина (Евклид): {result.wire_euclidean:.2f} мм\n"
            f"Длина (Манхэттен): {result.wire_manhattan:.2f} мм"
        )
        QMessageBox.information(self.w, "Размещение завершено", msg)
        self.w.show_log("Авторазмещение выполнено")