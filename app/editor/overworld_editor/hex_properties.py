from PyQt5.QtWidgets import QVBoxLayout, \
    QWidget, QLabel
from PyQt5.QtCore import Qt

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
        print("Hex Properties Menu select_hex", hex_prefab)
        current_overworld = DB.overworlds.get(self.state_manager.state.selected_overworld)
        if current_overworld:
            self.current_hex = hex_prefab
        else:
            self.current_hex = None
        if self.current_hex:
            self.position_label.setText(self.current_hex.get_position_label())
            self.hex_type_box.edit.setValue(self.current_hex.hex_type)
        else:
            self.set_components_active(False)

    def set_components_active(self, is_active):
        is_inactive = not is_active
        self.hex_type_box.setDisabled(is_inactive)

    def hex_type_changed(self):
        if self.current_hex:
            self.current_hex.hex_type = self.hex_type_box.edit.currentText()

    def _initialize_components(self):
        self.setStyleSheet("font: 10pt;")
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)

        self.position_label = QLabel()
        self.position_label.setText("No Hex Selected")
        self.layout.addWidget(self.position_label)

        self.hex_type_box = HexTypeBox(self)
        self.hex_type_box.edit.activated.connect(self.hex_type_changed)
        self.layout.addWidget(self.hex_type_box)
