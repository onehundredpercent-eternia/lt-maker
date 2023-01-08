from __future__ import annotations
from app.data.database.items import ItemPrefab

from dataclasses import dataclass, field
from pprint import pprint
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel

from app.data.category import Categories, CategorizedCatalog
from app.utilities.data import Data, Prefab
import app.editor.utilities as editor_utilities
from app.utilities.typing import NID
from PyQt5 import QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont, QIcon, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import (QAction, QMenu, QPushButton, QStyledItemDelegate,
                             QTreeWidget, QTreeWidgetItem, QVBoxLayout,
                             QWidget)
from app.data.database.database import DB


@dataclass
class ListNode():
    nid: NID
    is_category: bool = False
    children: Dict[NID, ListNode] = field(default_factory=dict)

def _treeify(list_entries: List[NID], list_categories: Categories) -> ListNode:
    root = ListNode('root', True)
    for nid in list_entries:
        curr_node = root
        item_categories = list_categories.get(nid, None)
        if item_categories:
            for category in item_categories:
                new_node = ListNode(category, True)
                if category not in curr_node.children:
                    curr_node.children[category] = new_node
                curr_node = curr_node.children[category]
        list_item = ListNode(nid)
        curr_node.children[nid] = list_item
    return root

def _build_tree_widget(root: ListNode, parent: TreeModel | QStandardItem):
    for node in root.children.values():
        item = QStandardItem(node.nid)
        parent.appendRow(item)
        if(node.is_category):
            _build_tree_widget(node, item)

def get_pixmap(item: ItemPrefab):
    x, y = item.icon_index
    res = RESOURCES.icons16.get(item.icon_nid)
    if not res:
        return None
    if not res.pixmap:
        res.pixmap = QPixmap(res.full_path)
    pixmap = res.pixmap.copy(x*16, y*16, 16, 16)
    pixmap = QPixmap.fromImage(editor_utilities.convert_colorkey(pixmap.toImage()))
    return pixmap

def create_empty_icon(w: int, h: int):
    pixmap = QPixmap(QSize(w, h))
    pixmap.fill(QtCore.Qt.transparent)
    return QIcon(pixmap)

class TreeModel(QStandardItemModel):
    def __init__(self, parent, catalog: CategorizedCatalog[Prefab]):
        super().__init__(parent)
        tree_struct = _treeify(catalog.keys(), catalog.categories)
        _build_tree_widget(tree_struct, self)

    def _get_icon(self, item: Optional[QStandardItem]) -> QIcon:
        if not item:
            return create_empty_icon(32, 32)
        nid = item.text()
        db_item = DB.items.get(nid)
        if db_item:
            pix = get_pixmap(db_item)
            if pix:
                pix = pix.scaled(32, 32)
                return QIcon(pix)
        if item.hasChildren():
            return self._get_icon(item.child(0))
        return create_empty_icon(32, 32)

    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return None
        item = self.item(index.row(), index.column())
        nid = item.text()
        if role == Qt.DisplayRole:
            return nid
        elif role == Qt.DecorationRole:
            return self._get_icon(item)
        return None

# Run "python -m app.editor.data_models.item_model" from main directory
if __name__ == '__main__':
    import sys

    from PyQt5.QtWidgets import QApplication, QHBoxLayout, QTreeView, QWidget
    app = QApplication(sys.argv)
    from app.data.resources.resources import RESOURCES
    RESOURCES.load('../../ano.ltproj')
    DB.load('../../ano.ltproj')
    w = QWidget()
    layout = QHBoxLayout(w)
    view = QTreeView()
    model = TreeModel(None, DB.items)
    view.setModel(model)
    view.expandAll()
    view.header().hide()
    layout.addWidget(view)
    # window = SingleDatabaseEditor(PartyDatabase)
    # window.show()
    w.show()
    app.exec_()

