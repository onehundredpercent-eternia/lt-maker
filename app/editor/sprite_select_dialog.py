from app.utilities.typing import NID
from typing import Tuple
from app.resources.panoramas import Panorama
from app.resources.resources import RESOURCES
from app.data.database import DB
from app.editor.base_database_gui import CollectionModel
from app.editor.icon_editor.icon_tab import IconListView
from app.extensions.custom_gui import PropertyBox
from app.sprites import SPRITES, BasicSprite
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QGridLayout, QLineEdit,
                             QListView)


class SpriteModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            sprite = self._data[index.row()]
            text = sprite.nid
            return text
        elif role == Qt.DecorationRole:
            sprite = self._data[index.row()]
            if isinstance(sprite, Panorama):
                panorama = sprite
                if not panorama.pixmaps:
                    for path in panorama.get_all_paths():
                        panorama.pixmaps.append(QPixmap(path))
                return QIcon(panorama.pixmaps[0])
            elif sprite.pixmap:
                return QIcon(sprite.pixmap)
        return None

class SpriteSelectionDialog(QDialog):
    def __init__(self, parent=None, with_panoramas: bool = False):
        super().__init__(parent)
        self._data = [sprite for sprite in SPRITES.values() if isinstance(sprite, BasicSprite)]
        if with_panoramas:
            self._data += [panorama for panorama in RESOURCES.panoramas.values()]

        self.setWindowTitle("Sprites")
        self.setStyleSheet("font: 10pt;")

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.filter = PropertyBox("Filter", QLineEdit, self, True)
        self.filter.edit.textChanged.connect(self.on_filter)

        self.view = IconListView()
        self.view.setMinimumSize(240*3 + 22, 240*3)
        self.view.setIconSize(QSize(240, 240))
        self.model = SpriteModel(self._data, self)
        self.view.setModel(self.model)
        self.view.setViewMode(QListView.IconMode)
        self.view.setResizeMode(QListView.Adjust)
        self.view.setMovement(QListView.Static)
        self.view.setGridSize(QSize(240, 240))

        self.layout.addWidget(self.filter, 0, 0, 1, 2)
        self.layout.addWidget(self.view, 1, 0, 1, 2)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.layout.addWidget(self.buttonbox, 2, 0, 1, 2)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.selected_sprite: str = None

    def on_filter(self):
        text = self.filter.edit.text()
        if not text:
            for i in range(self.model.rowCount()):
                self.view.setRowHidden(i, False)
            self.view.setDragEnabled(True)
            return
        else:
            try:
                for i in range(self.model.rowCount()):
                    self.view.setRowHidden(i, False)
                    index = self.model.index(i)
                    match = False
                    name: str = self.model.data(index, Qt.DisplayRole)
                    if text.lower() in name.lower():
                        match = True
                    if not match:
                        self.view.setRowHidden(i, True)
                self.view.setDragEnabled(False)
            except Exception as e:
                print(e)

    @property
    def current(self) -> NID:
        indices = self.view.selectionModel().selectedIndexes()
        if indices:
            index = indices[0]
            bg = self.model._data[index.row()]
            return bg.nid
        return None

def get_sprite(with_panoramas=False):
    window = SpriteSelectionDialog(with_panoramas=with_panoramas)
    result = window.exec_()
    if result == QDialog.Accepted:
        selected_sprite = window.current
        return selected_sprite, True
    else:
        return None, False