from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt

from app.data.database import DB

from app.editor.base_database_gui import DragDropCollectionModel
from app.utilities import str_utils

from app.data import hex_type

class HexTypeModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            hex_type = self._data[index.row()]
            text = hex_type.nid
            return text
        elif role == Qt.DecorationRole:
            hex_type = self._data[index.row()]
            color = hex_type.color
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(color[0], color[1], color[2]))
            return QIcon(pixmap)
        return None

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = str_utils.get_next_name("New Hex Type", nids)
        new_hex_type = hex_type.HexType(nid, name, (0, 0, 0), 1)
        DB.hex_type.append(new_hex_type)
        return new_hex_type
