from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap

from app.data.resources.resources import RESOURCES
from app.editor.base_database_gui import DragDropCollectionModel

import app.editor.utilities as editor_utilities


def get_pixmap(tech):
    if not tech:
        return None
    x, y = tech.icon_index
    res = RESOURCES.icons16.get(tech.icon_nid)
    if not res:
        return None
    if not res.pixmap:
        res.pixmap = QPixmap(res.full_path)
    pixmap = res.pixmap.copy(x * 16, y * 16, 16, 16)
    pixmap = QPixmap.fromImage(editor_utilities.convert_colorkey(pixmap.toImage()))
    return pixmap


class TechModel(DragDropCollectionModel):
    """Small list model behind tech comboboxes and deletion dialogs. The Techs tab itself
    is a NewEditorTab, which builds its own tree from the catalog."""

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self._data[index.row()].nid
        elif role == Qt.DecorationRole:
            pix = get_pixmap(self._data[index.row()])
            if pix:
                return QIcon(pix.scaled(32, 32))
        return None
