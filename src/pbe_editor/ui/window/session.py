from pathlib import Path

from PySide6.QtCore import QSettings

from constants import SETTINGS_ORG, SETTINGS_APP
from constants.board_settings import SETTINGS_KEY_BRD_LAST
from common.ui.dialogs.custom_question_dialog import CustomQuestionDialog


class SessionService:
    def _init_session(self):
        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)

    def save_last_board(self):
        if self.board.filename:
            self._settings.setValue(SETTINGS_KEY_BRD_LAST, self.board.filename)
        else:
            self._settings.setValue(SETTINGS_KEY_BRD_LAST, "")
        self._settings.sync()

    def _restore_last_board(self):
        last = self._settings.value(SETTINGS_KEY_BRD_LAST, "", type=str)
        if not last:
            self._reset_history()
            return
        p = Path(last)
        if not p.exists() or not p.is_file():
            self._reset_history()
            return
        self.load_board_from_path(str(p))

    def closeEvent(self, event):
        if self._modified:
            dlg = CustomQuestionDialog(
                self,
                title="Несохранённые изменения",
                message=f"Сохранить изменения в плате '{self.board.name}' перед выходом?"
            )
            result = dlg.exec()
            if result == CustomQuestionDialog.ResultSave:
                self.save_board()
                if self._modified:
                    event.ignore()
                    return
            elif result == CustomQuestionDialog.ResultCancel:
                event.ignore()
                return
        self.save_last_board()
        super().closeEvent(event)