import enum
from typing import Dict
from PyQt5.QtWidgets import QStyle, QVBoxLayout
from PyQt5.QtCore import Qt

from app.utilities import str_utils
from app.utilities.data import Data
from app.data.database import DB

from app.extensions.custom_gui import DeletionDialog, PropertyBox, ComboBox, SimpleDialog
from app.extensions.list_dialogs import MultiAttrListDialog
from app.extensions.list_models import MultiAttrListModel

from app.data import equations, level_units, item_components, components

from app.engine.objects.unit import UnitObject

import logging

class EvalType(enum.Enum):
    UNIT = "UnitObject"
    ITEM = "ItemObject"
    SKILL = "SkillObject"

class ConditionDialog(SimpleDialog):
    def __init__(self, params: Dict[str, EvalType]):
        super().__init__()
        self.setWindowTitle("New Condition")
        self.params = params

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.boxes = {}
        for idx, key in enumerate(self.current.music.keys()):
            title = key.replace('_', ' ').title()
            box = PropertyBox(title, QLineEdit, self)
            box.edit.setReadOnly(True)
            box.add_button(QPushButton('...'))
            box.button.setMaximumWidth(40)
            box.button.clicked.connect(
                partial(self.access_music_resources, key))
            box.delete_button = QPushButton('X')
            box.bottom_section.addWidget(box.delete_button)
            box.delete_button.setMaximumWidth(30)
            box.delete_button.clicked.connect(
                partial(self.delete_music_resource, key))

            layout.addWidget(box)
            self.boxes[key] = box

        self.set_current(self.current)
        self.setMinimumWidth(300)

    def set_current(self, current):
        self.current = current
        for key, value in self.current.music.items():
            if value:
                self.boxes[key].edit.setText(value)

    def access_music_resources(self, key):
        res, ok = sound_tab.get_music()
        if ok and res:
            nid = res[0].nid
            self.current.music[key] = nid
            self.boxes[key].edit.setText(nid)

    def delete_music_resource(self, key):
        self.current.music[key] = None
        self.boxes[key].edit.setText('')

# Testing
# Run "python -m app.editor.condition_widget"
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    DB.load('default.ltproj')
    from typing import get_type_hints
    # print(get_type_hints(UnitObject))
    # print(get_type_hints(get_type_hints(UnitObject)['skills'].__args__[0]))
    import typing
    # attrs = [f for f in dir(UnitObject) if '_' is not f[0]]
    # for f in attrs:
    #     try:
    #         print(f, get_type_hints(getattr(UnitObject, f)))
    #     except:
    #         pass
    # window = ConditionDialog.create()
    # window.show()
    # app.exec_()
