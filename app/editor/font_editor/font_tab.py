from app.data.resources.fonts import Font
from app.editor.custom_widgets import CustomQtRoles
import re
from typing import Callable, List

from app.editor.data_editor import MultiResourceEditor, SingleResourceEditor
from app.editor.icon_editor import icon_model
from app.editor.settings.main_settings_controller import MainSettingsController
from app.data.resources.resources import RESOURCES
from app.utilities.data import Data
from app.utilities.typing import NID
from PyQt5.QtCore import QSize, QSortFilterProxyModel, Qt
from PyQt5.QtWidgets import (QCheckBox, QDialog, QGridLayout, QLineEdit,
                             QListView, QListWidget, QPushButton, QVBoxLayout,
                             QWidget)


class FontTab(QWidget):
    def __init__(self, data: List[Font], parent=None):
        super().__init__(parent)
        self.settings = MainSettingsController()
        self._data = data

        self.setWindowTitle("Fonts")
        self.setStyleSheet("font: 10pt;")

        self.layout = QGridLayout(self)

        self.view = IconListView()
        self.view.setMinimumSize(360, 360)
        self.view.setUniformItemSizes(True)
        self.view.setIconSize(QSize(64, 64))
        self.full_model = model(self._data, self)
        self.model = QSortFilterProxyModel()
        self.model.setSourceModel(self.full_model)
        self.view.setModel(self.model)
        self.view.setViewMode(QListView.IconMode)
        self.view.setResizeMode(QListView.Adjust)
        self.view.setMovement(QListView.Static)
        self.view.setGridSize(QSize(80, 80))

        if self.side_menu_enabled:
            self.model.setFilterRole(CustomQtRoles.FilterRole)
            left_layout = QVBoxLayout()

            self.icon_sheet_search = QLineEdit()
            self.icon_sheet_search.setPlaceholderText('Filter by Icon Sheet...')
            self.icon_sheet_search.textChanged.connect(self.filter_icon_sheet_list)

            left_layout.addWidget(self.icon_sheet_search)

            self.icon_sheet_list = QListWidget()
            for i, icon_sheet in enumerate(data):
                self.icon_sheet_list.insertItem(i, icon_sheet.nid)
            self.icon_sheet_list.itemSelectionChanged.connect(self.on_icon_sheet_selection_changed)
            left_layout.addWidget(self.icon_sheet_list)

            self.layout.addLayout(left_layout, 0, 0, 1, 2)
            self.layout.addWidget(self.view, 0, 2, 1, 1)
        else:
            self.layout.addWidget(self.view, 0, 0, 1, 1)

        self.button = QPushButton("Add New Icon Sheet...")
        self.button.clicked.connect(self.full_model.append)
        self.layout.addWidget(self.button, 1, 0, 1, 1)

        self.display = None

        if initial_icon_nid and self.side_menu_enabled:
            self.model.setFilterRegularExpression(re.escape(initial_icon_nid))

    def on_icon_sheet_selection_changed(self):
        item = self.icon_sheet_list.currentItem()
        self.model.setFilterRegularExpression(re.escape(item.text()))

    def filter_icon_sheet_list(self, text):
        text = text.lower()
        if text:
            self.icon_sheet_list.clear()
            for i, icon_sheet in enumerate(self._data):
                if text in icon_sheet.nid.lower():
                    self.icon_sheet_list.insertItem(i, icon_sheet.nid)
        else:
            self.icon_sheet_list.clear()
            for i, icon_sheet in enumerate(self._data):
                self.icon_sheet_list.insertItem(i, icon_sheet.nid)

    def update_list(self):
        # self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))
        self.full_model.layoutChanged.emit()
        if self.side_menu_enabled:
            self.icon_sheet_list.clear()
            for i, icon_sheet in enumerate(self._data):
                self.icon_sheet_list.insertItem(i, icon_sheet.nid)

    def reset(self):
        pass

    def _type(self):
        return self.__class__.__name__

    @property
    def current(self):
        indices = self.view.selectionModel().selectedIndexes()
        if indices:
            index = indices[0]
            index = self.model.mapToSource(index)
            icon = self.full_model.sub_data[index.row()]
            if icon.parent_nid:
                icon.nid = icon.parent_nid
            return icon
        return None