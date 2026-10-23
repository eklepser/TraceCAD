import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from pbe_editor.ui.board_window import BoardEditorWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = BoardEditorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()