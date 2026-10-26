from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from pbe_editor.core.board_models import Board, BoardModule, PadNet
from pbe_editor.core.netlist_parser import parse_netlist
from kicad.brd_exporter import build_brd_text
from kicad.brd_importer import parse_brd


class BoardFilesService:
    def on_import_net(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть сетлист", "",
                                              "Netlist (*.net);;All Files (*)")
        if not path:
            return
        self.refresh_library_modules()
        try:
            components = parse_netlist(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разобрать сетлист: {e}")
            return

        self.manager.clear()
        self.board = Board(name=Path(path).stem)
        self.manager.board = self.board

        missing = []
        next_uid = 1
        for comp in components:
            fp = self.find_footprint(comp.footprint)
            if fp is None:
                missing.append(f"{comp.reference} ({comp.footprint})")
                continue
            module = BoardModule(
                footprint=fp, reference=comp.reference, value=comp.value,
                x=0.0, y=0.0, angle=0.0, layer="F.Cu", uid=next_uid,
            )
            next_uid += 1
            pad_numbers = {p.number for p in fp.pads}
            for pad_number, net_name in comp.pins.items():
                if pad_number not in pad_numbers or not net_name:
                    continue
                net = self.board.get_or_create_net(net_name)
                module.pad_nets[pad_number] = PadNet(
                    pad_number=pad_number,
                    net_code=net.code,
                    net_name=net.name,
                )
            self.board.modules.append(module)
            self.manager.add_module(module)
        self.refresh_module_list()
        self.manager.rebuild_ratsnest()
        self.show_log(f"Импортировано модулей: {len(self.board.modules)}")
        self._reset_history()
        self._modified = True
        if missing:
            QMessageBox.information(self, "Импорт завершён",
                "Импорт выполнен, но не найдены посадочные места:\n" + "\n".join(missing))

    def on_open_board(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть плату", "",
                                              "KiCad Board (*.brd);;All Files (*)")
        if not path:
            return
        self.load_board_from_path(path)

    def load_board_from_path(self, path):
        try:
            board = parse_brd(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть плату: {e}")
            return
        self.manager.clear()
        self.board = board
        self.manager.board = self.board
        self.board.name = Path(path).stem

        for module in self.board.modules:
            self.manager.add_module(module)
        for line in self.board.lines:
            self.manager.add_line(line)
        for circle in self.board.circles:
            self.manager.add_circle(circle)
        for arc in self.board.arcs:
            self.manager.add_arc(arc)
        for text in self.board.texts:
            self.manager.add_text(text)

        self.refresh_module_list()
        self.manager.rebuild_ratsnest()
        self.board.filename = path
        self.show_log(f"Плата загружена: {Path(path).name} ({len(self.board.modules)} модулей)")
        self._reset_history()
        self._modified = False

    def save_board(self):
        if not self.board.filename:
            self.on_save_board_as()
            return
        try:
            text = build_brd_text(self.board)
            Path(self.board.filename).write_text(text, encoding='utf-8')
            self._modified = False
            self.show_log(f"Плата сохранена: {Path(self.board.filename).name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def on_save_board_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить плату как", "",
                                              "KiCad Board (*.brd);;All Files (*)")
        if not path:
            return
        if not path.lower().endswith('.brd'):
            path += '.brd'
        try:
            text = build_brd_text(self.board)
            Path(path).write_text(text, encoding='utf-8')
            self.board.filename = path
            self.board.name = Path(path).stem
            self._modified = False
            self.show_log(f"Плата сохранена: {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")