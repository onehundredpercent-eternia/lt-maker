from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QHBoxLayout, QMessageBox, QSplitter, QWidget, QGridLayout, QPushButton, QFileDialog
from app.data.resources.resources import Resources
from app.editor import timer
from app.editor.data_editor import SingleDatabaseEditor
from app.editor.settings.main_settings_controller import MainSettingsController

import app.engine.item_component_access as ICA
from app.data.database import items
from app.data.database.database import DB, Database
from app.data.database.items import ItemCatalog, ItemPrefab
from app.editor.item_editor import item_model, item_import
from app.editor.decoupled_component_properties import NewComponentProperties
from app.editor.lib.components.nested_list import (LTNestedList,
                                                   createClearQIcon)
from app.utilities import str_utils
from app.utilities.typing import NID

def get_item_icon(item_nid):
    pix = item_model.get_pixmap(DB.items.get(item_nid))
    if pix:
        return QIcon(pix.scaled(32, 32))
    else:
        return createClearQIcon(32, 32)

class NewItemProperties(NewComponentProperties[ItemPrefab]):
    title = "Item"
    get_components = staticmethod(ICA.get_item_components)
    get_templates = staticmethod(ICA.get_templates)
    get_tags = staticmethod(ICA.get_item_tags)

class NewItemDatabase(QWidget):
    def __init__(self, parent, database: Database) -> None:
        QWidget.__init__(self, parent)
        self._db = database
        self.categories = database.items.categories

        self.left_frame = QWidget()
        left_frame_layout = QGridLayout()
        self.left_frame.setLayout(left_frame_layout)
        self.tree_list = LTNestedList(self, self.data.keys(), self.categories, get_item_icon,
                                      self.on_select, self.resort_db, self.delete_from_db, self.create_new,
                                      self.duplicate)
        left_frame_layout.addWidget(self.tree_list, 0, 0, 1, 4)
        self.import_csv_button = QPushButton("Import .csv")
        self.import_csv_button.clicked.connect(self.import_csv)
        left_frame_layout.addWidget(self.import_csv_button, 1, 0, 1, 4)
        self.copy_to_clipboard_button = QPushButton("Copy to clipboard")
        self.copy_to_clipboard_button.clicked.connect(self.copy_to_clipboard)
        left_frame_layout.addWidget(self.copy_to_clipboard_button, 2, 0, 1, 2)
        self.paste_from_clipboard_button = QPushButton("Paste from clipboard")
        self.paste_from_clipboard_button.clicked.connect(self.paste_from_clipboard)
        left_frame_layout.addWidget(self.paste_from_clipboard_button, 2, 2, 1, 2)

        self.right_frame = NewItemProperties(self, None, self.attempt_change_nid, lambda: self.tree_list.regenerate_icons(True))
        self.splitter = QSplitter(self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.left_frame)
        self.splitter.addWidget(self.right_frame)
        self.splitter.setStyleSheet(
            "QSplitter::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc); border: 1px solid #777; width: 13px; margin-top: 2px; margin-bottom: 2px; border-radius: 4px;}")

        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)

        self._layout.addWidget(self.splitter)

    @property
    def data(self):
        return self._db.items

    def reset(self):
        self.tree_list.reset(self.data.keys(), self.categories)

    def attempt_change_nid(self, old_nid: NID, new_nid: NID) -> bool:
        if old_nid == new_nid:
            return True
        if self.data.get(new_nid):
            QMessageBox.warning(self, 'Warning', 'ID %s already in use' % new_nid)
            return False
        self.data.change_key(old_nid, new_nid)
        self.tree_list.update_nid(old_nid, new_nid)
        return True

    def on_select(self, item_nid: Optional[NID]):
        if not item_nid:
            self.right_frame.set_current(None)
            return
        curr_item = self.data.get(item_nid)
        if curr_item:
            self.right_frame.set_current(curr_item)

    def resort_db(self, entries: List[str], categories):
        self.data.categories = categories
        self.data.sort(lambda x: entries.index(x.nid) if x.nid in entries else -1)

    def delete_from_db(self, nid):
        self.data.remove_key(nid)
        return True

    def create_new(self, nid):
        if self.data.get(nid):
            QMessageBox.warning(self, 'Warning', 'ID %s already in use' % nid)
            return False
        new_item = items.ItemPrefab(nid, nid, '')
        self.data.append(new_item)
        return True

    def duplicate(self, old_nid, nid):
        if self.data.get(nid):
            QMessageBox.warning(self, 'Warning', 'ID %s already in use' % nid)
            return False
        orig_item = self.data.get(old_nid)
        if not orig_item:
            QMessageBox.warning(self, 'Warning', 'ID %s not found' % old_nid)
            return False
        new_item = ItemPrefab.restore(orig_item.save())
        new_item.nid = nid
        self.data.append(new_item)
        return True

    def copy_to_clipboard(self):
        selected_nid = self.tree_list.get_selected_item()
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
            self.reset()
            if any_nid:
                self.tree_list.select_item(any_nid)
        except Exception as e:
            logging.warning("Could not read from clipboard! %s" % e)
            QMessageBox.critical(self, "Import Error", "Could not read valid json from clipboard!")

    def import_csv(self):
        settings = MainSettingsController()
        starting_path = settings.get_last_open_path()
        fn, ok = QFileDialog.getOpenFileName(self, "Import items from csv", starting_path, "items csv (*.csv);;All Files(*)")
        if ok and fn:
            parent_dir = os.path.split(fn)[0]
            settings.set_last_open_path(parent_dir)
            item_import.update_db_from_csv(self._db, fn)
            self.reset()


    # @todo(mag) fix the unit tab (which is the only time this callback is used forcibly in data_editor.py) and remove this
    def on_tab_close(self):
        pass

    @classmethod
    def create(cls, parent=None, db=None):
        db = db or DB
        return cls(parent, db)

    @classmethod
    def edit(cls, parent=None):
        timer.get_timer().stop_for_editor()  # Don't need these while running game
        window = SingleDatabaseEditor(NewItemDatabase, parent)
        window.exec_()
        timer.get_timer().start_for_editor()

# Testing
# Run "python -m app.editor.item_editor.new_item_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.data.resources.resources import RESOURCES
    DB.load('default.ltproj')
    RESOURCES.load('default.ltproj')
    window = NewItemDatabase(None, DB)
    window.show()
    app.exec_()
