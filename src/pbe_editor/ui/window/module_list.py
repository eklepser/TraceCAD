class ModuleListService:
    def refresh_module_list(self):
        self.module_list.clear()
        for module in self.board.modules:
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(f"{module.reference}  [{module.footprint.name}]")
            item.setToolTip(f"{module.reference} = {module.value}")
            self.module_list.addItem(item)