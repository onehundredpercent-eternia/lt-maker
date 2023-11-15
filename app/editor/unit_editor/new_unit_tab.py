from __future__ import annotations

import json
import logging
import os
from typing import Dict, Generic, List, Optional, Type, TypeVar

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QDialog, QFileDialog, QGridLayout, QHBoxLayout,
                             QMessageBox, QPushButton, QSplitter, QVBoxLayout,
                             QWidget)

from app.data.category import Categories
from app.data.database.database import DB, Database
from app.data.database.level_units import UniqueUnit
from app.data.database.units import UnitCatalog, UnitPrefab
from app.editor import timer
from app.editor.data_editor import SingleDatabaseEditor
from app.editor.lib.components.nested_list import LTNestedList
from app.editor.unit_editor import unit_import, unit_model, new_unit_properties
from app.editor.settings.main_settings_controller import MainSettingsController
from app.editor.component_object_editor import ComponentObjectEditor
from app.utilities import str_utils
from app.utilities.data import Data
from app.utilities.typing import NID

class NewUnitProperties(new_unit_properties.NewUnitProperties):
    title = "Unit"
    # get_components = staticmethod(ICA.get_Unit_components)
    # get_templates = staticmethod(ICA.get_templates)
    # get_tags = staticmethod(ICA.get_Unit_tags)


class NewUnitDatabase(QWidget):
    catalog_type = UnitCatalog
    properties_type = NewUnitProperties

    def __init__(self, parent, database: Database) -> None:
        QWidget.__init__(self, parent)
        self._db = database
        self.categories = self.data.categories

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
        self.right_frame = self.properties_type(self, None, self.attempt_change_nid,
                                                lambda: self.tree_list.regenerate_icons(initial_generation=True))
        self.splitter = QSplitter(self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.left_frame)
        self.splitter.addWidget(self.right_frame)
        self.splitter.setStyleSheet(
            "QSplitter::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc); border: 1px solid #777; width: 13px; margin-top: 2px; margin-bottom: 2px; border-radius: 4px;}")

        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)

        self._layout.addWidget(self.splitter)


    @classmethod
    def edit(cls, parent=None):
        timer.get_timer().stop_for_editor()  # Don't need these while running game
        window = SingleDatabaseEditor(NewUnitDatabase, parent)
        window.exec_()
        timer.get_timer().start_for_editor()

    @property
    def data(self):
        return self._db.units

    def get_icon(self, unit_nid) -> Optional[QIcon]:
        if not self.data.get(unit_nid):
            return None
        pix = unit_model.get_chibi(self.data.get(unit_nid))
        if pix:
            return QIcon(pix.scaled(32, 32))
        return None

    def import_xml(self):
        settings = MainSettingsController()
        starting_path = settings.get_last_open_path()
        fn, ok = QFileDialog.getOpenFileName(self, _("Import Units from units.xml"), starting_path, "Units XML (units.xml);;All Files(*)")
        if ok and fn.endswith('units.xml'):
            parent_dir = os.path.split(fn)[0]
            settings.set_last_open_path(parent_dir)
            new_units = unit_import.get_from_xml(parent_dir, fn)
            for unit in new_units:
                self.data.append(unit)
            self.reset()

    def import_csv(self):
        settings = MainSettingsController()
        starting_path = settings.get_last_open_path()
        fn, ok = QFileDialog.getOpenFileName(self, _("Import Units from csv"), starting_path, "units csv (*.csv);;All Files(*)")
        if ok and fn:
            parent_dir = os.path.split(fn)[0]
            settings.set_last_open_path(parent_dir)
            unit_import.update_db_from_csv(self._db, fn)
            self.reset()

    def reset(self):
        self.tree_list.reset(self.data.keys(), self.categories)

    def attempt_change_nid(self, old_nid: NID, new_nid: NID) -> bool:
        if not new_nid:
            return False
        if old_nid == new_nid:
            return True
        if self.data.get(new_nid):
            QMessageBox.warning(self, 'Warning', 'ID %s already in use' % new_nid)
            return False
        self.data.change_key(old_nid, new_nid)
        self.tree_list.update_nid(old_nid, new_nid)
        self.tree_list.on_filter_changed(self.tree_list.search_box.text())
        self.on_nid_changed(old_nid, new_nid)
        return True

    def on_nid_changed(self, old_nid, new_nid):
        for ai in DB.ai:
            ai.change_unit_spec("ID", old_nid, new_nid)
        for level in DB.levels:
            for unit in level.units:
                if isinstance(unit, UniqueUnit) and unit.nid == old_nid:
                    level.units.update_nid(unit, new_nid)
            for unit_group in level.unit_groups:
                unit_group.swap(old_nid, new_nid)
            for unit in level.units:
                if old_nid and unit.starting_traveler == old_nid:
                    unit.starting_traveler = new_nid
        for party in DB.parties:
            if party.leader == old_nid:
                party.leader = new_nid

    def on_select(self, entry_nid: Optional[NID]):
        if not entry_nid:
            self.right_frame.set_current(None)
            return
        curr_entry = self.data.get(entry_nid)
        if curr_entry:
            self.right_frame.set_current(curr_entry)

    def resort_db(self, entries: List[str], categories: Categories):
        self.data.categories = categories
        self.data.sort(lambda x: entries.index(x.nid) if x.nid in entries else -1)

    def delete_from_db(self, nid):
        if len(self.data) == 1:
            # We must always have at least one unit in the database.
            return False
        unit = self.data.get(nid)
        affected = None
        affected_ais = [ai for ai in DB.ai if ai.has_unit_spec("ID", nid)]
        affected_levels = [level for level in DB.levels if
                           any(isinstance(unit, UniqueUnit) and unit.nid == nid for unit in level.units)]
        if affected_ais:
            affected = Data(affected_ais)
            from app.editor.ai_editor.ai_model import AIModel
            model = AIModel
        elif affected_levels:
            affected = Data(affected_levels)
            from app.editor.global_editor.level_menu import LevelModel
            model = LevelModel
        if affected:
            msg = "Deleting Unit <b>%s</b> would affect these objects" % nid
            from app.extensions.custom_gui import DeletionDialog
            ok = DeletionDialog.inform(affected, model, msg, self.window())
            if ok:
                self.on_delete(nid)
            else:
                return False
        self.data.remove_key(nid)
        return True

    def on_delete(self, old_nid):
        new_nid = None
        for unit in DB.units:
            if unit.nid != old_nid:
                new_nid = unit.nid
                break
        for ai in DB.ai:
            ai.change_unit_spec("ID", old_nid, new_nid)
        for level in DB.levels:
            if old_nid in level.units.keys():
                level.units.remove_key(old_nid)
            for unit_group in level.unit_groups:
                unit_group.remove(old_nid)
            for unit in level.units:
                if unit.starting_traveler == old_nid:
                    unit.starting_traveler = None
        for party in DB.parties:
            if party.leader == old_nid:
                party.leader = new_nid

    def create_new(self, nid):
        if self.data.get(nid):
            QMessageBox.warning(self, 'Warning', 'ID %s already in use' % nid)
            return False
        new_obj = self.catalog_type.datatype(nid, nid, '')
        self.data.append(new_obj)
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
            self.reset()
            if any_nid:
                self.tree_list.select_item(any_nid)
        except Exception as e:
            logging.warning("Could not read from clipboard! %s" % e)
            QMessageBox.critical(self, "Import Error", "Could not read valid json from clipboard!")

    def on_tab_close(self):
        # Checking to see if any levels need to be changed
        for level in DB.levels:
            for unit in level.units.values():
                if unit.generic or unit.nid in DB.units.keys():
                    pass
                else:  # Remove any unit that no longer exist
                    level.units.remove_key(unit.nid)
            # Now remove groups
            for unit_group in level.unit_groups:
                for unit_nid in unit_group.units:
                    if unit_nid not in level.units.keys():
                        unit_group.remove(unit_nid)

    @classmethod
    def create(cls, parent=None, db=None):
        db = db or DB
        return cls(parent, db)

def get(unit_nid=None):
    window = NewUnitDatabase(None, DB)
    unit = DB.units.get(unit_nid)
    if unit:
        window.on_select(unit_nid)
    try:
        NewUnitDatabase.edit()
        result = True
    except Exception as err:
        logging.warning(f"Failed to open Unit Window due to {err}")
        result = False
    if result:
        selected_unit = window.right_frame.current
        return selected_unit, True
    else:
        return None, False

# Testing
# Run "python -m app.editor.unit_editor.new_unit_tab" from main directory
if __name__ == '__main__':
    import sys
    from app.data.database.database import DB
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.data.resources.resources import RESOURCES
    DB.load('default.ltproj')
    RESOURCES.load('default.ltproj')
    window = NewUnitDatabase(None, DB)
    window.show()
    app.exec_()