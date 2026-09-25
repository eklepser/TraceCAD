import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from footprint_editor.ui.main_window import FootprintEditorWindow
from footprint_editor.core.models import Footprint


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = FootprintEditorWindow(footprint=Footprint(name="My_First_Component"))
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()