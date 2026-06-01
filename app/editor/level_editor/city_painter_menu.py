from PyQt5.QtWidgets import QPushButton, \
    QWidget, QVBoxLayout, QMessageBox, QSpinBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor, QPixmap, QPainter

from app.data.database.database import DB

from app.utilities import utils, str_utils
from app.utilities.data import Data

from app.extensions.custom_gui import PropertyBox, RightClickListView
from app.editor.base_database_gui import DragDropCollectionModel
from app.editor.custom_widgets import TeamBox
from app.editor.lib.components.validated_line_edit import NidLineEdit
from app.data import cities

from app.editor.level_editor.region_painter_menu import RegionMenu


class CityMenu(RegionMenu):
    def __init__(self, state_manager, map_view):
        super().__init__()
        self.state_manager = state_manager
        self.map_view = map_view
        self.current_level = DB.levels.get(
            self.state_manager.state.selected_level)
        if self.current_level:
            self._data = self.current_level.cities
        else:
            self._data = Data()

        grid = QVBoxLayout()
        self.setLayout(grid)

        self.view = RightClickListView(
            (None, None, None), parent=self)
        self.view.currentChanged = self.on_item_changed

        self.model = CityModel(self._data, self)
        self.view.setModel(self.model)

        grid.addWidget(self.view)

        self.create_button = QPushButton("Create City...")
        self.create_button.clicked.connect(self.create_city)
        grid.addWidget(self.create_button)

        self.modify_city_widget = ModifyCityWidget(self._data, self)
        grid.addWidget(self.modify_city_widget)

        self.check_whether_enabled()

        self.last_touched_city = None
        self.display = self.modify_city_widget

        self.state_manager.subscribe_to_key(
            CityMenu.__name__, 'selected_level', self.set_current_level)
        self.state_manager.subscribe_to_key(
            CityMenu.__name__, 'ui_refresh_signal', self._refresh_view)

    def check_whether_enabled(self):
        if not len(self._data):
            self.modify_city_widget.setEnabled(False)

    def set_current_level(self, level_nid):
        level = DB.levels.get(level_nid)
        self.current_level = level
        self._data = self.current_level.cities
        self.model._data = self._data
        self.model.update()
        self.modify_city_widget._data = self._data
        if len(self._data):
            self.modify_city_widget.setEnabled(True)
            city = self._data[0]
            if city.position:
                self.map_view.center_on_pos(city.position)
            self.modify_city_widget.set_current(city)
        else:
            self.modify_city_widget.setEnabled(False)

    def on_item_changed(self, curr, prev):
        if self._data:
            city = self._data[curr.row()]
            if city.position:
                self.map_view.center_on_pos(city.position)
            self.modify_city_widget.set_current(city)

    def create_city(self, example=None):
        nid = str_utils.get_next_name('New City', self._data.keys())
        created_city = cities.City(nid)
        self._data.append(created_city)
        self.modify_city_widget.setEnabled(True)
        self.model.update()
        if len(self._data) == 1:
            self.modify_city_widget.set_current(created_city)
        # Select the city
        idx = self._data.index(created_city.nid)
        index = self.model.index(idx)
        self.view.setCurrentIndex(index)
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)
        return created_city


class CityModel(DragDropCollectionModel):
    allow_delete_last_obj = True

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
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(*color))
            painter = QPainter()
            painter.begin(pixmap)
            painter.setBrush(Qt.NoBrush)
            if city.team == 'player':
                painter.setPen(Qt.blue)
            else:
                painter.setPen(Qt.red)
            painter.setOpacity(0.75)
            painter.drawRect(0, 0, 32, 32)
            painter.end()
            return QIcon(pixmap)
        return None

    def new(self, idx):
        ok = self.window.create_city()
        if ok:
            self._data.move_index(len(self._data) - 1, idx + 1)
            self.layoutChanged.emit()

    def duplicate(self, idx):
        view = self.window.view
        obj = self._data[idx]
        new_nid = str_utils.get_next_name(obj.nid, self._data.keys())
        serialized_obj = obj.save()
        new_obj = cities.City.restore(serialized_obj)
        new_obj.nid = new_nid
        self._data.insert(idx + 1, new_obj)
        self.layoutChanged.emit()
        new_index = self.index(idx + 1)
        view.setCurrentIndex(new_index)
        return new_index

    def delete(self, idx):
        super().delete(idx)
        self.window.check_whether_enabled()

class ModifyCityWidget(QWidget):
    def __init__(self, data, parent=None, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = data

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.current = current

        self.nid_box = PropertyBox("Unique ID", NidLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        layout.addWidget(self.nid_box)

        self.team_box = TeamBox(self)
        self.team_box.edit.setValue(self.current.team)
        self.team_box.edit.activated.connect(self.team_changed)
        layout.addWidget(self.team_box)

        self.population_box = PropertyBox("Population", QSpinBox, self)
        self.population_box.edit.setValue(self.current.population)
        self.population_box.edit.valueChanged.connect(self.population_changed)
        layout.addWidget(self.population_box)

    def nid_changed(self, text):
        if self.current:
            self.current.nid = text
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
        self.nid_box.edit.setText(current.nid)
        self.population_box.edit.setValue(current.population)
        self.team_box.edit.setValue(current.team)
