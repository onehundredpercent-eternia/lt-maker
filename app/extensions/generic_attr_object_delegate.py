from app.extensions.list_models import MultiAttrListModel
from PyQt5.QtWidgets import QItemDelegate, QLineEdit


class GenericObjectDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

class GenericObjectListModel(MultiAttrListModel):
    """
    Handles rows of arbitrary size and header
    """
    def create_new(self):
        o = type('', (), {})()
        for h in self._headers:
            setattr(o, h, "")
        self._data.append(o)
