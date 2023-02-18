from typing import Any, Dict

from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QWidget

from app.data.database.components import ComponentType


class BoolSubcomponentEditor(QWidget):
    def __init__(self, editor_name: str, option_dict: Dict[str, Any]) -> None:
        super().__init__()
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hbox)
        self.editor_name = editor_name
        self.option_dict = option_dict

        name_label = QLabel(editor_name)
        hbox.addWidget(name_label)

        self.create_editor(hbox)

    def create_editor(self, hbox):
        editor = QCheckBox(self)
        editor.setChecked(self.option_dict[self.editor_name])
        editor.stateChanged.connect(self.on_value_changed)
        hbox.addWidget(editor)

    def on_value_changed(self, val):
        self.option_dict[self.editor_name] = bool(val)

def get_editor_widget(editor_name: str, ctype: ComponentType, option_dict: Dict[str, Any]):
    if ctype == ComponentType.Bool:
        return BoolSubcomponentEditor(editor_name, option_dict)
