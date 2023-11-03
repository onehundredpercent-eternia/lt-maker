from __future__ import annotations

import os
from typing import Optional

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QFileDialog)

from app.data.database.units import UnitCatalog, UnitPrefab
from app.editor import timer
from app.editor.data_editor import SingleDatabaseEditor
from app.editor.unit_editor import unit_import, unit_model, unit_properties
from app.editor.component_editor_properties import NewComponentProperties
from app.editor.settings.main_settings_controller import MainSettingsController
from app.editor.component_object_editor import ComponentObjectEditor

class NewUnitProperties(unit_properties.UnitProperties):
    title = "Unit"
    # get_components = staticmethod(ICA.get_Unit_components)
    # get_templates = staticmethod(ICA.get_templates)
    # get_tags = staticmethod(ICA.get_Unit_tags)


class NewUnitDatabase(ComponentObjectEditor):
    catalog_type = UnitCatalog
    properties_type = NewUnitProperties

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