from typing import Any, Dict

from PyQt5.QtWidgets import (QCheckBox, QDoubleSpinBox, QHBoxLayout,
                             QLabel, QLineEdit, QSpinBox, QWidget)
from app.utilities import utils
from app.extensions.custom_gui import ComboBox
from app.data.database.components import ComponentType
from app.data.database.database import DB
from app.data.resources.resources import RESOURCES

from app.editor.editor_constants import MIN_DROP_DOWN_WIDTH, MAX_DROP_DOWN_WIDTH, DROP_DOWN_BUFFER

import logging

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

class SkillSubcomponentEditor(BoolSubcomponentEditor):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        for skill in DB.skills.values():
            self.editor.addItem(skill.nid)
        width = utils.clamp(self.editor.minimumSizeHint().width() + DROP_DOWN_BUFFER, MIN_DROP_DOWN_WIDTH, MAX_DROP_DOWN_WIDTH)
        self.editor.setMaximumWidth(width)
        if not self.option_dict.get(self.editor_name):
            self.option_dict[self.editor_name] = DB.skills[0].nid
        self.editor.setValue(self.option_dict[self.editor_name])
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self.option_dict[self.editor_name] = val

class IntSubcomponentEditor(BoolSubcomponentEditor):
    def create_editor(self, hbox):
        self.editor = QSpinBox(self)
        self.set_format()
        if self.option_dict.get(self.editor_name) is None:
            self.option_dict[self.editor_name] = 0
        self.editor.setValue(self.option_dict[self.editor_name])
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self.option_dict[self.editor_name] = int(val)

    def set_format(self):
        self.editor.setMaximumWidth(60)
        self.editor.setRange(-1000, 10000)

class StringSubcomponentEditor(BoolSubcomponentEditor):
    def create_editor(self, hbox):
        self.editor = QLineEdit(self)
        self.editor.setMaximumWidth(640)
        if not self.option_dict.get(self.editor_name):
            self.option_dict[self.editor_name] = ''
        self.editor.setText(str(self.option_dict[self.editor_name]))
        self.editor.textChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self.option_dict[self.editor_name] = str(val)

class FloatSubcomponentEditor(BoolSubcomponentEditor):
    def create_editor(self, hbox):
        self.editor = QDoubleSpinBox(self)
        self.editor.setMaximumWidth(60)
        self.editor.setRange(-99, 99)
        self.editor.setSingleStep(.1)
        if self.option_dict.get(self.editor_name) is None:
            self.option_dict[self.editor_name] = 0
        self.editor.setValue(self.option_dict[self.editor_name])
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self.option_dict[self.editor_name] = float(val)

class EventSubcomponentEditor(BoolSubcomponentEditor):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        # Only use global events
        valid_events = [event for event in DB.events.values() if not event.level_nid]
        for event in valid_events:
            self.editor.addItem(event.nid)
        width = utils.clamp(self.editor.minimumSizeHint().width() + DROP_DOWN_BUFFER, MIN_DROP_DOWN_WIDTH, MAX_DROP_DOWN_WIDTH)
        self.editor.setMaximumWidth(width)
        if not self.option_dict.get(self.editor_name) and valid_events:
            self.option_dict[self.editor_name] = valid_events[0].nid
        self.editor.setValue(self.option_dict[self.editor_name])
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self.option_dict[self.editor_name] = val

class ItemSubcomponentEditor(BoolSubcomponentEditor):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        for item in DB.items.values():
            self.editor.addItem(item.nid)
        width = utils.clamp(self.editor.minimumSizeHint().width() + DROP_DOWN_BUFFER, MIN_DROP_DOWN_WIDTH, MAX_DROP_DOWN_WIDTH)
        self.editor.setMaximumWidth(width)
        if not self.option_dict.get(self.editor_name):
            self.option_dict[self.editor_name] = DB.items[0].nid
        self.editor.setValue(self.option_dict[self.editor_name])
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self.option_dict[self.editor_name] = val

class SoundSubcomponentEditor(BoolSubcomponentEditor):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        for sound in RESOURCES.sfx.values():
            self.editor.addItem(sound.nid)
        width = utils.clamp(self.editor.minimumSizeHint().width() + DROP_DOWN_BUFFER, MIN_DROP_DOWN_WIDTH, MAX_DROP_DOWN_WIDTH)
        self.editor.setMaximumWidth(width)
        if not self.option_dict.get(self.editor_name):
            self.option_dict[self.editor_name] = RESOURCES.sfx[0].nid
        self.editor.setValue(self.option_dict[self.editor_name])
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self.option_dict[self.editor_name] = val

def get_editor_widget(editor_name: str, ctype: ComponentType, option_dict: Dict[str, Any]):
    if ctype == ComponentType.Bool:
        return BoolSubcomponentEditor(editor_name, option_dict)
    elif ctype == ComponentType.Skill:
        return SkillSubcomponentEditor(editor_name, option_dict)
    elif ctype == ComponentType.Int:
        return IntSubcomponentEditor(editor_name, option_dict)
    elif ctype == ComponentType.String:
        return StringSubcomponentEditor(editor_name, option_dict)
    elif ctype == ComponentType.Float:
        return FloatSubcomponentEditor(editor_name, option_dict)
    elif ctype == ComponentType.Item:
        return ItemSubcomponentEditor(editor_name, option_dict)
    elif ctype == ComponentType.Event:
        return EventSubcomponentEditor(editor_name, option_dict)
    elif ctype == ComponentType.Sound:
        return SoundSubcomponentEditor(editor_name, option_dict)
    else:
        logging.error("No valid ctype %s available for subcomponent. Defaulting to bool")
        return BoolSubcomponentEditor(editor_name, option_dict)
