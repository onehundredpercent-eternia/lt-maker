from app.utilities import str_utils
from app.data.database import DB
from typing import Dict

from app.data.ui_prefab import UIObjectPrefab
from app.editor.lib.state_editor.editor_state_manager import EditorStateManager
from app.editor.sprite_select_dialog import get_sprite
from app.extensions.custom_gui import PropertyBox, PropertyCheckBox, QHLine
from app.extensions.frame_layout import FrameLayout
from app.extensions.key_value_delegate import (KeyValueDelegate,
                                               KeyValueDictModel)
from app.extensions.list_widgets import AppendMultiListWidget
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QGridLayout, QGroupBox, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QSpinBox, QVBoxLayout,
                             QWidget)


class UIElementProperties(QWidget):
    def __init__(self, parent=None, state_manager: EditorStateManager = None):
        super().__init__(parent)
        self.ui_editor = parent
        self.state_manager=state_manager

        form = QVBoxLayout(self)
        form.setAlignment(Qt.AlignTop)

        self.current_subcomponent: UIObjectPrefab = None

        self.nid_box = PropertyBox("Component Type", QLabel, self)
        form.addWidget(self.nid_box)

        size_section = QGroupBox(self)
        size_section.setTitle("Size")
        size_layout = QGridLayout()
        self.width_box = QSpinBox()
        self.width_box.setRange(1, 1000)
        self.width_box.valueChanged.connect(self.on_width_changed)
        self.height_box = QSpinBox()
        self.height_box.setRange(1, 1000)
        self.height_box.valueChanged.connect(self.on_height_changed)
        size_layout.addWidget(QLabel("Width:"), 0, 0)
        size_layout.addWidget(self.width_box, 0, 1)
        size_layout.addWidget(QLabel("Height:"), 0, 2)
        size_layout.addWidget(self.height_box, 0, 3)
        self.can_be_invalid_box = PropertyCheckBox('Can be invalid?', QCheckBox, self)
        self.can_be_invalid_box.edit.stateChanged.connect(self.can_be_invalid_checked)
        size_layout.addWidget(self.can_be_invalid_box, 0, 4)
        size_section.setLayout(size_layout)
        form.addWidget(size_section)

        form.addWidget(QHLine())

        self.args_section = QGroupBox(self)
        self.args_section.setTitle("Component Parameters")
        self.component_parameters: Dict[str, PropertyBox] = {}
        self.args_layout = QGridLayout()
        self.args_section.setLayout(self.args_layout)
        form.addWidget(self.args_section)
        form.addWidget(QHLine())

        self.set_selected(self.current_subcomponent)

    def can_be_invalid_checked(self):
        self.current_subcomponent.can_be_invalid = self.can_be_invalid_box.edit.isChecked()

    def set_selected(self, ui_prefab: UIObjectPrefab):
        self.current_subcomponent = ui_prefab
        any_selection = False
        if self.current_subcomponent:
            any_selection = True
            self.nid_box.edit.setText(self.current_subcomponent.nid)
            x, y = self.current_subcomponent.size
            self.width_box.setValue(x)
            self.height_box.setValue(y)
            self.can_be_invalid_box.edit.setChecked(self.current_subcomponent.can_be_invalid)
        disable = not any_selection
        self.nid_box.edit.setDisabled(disable)
        self.width_box.setDisabled(disable)
        self.height_box.setDisabled(disable)
        self.can_be_invalid_box.edit.setDisabled(disable)
        self.populate_args(self.current_subcomponent)

    def on_width_changed(self, width: int):
        new_size = width, self.current_subcomponent.size[1]
        self.current_subcomponent.size = new_size
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def on_height_changed(self, height: int):
        new_size = self.current_subcomponent.size[0], height
        self.current_subcomponent.size = new_size
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def edit_arg(self, argtype: str):
        if self.current_subcomponent:
            component_editor = self.component_parameters.get(argtype)
            if component_editor:
                value = component_editor.edit.text()
                self.current_subcomponent.arguments[argtype] = value
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def populate_args(self, component: UIObjectPrefab):
        # remove all existing widgets
        self.component_parameters = {}
        for i in reversed(range(self.args_layout.count())):
            self.args_layout.itemAt(i).widget().setParent(None)
        if component:
            x = 0
            y = 0
            for argtype, argvalue in component.arguments.items():
                arg_box = PropertyBox(argtype, QLineEdit, self, True)
                arg_box.edit.setText(str(argvalue))
                arg_box.edit.editingFinished.connect(lambda arg=argtype: self.edit_arg(arg))
                self.args_layout.addWidget(arg_box, x, y)
                self.component_parameters[argtype] = arg_box
                if y == 2:
                    y = 0
                    x += 1
                else:
                    y += 1

class UIContainerProperties(QWidget):
    def __init__(self, parent=None, state_manager: EditorStateManager = None):
        super().__init__(parent)
        self.ui_editor = parent
        self.state_manager=state_manager

        form = QVBoxLayout(self)
        form.setAlignment(Qt.AlignBottom)

        self.current_container: UIObjectPrefab = None

        self.nid_box = PropertyBox("Main Container", QLineEdit, self)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        form.addWidget(self.nid_box)

        size_section = QGroupBox(self)
        size_layout = QGridLayout()
        self.width_box = QSpinBox()
        self.width_box.setRange(1, 1000)
        self.width_box.valueChanged.connect(self.on_width_changed)
        self.height_box = QSpinBox()
        self.height_box.setRange(1, 1000)
        self.height_box.valueChanged.connect(self.on_height_changed)
        size_layout.addWidget(QLabel("Width:"), 0, 0)
        size_layout.addWidget(self.width_box, 0, 1)
        size_layout.addWidget(QLabel("Height:"), 0, 2)
        size_layout.addWidget(self.height_box, 0, 3)
        self.background_select = QPushButton('UI Background Image')
        self.background_select.clicked.connect(self.set_bg)
        size_layout.addWidget(self.background_select, 0, 4, 1, 2)
        self.can_be_invalid_box = PropertyCheckBox('Can be invalid?', QCheckBox, self)
        self.can_be_invalid_box.edit.stateChanged.connect(self.can_be_invalid_checked)
        size_layout.addWidget(self.can_be_invalid_box, 1, 0, 1, 2)
        self.log_errors_box = PropertyCheckBox('Log errors?', QCheckBox, self)
        self.log_errors_box.edit.stateChanged.connect(self.log_errors_checked)
        size_layout.addWidget(self.log_errors_box, 1, 2, 1, 2)
        size_section.setLayout(size_layout)
        form.addWidget(size_section)

        self.argvalue_box = AppendMultiListWidget([], "Component Args", ("Arg Name", "Testing Value"), KeyValueDelegate, self, model=KeyValueDictModel)
        self.argvalue_box.model.dataChanged.connect(lambda x, y: self.state_manager.change_and_broadcast('ui_refresh_signal', None))
        self.argvalue_box.model.layoutChanged.connect(lambda: self.state_manager.change_and_broadcast('ui_refresh_signal', None))
        self.argvalue_box.setMaximumHeight(200)
        form.addWidget(self.argvalue_box)

        editor_tools_frame = FrameLayout(None, "Editor Settings")
        editor_tools_section = QGroupBox()
        editor_tools_layout = QGridLayout()

        editor_tools_layout.addWidget(
            QLabel("""Various tools to help align and position UI elements.\nThe canvas, offset, and outlines will not appear in the game."""), 0, 0, 1, 6)
        self.x_offset_box = QSpinBox()
        self.x_offset_box.setRange(-1000, 1000)
        self.x_offset_box.valueChanged.connect(self.on_x_offset_changed)
        self.y_offset_box = QSpinBox()
        self.y_offset_box.setRange(-1000, 1000)
        self.y_offset_box.valueChanged.connect(self.on_y_offset_changed)
        editor_tools_layout.addWidget(QLabel("Canvas X:"), 1, 0, 1, 1)
        editor_tools_layout.addWidget(self.x_offset_box, 1, 1, 1, 1)
        editor_tools_layout.addWidget(QLabel("Canvas Y:"), 1, 2, 1, 1)
        editor_tools_layout.addWidget(self.y_offset_box, 1, 3, 1, 1)

        self.canvas_select = QPushButton('Canvas Background')
        self.canvas_select.clicked.connect(self.set_canvas)
        editor_tools_layout.addWidget(self.canvas_select, 1, 4, 1, 2)

        self.enable_outlines_checkbox = QCheckBox("Show component outlines?", None)
        self.enable_outlines_checkbox.setChecked(True)
        self.enable_outlines_checkbox.clicked.connect(self.toggle_outlines)
        editor_tools_layout.addWidget(self.enable_outlines_checkbox, 2, 0, 1, 3)

        editor_tools_section.setLayout(editor_tools_layout)
        editor_tools_frame.addWidget(editor_tools_section)

        form.addWidget(editor_tools_frame)
        self.set_selected(self.current_container)

    def nid_done_editing(self):
        new_nid = self.nid_box.edit.text()
        all_nids = [ui.nid for ui in DB.custom_ui.values() if ui is not self.current_container]
        if new_nid in all_nids:
            QMessageBox.warning(self.ui_editor, 'Warning', 'NID %s already in use' % (new_nid))
            new_nid = str_utils.get_next_name(new_nid, all_nids)
            self.nid_box.edit.setText(new_nid)
        DB.custom_ui.update_nid(self.current_container, new_nid, True)
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def can_be_invalid_checked(self):
        self.current_container.can_be_invalid = self.can_be_invalid_box.edit.isChecked()

    def log_errors_checked(self):
        self.current_container.log_errors = self.log_errors_box.edit.isChecked()

    def set_bg(self):
        sprite_nid, ok = get_sprite()
        if ok:
            self.current_container.bg_sprite = sprite_nid
            self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def set_canvas(self):
        sprite_nid, ok = get_sprite()
        if ok:
            self.current_container.canvas = sprite_nid
            self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def toggle_outlines(self):
        self.ui_editor.view.show_outlines = self.enable_outlines_checkbox.isChecked()
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def set_selected(self, ui_prefab: UIObjectPrefab):
        self.current_container = ui_prefab
        any_selection = False
        if self.current_container:
            any_selection = True
            self.nid_box.edit.setText(self.current_container.nid)
            x, y = self.current_container.size
            self.width_box.setValue(x)
            self.height_box.setValue(y)
            self.argvalue_box.set_current([])
            self.argvalue_box.set_current(self.current_container.arguments)
            self.can_be_invalid_box.edit.setChecked(self.current_container.can_be_invalid)
            self.log_errors_box.edit.setChecked(self.current_container.log_errors)
        disable = not any_selection
        self.width_box.setDisabled(disable)
        self.height_box.setDisabled(disable)
        self.can_be_invalid_box.edit.setDisabled(disable)
        self.log_errors_box.edit.setDisabled(disable)
        self.argvalue_box.setDisabled(disable)
        self.x_offset_box.setDisabled(disable)
        self.y_offset_box.setDisabled(disable)
        self.enable_outlines_checkbox.setDisabled(disable)
        self.canvas_select.setDisabled(disable)
        self.background_select.setDisabled(disable)

        # special handling for nid box
        if disable or self.current_container.locked or self.current_container.generic:
            self.nid_box.edit.setDisabled(True)
        else:
            self.nid_box.edit.setDisabled(False)

    def on_width_changed(self, width: int):
        new_size = width, self.current_container.size[1]
        self.current_container.size = new_size
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def on_height_changed(self, height: int):
        new_size = self.current_container.size[0], height
        self.current_container.size = new_size
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def on_x_offset_changed(self, x: int):
        self.current_container.canvas_offset[0] = x
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def on_y_offset_changed(self, y: int):
        self.current_container.canvas_offset[1] = y
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)
