class Styles:
    DIALOG_BG = ""
    INPUT_BG = ""
    BUTTON_OK = ""
    BUTTON_CANCEL = ""
    BUTTON_DISABLED = ""
    LOG_LABEL = ""
    RIGHT_PANEL = ""
    APPLY_BUTTON = ""
    RESET_BUTTON = ""
    TOOL_BUTTON_ACTIVE = ""
    TOOL_BUTTON_INACTIVE = ""
    LIST_BG = ""
    TOOLTIP = ""
    MAIN_WINDOW = ""
    SECTION_LABEL = ""
    OBJECT_TITLE = ""
    AUX_BAR = ""


DARK_STYLES = {
    "DIALOG_BG": (
        "QDialog { background-color: #2b2b2b; color: #d8d8d8; }"
        "QLabel { color: #d8d8d8; }"
        "QLineEdit, QDoubleSpinBox {"
        "  background-color: #3c3f41; color: #ffffff;"
        "  border: 1px solid #555555; padding: 5px; }"
        "QLineEdit:focus, QDoubleSpinBox:focus { border: 1px solid #365880; }"
        "QCheckBox { color: #d8d8d8; spacing: 6px; }"
    ),
    "INPUT_BG": (
        "background-color: #3c3f41; color: #ffffff;"
        "border: 1px solid #555555; padding: 5px;"
    ),
    "BUTTON_OK": "background-color: #365880; color: white; border: none; padding: 5px 14px;",
    "BUTTON_CANCEL": "background-color: #555555; color: white; border: none; padding: 5px 14px;",
    "BUTTON_DISABLED": "background-color: #3a3a3a; color: #707070; border: none; padding: 5px 14px;",
    "LOG_LABEL": "background-color: rgba(40, 40, 40, 220); color: #a9b7c6; padding: 5px; border-radius: 3px;",
    "RIGHT_PANEL": "background-color: #3c3f41; color: white;",
    "APPLY_BUTTON": "background-color: #365880; color: white; padding: 5px; border: none;",
    "RESET_BUTTON": "background-color: #555555; color: white; padding: 5px; border: none;",
    "TOOL_BUTTON_ACTIVE": (
        "QPushButton { font-size: 18px; border: 2px solid #0096ff;"
        " background-color: #365880; color: white; }"
        " QPushButton:hover { background-color: #2a4a6b; }"
    ),
    "TOOL_BUTTON_INACTIVE": (
        "QPushButton { font-size: 18px; border: 2px solid transparent;"
        " background-color: #3c3f41; color: white; }"
        " QPushButton:hover { background-color: #2a4a6b; }"
    ),
    "LIST_BG": (
        "QListWidget { background-color: #2b2b2b; color: #a9b7c6;"
        " border: 1px solid #555555; }"
        " QListWidget::item { padding: 3px 6px; }"
        " QListWidget::item:selected { background-color: #365880; color: white; }"
        " QListWidget::item:hover { background-color: #3c3f41; }"
    ),
    "TOOLTIP": "QToolTip { font-size: 10px; background-color: #2b2b2b; color: #a9b7c6; border: 1px solid #555555; padding: 2px; }",
    "MAIN_WINDOW": (
        "QMainWindow { background-color: #3c3f41; }"
        "QDockWidget { background-color: #3c3f41; color: #a9b7c6; }"
        "QMenuBar { background-color: #2b2b2b; color: #a9b7c6; }"
        "QMenuBar::item { padding: 6px 10px; background: transparent; }"
        "QMenuBar::item:selected { background-color: #365880; }"
        "QMenu { background-color: #2b2b2b; color: #a9b7c6; }"
        "QMenu::item { padding: 4px 20px; }"
        "QMenu::item:selected { background-color: #365880; }"
        "QStatusBar { background-color: #2b2b2b; color: #a9b7c6; }"
        "QToolBar { background-color: #2b2b2b; color: #a9b7c6; padding: 0px; spacing: 4px; }"
        "QGroupBox { color: #a9b7c6; border: 1px solid #555555; margin-top: 8px; padding-top: 6px; }"
        "QGroupBox::title { subcontrol-origin: margin; left: 8px; }"
        "QLabel { color: #a9b7c6; }"
        "QComboBox { background-color: #3c3f41; color: white;"
        " border: 1px solid #555555; padding: 3px 8px; min-height: 20px; }"
        "QComboBox::drop-down { border: none; width: 18px; }"
        "QComboBox QAbstractItemView { background-color: #2b2b2b;"
        " color: #a9b7c6; selection-background-color: #365880; }"
    ),
    "SECTION_LABEL": "color: #a9b7c6; font-weight: bold; padding: 2px 0px;",
    "OBJECT_TITLE": "color: #7a9cc6; font-weight: bold; font-size: 10pt; padding: 2px 0px;",
    "AUX_BAR": (
        "QWidget#AuxBar { background-color: #2b2b2b;"
        " border-top: 1px solid #1e1e1e; }"
    ),
}