CHECKBOX_QSS = (
    "QCheckBox { color: #a9b7c6; spacing: 8px; background: transparent; }"
    "QCheckBox::indicator { width: 14px; height: 14px;"
    " border: 1px solid #d8d8d8; background-color: #2b2b2b;"
    " border-radius: 2px; }"
    "QCheckBox::indicator:hover { border: 1px solid #ffffff; }"
    "QCheckBox::indicator:checked {"
    " border: 1px solid #ffffff; background-color: #365880; }"
)


COMBO_VIEW_QSS = (
    "QListView { background-color: #2b2b2b; color: #a9b7c6;"
    " border: 1px solid #555555; outline: 0; }"
    "QListView::item { padding: 4px 8px; }"
    "QListView::item:selected {"
    "  background-color: #365880; color: white; }"
)


TABLE_QSS = (
    "QTableWidget { background-color: #1e1e1e; color: #cfcfcf;"
    " gridline-color: #3c3f41; border: 1px solid #3c3f41; }"
    "QHeaderView::section { background-color: #2b2b2b; color: #a9b7c6;"
    " border: 0px; border-right: 1px solid #3c3f41; padding: 4px; }"
)


ADD_BUTTON_STYLE = (
    "QPushButton { background-color: #365880; color: white;"
    " font-size: 14px; font-weight: bold;"
    " border: none; padding: 0px; }"
    " QPushButton:hover { background-color: #2a4a6b; }"
)


def form_widget_qss():
    return (
        "QWidget#PropertiesTable { background-color: #2b2b2b;"
        " border: 1px solid #555555; }"
        " QWidget#PropertiesTable QLabel { background: transparent; color: #a9b7c6; }"
        " QWidget#PropertiesTable QLineEdit {"
        "   background: transparent; color: #ffffff;"
        "   border: 1px solid transparent;"
        "   border-bottom: 1px solid #555555;"
        "   padding: 2px 6px;"
        " }"
        " QWidget#PropertiesTable QLineEdit:focus {"
        "   border-bottom: 1px solid #365880;"
        " }"
        " QWidget#PropertiesTable QComboBox {"
        "   background: transparent; color: #ffffff;"
        "   border: 1px solid transparent;"
        "   border-bottom: 1px solid #555555;"
        "   padding: 2px 6px;"
        " }"
        " QWidget#PropertiesTable QComboBox::drop-down {"
        "   border: none; width: 14px; }"
    )


def inline_combo_qss():
    return (
        "QComboBox { background: transparent; color: #ffffff;"
        " border: 1px solid transparent; border-bottom: 1px solid #555555;"
        " padding: 2px 6px; }"
        " QComboBox:focus { border-bottom: 1px solid #365880; }"
        " QComboBox::drop-down { border: none; width: 14px; }"
    )