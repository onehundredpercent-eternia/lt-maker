from PyQt5.QtWidgets import QLineEdit, QItemDelegate
from PyQt5.QtCore import Qt

from app.extensions.list_models import DoubleListModel


class FixedKeyMutableValueDelegate(QItemDelegate):
    key_column = 0
    value_column = 1

    def createEditor(self, parent, option, index):
        if index.column() == self.key_column:
            editor = QLineEdit(parent)
            editor.setDisabled(True)
            return editor
        elif index.column() == self.value_column:
            editor = QLineEdit(parent)
            return editor
        else:
            return super().createEditor(parent, option, index)


class KeyValueDelegate(QItemDelegate):
    key_column = 0
    value_column = 1

    def createEditor(self, parent, option, index):
        if index.column() == self.key_column:
            editor = QLineEdit(parent)
            return editor
        elif index.column() == self.value_column:
            editor = QLineEdit(parent)
            return editor
        else:
            return super().createEditor(parent, option, index)

class KeyValueDoubleListModel(DoubleListModel):
    """
    Handles a simple list of 2-tuples/lists where
    both values are strings that can be edited
    """
    def create_new(self):
        new_key = "New Key"
        new_value = "New Value"
        self._data.append([new_key, new_value])

class KeyValueDictModel(DoubleListModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            key = list(self._data.keys())[index.row()]
            value = self._data[key]
            if index.column() == 0:
                return key
            else:
                return value
        return None

    def create_new(self):
        new_key = "New Arg"
        new_value = "New Value"
        self._data[new_key] = new_value

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        key = list(self._data.keys())[index.row()]
        if index.column() == 0: # changing key
            new_key = value
            old_value = self._data.pop(key)
            self._data[new_key] = old_value
        else:
            self._data[key] = value
        self.dataChanged.emit(index, index)
        return True

    def delete(self, idx):
        if len(self._data) > idx:
            key = list(self._data.keys())[idx]
            self._data.pop(key)
        self.layoutChanged.emit()