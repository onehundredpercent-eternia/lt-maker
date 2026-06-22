from PyQt5.QtWidgets import \
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox, QSpinBox, \
    QListWidget, QListWidgetItem, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor, QPixmap, QPainter

from app.data.database.database import DB

from app.utilities import utils, str_utils

from app.extensions.custom_gui import PropertyBox, ComboBox
from app.editor.custom_widgets import TeamBox
from app.editor.icons import ItemIcon32
from app.editor.lib.components.validated_line_edit import NidLineEdit
from app.editor.level_editor.painter_menu import PainterMenu, PainterModel
from app.editor.building_editor.building_model import get_pixmap
from app.data import cities


class CityMenu(PainterMenu):
    def __init__(self, state_manager, map_view):
        super().__init__(state_manager, map_view, noun='City', data_attr='cities',
                         model_cls=CityModel, modify_widget_cls=ModifyCityWidget,
                         prefab_cls=cities.City)

    def get_current_building(self):
        """Return (city, building_index) when a building row is selected in the
        building list, else None. Used by the map view to decide whether a map
        click places a building (vs. the city itself)."""
        city = self.get_current()
        if not city:
            return None
        idx = self.modify_widget.building_list.current_index()
        if idx is None:
            return None
        return city, idx


class CityModel(PainterModel):
    prefab_cls = cities.City

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            city = self._data[index.row()]
            text = city.nid
            return text
        elif role == Qt.DecorationRole:
            city = self._data[index.row()]
            color = utils.hash_to_color(utils.strhash(city.nid))
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(*color))
            painter = QPainter()
            painter.begin(pixmap)
            painter.setBrush(Qt.NoBrush)
            if city.team == 'player':
                painter.setPen(Qt.blue)
            else:
                painter.setPen(Qt.red)
            painter.setOpacity(0.75)
            painter.drawRect(0, 0, 15, 15)
            painter.end()
            return QIcon(pixmap)
        return None


class CityBuildingList(QWidget):
    """Editable list of buildings assigned to the currently-selected city.

    Each row is a ComboBox picking a building type from `DB.buildings` plus a
    label showing the placement position. Selecting a row makes it the "current
    building" the map view will place when the user clicks the map.

    Operates directly on `city.buildings`, a list of [building_nid, position]
    pairs (position is None until placed).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.current = None
        self.combo_boxes = []
        self.pos_labels = []

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.title_label = QLabel("Buildings")
        layout.addWidget(self.title_label, 0, 0)

        self.add_button = QPushButton("+")
        self.add_button.setMaximumWidth(30)
        self.add_button.clicked.connect(self.add_building)
        self.remove_button = QPushButton("-")
        self.remove_button.setMaximumWidth(30)
        self.remove_button.clicked.connect(self.remove_building)
        layout.addWidget(self.add_button, 0, 1, Qt.AlignRight)
        layout.addWidget(self.remove_button, 0, 2, Qt.AlignRight)

        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget, 1, 0, 1, 3)

    def _building_nids(self):
        return [b.nid for b in DB.buildings]

    def current_index(self):
        idx = self.list_widget.currentRow()
        if self.current and 0 <= idx < len(self.current.buildings):
            return idx
        return None

    def _make_row(self, idx, building_nid, position):
        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_widget.setLayout(row_layout)

        combo_box = ComboBox(row_widget)
        for building in DB.buildings:
            pix = get_pixmap(building)
            if pix:
                combo_box.addItem(QIcon(pix.scaled(16, 16)), building.nid)
            else:
                combo_box.addItem(building.nid)
        if building_nid:
            combo_box.setValue(building_nid)
        combo_box.currentTextChanged.connect(lambda text, i=idx: self.on_type_changed(i, text))
        row_layout.addWidget(combo_box, 1)

        pos_label = QLabel(self._pos_text(position))
        row_layout.addWidget(pos_label)

        self.combo_boxes.append(combo_box)
        self.pos_labels.append(pos_label)
        return row_widget

    def _pos_text(self, position):
        return "(%d, %d)" % (position[0], position[1]) if position else "unplaced"

    def set_current(self, city):
        self.current = city
        self.list_widget.clear()
        self.combo_boxes = []
        self.pos_labels = []
        if not city:
            return
        for idx, (building_nid, position) in enumerate(city.buildings):
            item = QListWidgetItem()
            row_widget = self._make_row(idx, building_nid, position)
            item.setSizeHint(row_widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row_widget)

    def refresh_labels(self):
        """Update only the position labels from city.buildings (after a map
        placement), without rebuilding combo boxes."""
        if not self.current:
            return
        for idx, (_, position) in enumerate(self.current.buildings):
            if idx < len(self.pos_labels):
                self.pos_labels[idx].setText(self._pos_text(position))

    def add_building(self):
        if not self.current:
            return
        nids = self._building_nids()
        if not nids:
            QMessageBox.warning(self.window, 'Warning',
                                'No buildings exist in the database to add')
            return
        self.current.buildings.append([nids[0], None])
        self.set_current(self.current)
        self.list_widget.setCurrentRow(len(self.current.buildings) - 1)
        self.window.window.map_view.update_view()

    def remove_building(self):
        idx = self.current_index()
        if idx is None:
            return
        self.current.buildings.pop(idx)
        self.set_current(self.current)
        self.window.window.map_view.update_view()

    def on_type_changed(self, idx, text):
        if self.current and 0 <= idx < len(self.current.buildings):
            self.current.buildings[idx][0] = text
            self.window.window.map_view.update_view()


class ModifyCityWidget(QWidget):
    def __init__(self, data, parent=None, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = data

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.current = current

        self.icon_edit = ItemIcon32(self)
        layout.addWidget(self.icon_edit)

        self.nid_box = PropertyBox("Unique ID", NidLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        layout.addWidget(self.nid_box)

        self.team_box = TeamBox(self)
        self.team_box.edit.activated.connect(self.team_changed)
        layout.addWidget(self.team_box)

        self.population_box = PropertyBox("Population", QSpinBox, self)
        self.population_box.edit.valueChanged.connect(self.population_changed)
        layout.addWidget(self.population_box)

        self.building_list = CityBuildingList(self)
        layout.addWidget(self.building_list)

    def nid_changed(self, text):
        if self.current:
            self.current.nid = text
            self.current.name = text.replace('_', ' ')
            self.window.update_list()

    def nid_done_editing(self):
        if not self.current:
            return
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values()
                      if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning',
                                'City ID %s already in use' % self.current.nid)
            self.current.nid = str_utils.get_next_name(
                self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def population_changed(self, value):
        self.current.population = value

    def team_changed(self, index):
        team = DB.teams[index]
        self.current.team = team.nid
        self.window.update_list()

    def set_current(self, current):
        self.current = current
        self.icon_edit.set_current(current.icon_nid, current.icon_index)
        self.nid_box.edit.setText(current.nid)
        self.population_box.edit.setValue(current.population)
        if not current.team:
            current.team = DB.teams[0].nid
        self.team_box.edit.setValue(current.team)
        self.building_list.set_current(current)
