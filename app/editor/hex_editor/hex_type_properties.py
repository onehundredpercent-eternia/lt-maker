from PyQt5.QtWidgets import QWidget, QSpacerItem, \
    QLineEdit, QHBoxLayout, QVBoxLayout, \
    QMessageBox, QSizePolicy, QDoubleSpinBox
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

from app.data.database import DB

from app.extensions.custom_gui import PropertyBox
from app.extensions.color_icon import ColorIcon
from app.extensions.list_widgets import AppendMultiListWidget
from app.extensions.list_models import DoubleListModel
from app.utilities import str_utils

class HexTypeProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = ColorIcon(QColor(0, 0, 0), self)
        self.icon_edit.colorChanged.connect(self.on_color_change)
        top_section.addWidget(self.icon_edit)

        horiz_spacer = QSpacerItem(40, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_section.addSpacerItem(horiz_spacer)

        name_section = QVBoxLayout()

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        name_section.addWidget(self.nid_box)

        self.name_box = PropertyBox("Display Name", QLineEdit, self)

        self.name_box.edit.textChanged.connect(self.name_changed)
        name_section.addWidget(self.name_box)

        top_section.addLayout(name_section)

        main_section = QVBoxLayout()

        movement_section = QHBoxLayout()
        self.movement_box = PropertyBox("Movement Cost", QDoubleSpinBox, self)
        self.movement_box.edit.setRange(0, 100)
        self.movement_box.edit.setSingleStep(0.25)
        self.movement_box.edit.setAlignment(Qt.AlignRight)
        self.movement_box.edit.valueChanged.connect(self.movement_changed)
        movement_section.addWidget(self.movement_box)

        main_section.addLayout(movement_section)

        attrs = ("event_nid", "event_chance")
        self.hex_event_widget = AppendMultiListWidget([], "Hex Events", attrs, HexEventDelegate, self, model=DoubleListModel)
        main_section.addLayout(self.hex_event_widget)

        total_section = QVBoxLayout()
        self.setLayout(total_section)
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        total_section.setAlignment(Qt.AlignTop)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [hex_type.nid for hex_type in DB.hex_types.values() if hex_type is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Hex Type ID %s already in use' % self.current.nid)
            self.current.nid = str_utils.get_next_int(self.current.nid, other_nids)
        DB.hex_type.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def movement_changed(self, index):
        self.current.movement_cost = self.movement_box.edit.value()

    def on_color_change(self, color):
        self.current.color = tuple(color.getRgb()[:3])
        self.window.update_list()

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.name_box.edit.setText(current.name)
        self.movement_box.edit.setValue(current.movement_cost)

        self.hex_event_widget.set_current(current.events)

        # Icon
        color = current.color
        self.icon_edit.change_color(QColor(color[0], color[1], color[2]))
