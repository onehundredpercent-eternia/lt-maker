from typing import Any, Dict, Optional, Tuple

from PyQt5.QtWidgets import QDoubleSpinBox, \
    QDialog, QGroupBox, QFormLayout, QSpinBox, \
    QCheckBox

from app.utilities.typing import NID

from app.extensions.custom_gui import ComboBox, Dialog
from app.editor.settings import MainSettingsController

from app.map_maker.terrain import Terrain

from app.dungeon_maker import themes

class AutogenerateIndoorMapDialog(Dialog):
    def __init__(self, current: Dict[NID, Any], parent=None):
        super().__init__(parent)
        self.window = parent
        self.setWindowTitle("Autogenerate Indoor Map")

        self.settings = MainSettingsController()

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.current: Dict[NID, Any] = current  # Set of custom theme parameters

        self.previous_theme = self.settings.component_controller.get_state(self.__class__.__name__)

        self.theme_preset_combobox = ComboBox(self)
        self.theme_presets = themes.theme_presets.keys()
        self.theme_preset_combobox.addItems(self.theme_presets)
        self.theme_preset_combobox.currentIndexChanged.connect(self.theme_preset_changed)

        boxes = {}
        for theme_parameter in themes.theme_parameters:
            if theme_parameter._type == Tuple[int, int]:
                editor, x_widget, y_widget = self._create_2d_editor(theme_parameter.name, theme_parameter.value)
                boxes[theme_parameter.nid] = (x_widget, y_widget)
            elif theme_parameter._type == float:
                editor = QDoubleSpinBox(self)
                editor.setMaximumWidth(60)
                editor.setRange(-999, 999)
                editor.setValue(theme_parameter.value)
                boxes[theme_parameter.nid] = editor
            elif theme_parameter._type == int:
                editor = QSpinBox(self)
                editor.setMaximumWidth(60)
                editor.setRange(-999, 999)
                editor.setValue(theme_parameter.value)
                boxes[theme_parameter.nid] = editor
            elif theme_parameter._type == bool:
                editor = QCheckBox(self)
                editor.setChecked(bool(theme_parameter.value))
                boxes[theme_parameter.nid] = editor
            elif theme_parameter._type == Terrain:
                editor = ComboBox(self)
                editor.addItems(Terrain.get_all_floor())
                boxes[theme_parameter.nid] = editor

            editor.setToolTip(theme_parameter.desc)
            self.layout.addRow(theme_parameter.name, editor)

        if self.previous_theme:
            self.theme_presets.append("Previous")
            self.theme_preset_combobox.addItem("Previous")
            self.theme_preset_combobox.setValue("Previous")

    def _create_2d_editor(self, title: str, value: Tuple[int, int]):
        size_section = QGroupBox(self)
        size_section.setTitle(title)
        size_layout = QFormLayout()
        self.x_box = QSpinBox()
        self.x_box.setValue(value[0])
        self.x_box.setRange(15, 255)
        size_layout.addRow("X:", self.x_box)
        self.y_box = QSpinBox()
        self.y_box.setValue(value[1])
        self.y_box.setRange(10, 255)
        size_layout.addRow("Y:", self.y_box)
        size_section.setLayout(size_layout)
        return (size_section, self.width_box, self.height_box)

    def theme_preset_changed(self, idx: int):
        """
        Called when the user selects a new theme preset
        Overwrites the current value of every selection made so far
        """
        chosen_preset_nid = self.theme_presets[idx]
        if chosen_preset_nid == "Previous":
            chosen_preset = self.previous_theme
        else:
            chosen_preset = themes.get_theme(chosen_preset_nid)
            
        for nid, value in chosen_preset.items():
            editor = self.boxes[nid]
            if isinstance(editor, QCheckBox):
                editor.setChecked(bool(value))
            else:
                editor.setValue(value)

    def get_parameters(self) -> Dict[NID, Any]:
        """
        Get the current set of parameters the user has chosen
        using this dialog
        """
        theme_parameters = {}
        for nid, editor in self.boxes:
            if isinstance(editor, QCheckBox):
                value = bool(editor.getChecked())
            else:
                value = editor.getValue()
            theme_parameters[nid] = value
        return theme_parameters

    @classmethod
    def get_theme(cls, parent=None) -> Optional[Dict[NID, Any]]:
        default_theme_parameters = themes.get_default_theme()
        dialog = cls(default_theme_parameters, parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            current_theme = dialog.get_parameters()
            dialog.settings.component_controller.set_state(cls.__name__, current_theme)
            return current_theme
        else:
            return None
