from app.data import ui_prefab
from app.data.database import DB
from app.editor.base_database_gui import DragDropCollectionModel
from app.utilities import str_utils
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor


class ComponentModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            ui_component = self._data[index.row()]
            text = ui_component.nid
            return text
        elif role == Qt.ForegroundRole:
            ui_component = self._data[index.row()]
            if ui_component.generic:
                return QBrush(QColor("blue"))
            elif ui_component.locked:
                return QBrush(QColor("red"))
            else:
                return QBrush(QColor("black"))
        return None

    def delete(self, idx):
        ui_component = self._data[idx]
        if ui_component.locked or ui_component.generic: # can't delete locked or generic components
            return
        super().delete(idx)

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = str_utils.get_next_name("New UI component", nids)
        new_ui = ui_prefab.UIObjectPrefab(nid, (50, 24), False)
        DB.custom_ui.append(new_ui)
        self.layoutChanged.emit()
        return new_ui
