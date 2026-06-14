from PyQt5.QtWidgets import QLineEdit, \
    QWidget, QVBoxLayout, QMessageBox, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor, QPixmap

from app.data.database.database import DB
from app.editor.code_line_edit import CodeLineEdit
from app.events.regions import RegionType, RegionHighlight

from app.utilities import utils, str_utils

from app.extensions.custom_gui import PropertyBox, PropertyCheckBox, ComboBox
from app.editor.custom_widgets import SkillBox, TerrainBox
from app.editor.lib.components.validated_line_edit import NidLineEdit
from app.editor.level_editor.painter_menu import PainterMenu, PainterModel
from app.events import regions

from app.editor import timer


class RegionMenu(PainterMenu):
    def __init__(self, state_manager, map_view):
        super().__init__(state_manager, map_view, noun='Region', data_attr='regions',
                         model_cls=RegionModel, modify_widget_cls=ModifyRegionWidget,
                         prefab_cls=regions.Region)
        timer.get_timer().tick_elapsed.connect(self.tick)

    def get_center(self, obj):
        return obj.center if obj.position else None

    def tick(self):
        status_box = self.modify_widget.status_box
        status_box.model.layoutChanged.emit()
        terrain_box = self.modify_widget.terrain_box
        terrain_box.model.layoutChanged.emit()


class RegionModel(PainterModel):
    prefab_cls = regions.Region

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            reg = self._data[index.row()]
            text = reg.nid + ': ' + reg.region_type
            if reg.region_type in (RegionType.STATUS, RegionType.FOG, RegionType.VISION, RegionType.TERRAIN):
                if reg.sub_nid:
                    text += ' ' + reg.sub_nid
            elif reg.region_type == RegionType.EVENT:
                if reg.sub_nid:
                    text += ' ' + reg.sub_nid
                if reg.condition:
                    text += '\n' + reg.condition
            return text
        elif role == Qt.DecorationRole:
            reg = self._data[index.row()]
            color = utils.hash_to_color(utils.strhash(reg.nid))
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(*color))
            return QIcon(pixmap)
        return None


class ModifyRegionWidget(QWidget):
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

        self.region_type_box = PropertyBox("Region Type", ComboBox, self)
        self.region_type_box.edit.addItems(list(RegionType))
        # self.region_type_box.edit.setValue(self.current.region_type)
        self.region_type_box.edit.currentIndexChanged.connect(
            self.region_type_changed)
        layout.addWidget(self.region_type_box)

        self.sub_nid_box = PropertyBox("Trigger Name", QLineEdit, self)
        # if self.current.sub_nid and self.current.region_type == 'Event':
        #     self.sub_nid_box.edit.setText(self.current.sub_nid)
        self.sub_nid_box.edit.textChanged.connect(self.sub_nid_changed)
        layout.addWidget(self.sub_nid_box)
        
        self.highlight_box = PropertyBox("Highlight", ComboBox, self)
        self.highlight_box.edit.addItems(list(RegionHighlight))
        self.highlight_box.edit.currentIndexChanged.connect(
            self.highlight_changed)
        layout.addWidget(self.highlight_box)

        self.condition_box = PropertyBox("Condition", CodeLineEdit, self)
        # self.condition_box.edit.setText(self.current.condition)
        self.condition_box.edit.textChanged.connect(lambda: self.condition_changed(self.condition_box.edit.toPlainText()))
        layout.addWidget(self.condition_box)

        self.time_left_box = PropertyBox("Num Turns", QLineEdit, self)
        self.time_left_box.edit.textChanged.connect(self.time_left_changed)
        layout.addWidget(self.time_left_box)

        self.only_once_box = PropertyCheckBox("Only once?", QCheckBox, self)
        self.only_once_box.edit.stateChanged.connect(self.only_once_changed)
        layout.addWidget(self.only_once_box)

        self.interrupt_move_box = PropertyCheckBox("Interrupts Movement?", QCheckBox, self)
        self.interrupt_move_box.edit.stateChanged.connect(self.interrupt_move_changed)
        layout.addWidget(self.interrupt_move_box)
        
        self.hide_time_box = PropertyCheckBox("Hide time?", QCheckBox, self)
        self.hide_time_box.edit.stateChanged.connect(self.hide_time_changed)
        layout.addWidget(self.hide_time_box)

        self.status_box = SkillBox(self)
        self.status_box.edit.currentIndexChanged.connect(self.status_changed)
        layout.addWidget(self.status_box)

        self.terrain_box = TerrainBox(self)
        self.terrain_box.edit.currentIndexChanged.connect(self.terrain_changed)
        layout.addWidget(self.terrain_box)

        self.sub_nid_box.hide()
        self.highlight_box.hide()
        self.condition_box.hide()
        self.only_once_box.hide()
        self.interrupt_move_box.hide()
        self.hide_time_box.hide()
        self.status_box.hide()
        self.terrain_box.hide()

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
                                'Region ID %s already in use' % self.current.nid)
            self.current.nid = str_utils.get_next_name(
                self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def region_type_changed(self, index):
        if not self.current:
            return
        self.current.region_type = self.region_type_box.edit.currentText().lower()
        # Just hide them all
        self.sub_nid_box.hide()
        self.highlight_box.hide()
        self.condition_box.hide()
        self.only_once_box.hide()
        self.interrupt_move_box.hide()
        self.status_box.hide()
        self.terrain_box.hide()
        if self.current.region_type in (RegionType.NORMAL, RegionType.STATUS, RegionType.TERRAIN, RegionType.EVENT):
            self.highlight_box.show()
        if self.current.region_type in (RegionType.NORMAL, RegionType.FORMATION):
            pass
        elif self.current.region_type == RegionType.STATUS:
            self.status_box.show()
        elif self.current.region_type == RegionType.TERRAIN:
            self.terrain_box.show()
        elif self.current.region_type == RegionType.EVENT:
            self.sub_nid_box.label.setText("Trigger Name")
            self.sub_nid_box.show()
            self.condition_box.show()
            self.only_once_box.show()
            self.interrupt_move_box.show()
        elif self.current.region_type in (RegionType.VISION, RegionType.FOG):
            self.sub_nid_box.label.setText("Range")
            self.sub_nid_box.show()
            
        self.hide_time_box.show()

    def sub_nid_changed(self, text):
        self.current.sub_nid = text
        self.window.update_list()

    def highlight_changed(self, index):
        if self.highlight_box.edit.currentText() != 'none':
            self.current.highlight = self.highlight_box.edit.currentText()
        else:
            self.current.highlight = None

    def condition_changed(self, text):
        self.current.condition = text
        self.window.update_list()

    def time_left_changed(self, text):
        if text and str_utils.is_int(text):
            self.current.time_left = int(text)
        else:
            self.current.time_left = None

    def only_once_changed(self, state):
        self.current.only_once = bool(state)

    def interrupt_move_changed(self, state):
        self.current.interrupt_move = bool(state)
        
    def hide_time_changed(self, state):
        self.current.hide_time = bool(state)

    def status_changed(self, index):
        self.current.sub_nid = self.status_box.edit.currentText()
        self.window.update_list()

    def terrain_changed(self, index):
        terrain = DB.terrain[index]
        self.current.sub_nid = terrain.nid
        self.window.update_list()

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.region_type_box.edit.setValue(current.region_type)
        self.highlight_box.edit.setValue(current.highlight)
        self.condition_box.edit.setPlainText(current.condition)
        self.time_left_box.edit.setText(str(current.time_left) if current.time_left is not None else '')
        self.only_once_box.edit.setChecked(bool(current.only_once))
        self.interrupt_move_box.edit.setChecked(bool(current.interrupt_move))
        self.hide_time_box.edit.setChecked(bool(current.hide_time))
        if current.region_type == RegionType.STATUS:
            self.status_box.edit.setValue(str(current.sub_nid))
        elif current.region_type == RegionType.TERRAIN:
            self.terrain_box.setValue(str(current.sub_nid))
        elif current.region_type in (RegionType.EVENT, RegionType.FOG, RegionType.VISION):
            self.sub_nid_box.edit.setText(str(current.sub_nid))
        else:
            self.sub_nid_box.edit.setText('')
