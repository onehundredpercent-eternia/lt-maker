from app.utilities import str_utils
from app.data.raw_data import RawListDataObjectBase
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
        nids = [d.nid for d in self._data]
        nid = str_utils.get_next_name("Key", nids)
        o = RawListDataObjectBase()
        for h in self._headers:
            setattr(o, h, "")
        o.nid = nid
        self._data.append(o)
