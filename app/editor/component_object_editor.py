from __future__ import annotations

import json
import logging
import os
from typing import Dict, Generic, List, Optional, Type, TypeVar
import uuid

from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QGridLayout, QHBoxLayout,
                             QMessageBox, QPushButton, QSplitter, QVBoxLayout,
                             QWidget)

from app.data.category import Categories, CategorizedCatalog
from app.data.database.database import DB, Database
from app.data.database.items import ItemPrefab
from app.editor.component_editor_properties import DBItemSkillLike, NewComponentProperties
from app.editor.lib.components.nested_list import LTNestedList
from app.editor.lib.state_editor.editor_state_manager import EditorStateManager
from app.utilities import str_utils
from app.utilities.typing import NID

T = TypeVar('T', bound=CategorizedCatalog)

class ComponentObjectEditor(QWidget, Generic[T]):
    catalog_type: Type[T]
    properties_type: Type[NewComponentProperties[DBItemSkillLike]]

    def __init__(self, parent, database: Database, state_manager: Optional[EditorStateManager] = None) -> None:
        QWidget.__init__(self, parent)
        self._db = database
        self.state_manager = state_manager

        self.left_frame = QWidget()
        left_frame_layout = QVBoxLayout()
        self.left_frame.setLayout(left_frame_layout)
        self.tree_list = LTNestedList(self, self.data.keys(), self.categories, self.get_icon,
                                      self.on_select, self.resort_db, self.delete_from_db, self.create_new,
                                      self.duplicate)
        left_frame_layout.setContentsMargins(0, 0, 0, 0)
        left_frame_layout.setSpacing(0)
        left_frame_layout.addWidget(self.tree_list)

        button_frame = QWidget()
        button_frame_layout = QGridLayout(button_frame)
        import_csv_button = QPushButton("Import .csv")
        import_csv_button.clicked.connect(self.import_csv)
        button_frame_layout.addWidget(import_csv_button, 0, 0, 1, 4)
        import_xml_button = QPushButton("Import .xml")
        import_xml_button.clicked.connect(self.import_xml)
        button_frame_layout.addWidget(import_xml_button, 1, 0, 1, 4)
        copy_to_clipboard_button = QPushButton("Copy to clipboard")
        copy_to_clipboard_button.clicked.connect(self.copy_to_clipboard)
        button_frame_layout.addWidget(copy_to_clipboard_button, 2, 0, 1, 2)
        paste_from_clipboard_button = QPushButton("Paste from clipboard")
        paste_from_clipboard_button.clicked.connect(self.paste_from_clipboard)
        button_frame_layout.addWidget(paste_from_clipboard_button, 2, 2, 1, 2)
        left_frame_layout.addWidget(button_frame)
        self.right_frame = self.properties_type(self, None, self.attempt_change_nid, lambda: self.tree_list.regenerate_icons(initial_generation=True))
        self.splitter = QSplitter(self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.left_frame)
        self.splitter.addWidget(self.right_frame)
        self.splitter.setStyleSheet(
            "QSplitter::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc); border: 1px solid #777; width: 13px; margin-top: 2px; margin-bottom: 2px; border-radius: 4px;}")

        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)

        self._layout.addWidget(self.splitter)
        # self.installEventFilter(self)

        self._window_id = str(uuid.uuid4())
        if self.state_manager:
            self.state_manager.subscribe_to_key(self._window_id, 'item_db_changed', self.reset)

    @property
    def data(self) -> T:
        raise NotImplementedError("This class must be extended and this method overriden.")

    @property
    def categories(self) -> Categories:
        return self.data.categories

    @classmethod
    def edit(cls, parent=None):
        raise NotImplementedError("This class must be extended and this method overriden.")

    def get_icon(self, nid) -> Optional[QIcon]:
        raise NotImplementedError("This class must be extended and this method overriden.")

    def import_csv(self):
        raise NotImplementedError("This class must be extended and this method overriden.")

    def import_xml(self):
        raise NotImplementedError("This class must be extended and this method overriden.")

    def reset(self, _=None):
        if self.data.keys() != self.tree_list.get_list_and_category_structure()[0]:
            self.tree_list.reset(self.data.keys(), self.categories)
            current_selected = self.right_frame.get_current()
            if current_selected and current_selected.nid not in self.data.keys():
                self.on_select(None)

    def attempt_change_nid(self, old_nid: NID, new_nid: NID) -> bool:
        current = self.right_frame.get_current()
        if not current: # should never happen
            return False
        if not new_nid:
            return False
        if old_nid == new_nid:
            return True
        if self.data.get(new_nid):
            QMessageBox.warning(self, 'Warning', 'ID %s already in use' % new_nid)
            return False
        self.data.change_key(old_nid, new_nid)
        self.tree_list.update_nid(old_nid, new_nid)
        if self.state_manager:
            self.state_manager.change_and_broadcast('item_db_changed', None, self._window_id)
        return True

    def save_item_changes(self, current: DBItemSkillLike):
        self.data.update_obj(current)
        if self.state_manager:
            self.state_manager.change_and_broadcast('item_db_changed', None, self._window_id)

    def on_select(self, entry_nid: Optional[NID]):
        sel_obj = self.right_frame.get_current()
        if sel_obj and sel_obj.nid != entry_nid and sel_obj.nid in self.data.keys():
            self.save_item_changes(sel_obj)
        if not entry_nid:
            self.right_frame.set_current(None)
            return
        curr_entry = self.data.get(entry_nid)
        if curr_entry:
            self.right_frame.set_current(curr_entry)

    def resort_db(self, entries: List[str], categories: Categories):
        self.data.categories = categories
        self.data.sort(lambda x: entries.index(x.nid) if x.nid in entries else -1)
        if self.state_manager:
            self.state_manager.change_and_broadcast('item_db_changed', None, self._window_id)

    def delete_from_db(self, nid):
        self.data.remove_key(nid)
        if self.state_manager:
            self.state_manager.change_and_broadcast('item_db_changed', None, self._window_id)
        return True

    def create_new(self, nid):
        if self.data.get(nid):
            QMessageBox.warning(self, 'Warning', 'ID %s already in use' % nid)
            return False
        new_obj = self.catalog_type.datatype(nid, nid, '')
        self.data.append(new_obj)
        if self.state_manager:
            self.state_manager.change_and_broadcast('item_db_changed', None, self._window_id)
        return True

    def duplicate(self, old_nid, nid):
        if self.data.get(nid):
            QMessageBox.warning(self, 'Warning', 'ID %s already in use' % nid)
            return False
        orig_obj = self.data.get(old_nid)
        if not orig_obj:
            QMessageBox.warning(self, 'Warning', 'ID %s not found' % old_nid)
            return False
        orig_obj = self.catalog_type.datatype.restore(orig_obj.save())
        orig_obj.nid = nid
        self.data.append(orig_obj)
        if self.state_manager:
            self.state_manager.change_and_broadcast('item_db_changed', None, self._window_id)
        return True

    def copy_to_clipboard(self):
        selected_nid = self.tree_list.get_selected_nid()
        if selected_nid:
            clipboard = QApplication.clipboard()
            prefab = self.data.get(selected_nid)
            if prefab:
                json_string = json.dumps([prefab.save()])
                clipboard.setText(json_string)

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        json_string = clipboard.text()
        try:
            any_nid = None
            ser_list = json.loads(json_string)
            for ser_dict in reversed(ser_list):
                prefab = self.data.datatype.restore(ser_dict)
                prefab.nid = str_utils.get_next_name(prefab.nid, self.data.keys())
                self.data.append(prefab)
                any_nid = prefab.nid
            if self.state_manager:
                self.state_manager.change_and_broadcast('item_db_changed', None, self._window_id)
            if any_nid:
                self.tree_list.select_item(any_nid)
        except Exception as e:
            logging.warning("Could not read from clipboard! %s" % e)
            QMessageBox.critical(self, "Import Error", "Could not read valid json from clipboard!")

    # @todo(mag) fix the unit tab (which is the only time this callback is used forcibly in data_editor.py) and remove this
    def on_tab_close(self):
        pass

    @classmethod
    def create(cls, parent=None, db=None):
        db = db or DB
        return cls(parent, db)
