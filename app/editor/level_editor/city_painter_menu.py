from PyQt5.QtWidgets import \
    QWidget, QVBoxLayout, QMessageBox, QSpinBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor, QPixmap, QPainter

from app.data.database.database import DB

from app.utilities import utils, str_utils

from app.extensions.custom_gui import PropertyBox
from app.editor.custom_widgets import TeamBox
from app.editor.icons import ItemIcon32
from app.editor.lib.components.validated_line_edit import NidLineEdit
from app.editor.level_editor.painter_menu import PainterMenu, PainterModel
from app.data import cities


class CityMenu(PainterMenu):
    def __init__(self, state_manager, map_view):
        super().__init__(state_manager, map_view, noun='City', data_attr='cities',
                         model_cls=CityModel, modify_widget_cls=ModifyCityWidget,
                         prefab_cls=cities.City)


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
        self.icon_edit.set_current(current.icon_nid, current.icon_index)
        self.nid_box.edit.setText(current.nid)
        self.population_box.edit.setValue(current.population)
        if not current.team:
            current.team = DB.teams[0].nid
        self.team_box.edit.setValue(current.team)
