from PyQt5.QtWidgets import QVBoxLayout, \
    QWidget, QLabel, QLineEdit
from PyQt5.QtCore import Qt

from app.extensions.custom_gui import PropertyBox, ComboBox

from app.data.database import DB
from app.editor.custom_widgets import HexTypeBox

class HexPropertiesMenu(QWidget):
    def __init__(self, state_manager):
        super().__init__()
        self.state_manager = state_manager

        self._initialize_components()

        # widget state
        self.current_hex = None
        self.select_hex(self.state_manager.state.selected_node)

        # subscriptions
        self.state_manager.subscribe_to_key(HexPropertiesMenu.__name__, 'selected_node', self.select_hex)

    def select_hex(self, hex_prefab):
        current_overworld = DB.overworlds.get(self.state_manager.state.selected_overworld)
        if current_overworld:
            self.current_hex = hex_prefab
        else:
            self.current_hex = None
        if self.current_hex:
            # Reset Hex Types
            self.hex_type_box.edit.clear()
            for hex_type in DB.hex_types:
                self.hex_type_box.edit.addItem(hex_type.nid)            

            self.position_label.setText(self.current_hex.get_position_label())
            if self.current_hex.hex_type:
                self.hex_type_box.edit.setValue(self.current_hex.hex_type)
            elif DB.hex_types:
                self.hex_type_box.edit.setValue(DB.hex_types.keys()[0])
            if self.current_hex.name:
                self.name_box.edit.setText(self.current_hex.name)
            else:
                self.name_box.edit.setText('')
            self.set_components_active(True)
        else:
            self.position_label.setText("No Hex Selected")
            self.set_components_active(False)

    def set_components_active(self, is_active):
        is_inactive = not is_active
        self.hex_type_box.setDisabled(is_inactive)
        self.name_box.setDisabled(is_inactive)

    def hex_type_changed(self):
        if self.current_hex:
            print("Hex Type Changed!", self.current_hex, self.hex_type_box.edit.currentText())
            self.current_hex.hex_type = self.hex_type_box.edit.currentText()

    def name_changed(self, text):
        if self.current_hex:
            self.current_hex.name = text
            self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def _initialize_components(self):
        self.setStyleSheet("font: 10pt;")
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)

        self.position_label = QLabel()
        self.position_label.setText("No Hex Selected")
        self.layout.addWidget(self.position_label)

        self.name_box = PropertyBox("Unique Name", QLineEdit, self)
        self.name_box.edit.textChanged.connect(self.name_changed)
        self.layout.addWidget(self.name_box)

        self.hex_type_box = PropertyBox("Hex Type", ComboBox, self)
        for hex_type in DB.hex_types:
            self.hex_type_box.edit.addItem(hex_type.nid)
        self.hex_type_box.edit.activated.connect(self.hex_type_changed)
        self.layout.addWidget(self.hex_type_box)
