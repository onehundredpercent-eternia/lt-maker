from __future__ import annotations

from typing import Optional

from PyQt5.QtGui import QIcon

import app.engine.skill_component_access as BCA
from app.data.database.buildings import BuildingCatalog, BuildingPrefab
from app.data.database import building_components
from app.data.database.components import swap_values, ComponentType
from app.editor import timer
from app.editor.new_editor_tab import NewEditorTab
from app.editor.data_editor import SingleDatabaseEditor
from app.editor.component_editor_properties import NewComponentProperties
from app.editor.building_editor import building_model
from app.extensions.custom_gui import DeletionTab, DeletionDialog
from app.editor.custom_widgets import BuildingBox

from app.utilities.typing import NID


class NewBuildingProperties(NewComponentProperties[BuildingPrefab]):
    title = "Building"
    get_components = staticmethod(BCA.get_building_components)
    get_templates = staticmethod(BCA.get_templates)
    get_tags = staticmethod(BCA.get_building_tags)


class NewBuildingDatabase(NewEditorTab):
    catalog_type = BuildingCatalog
    properties_type = NewBuildingProperties

    @classmethod
    def edit(cls, parent=None):
        timer.get_timer().stop_for_editor()  # Don't need these while running game
        window = SingleDatabaseEditor(NewBuildingDatabase, parent)
        window.exec_()
        timer.get_timer().start_for_editor()

    @property
    def data(self):
        return self._db.buildings

    def get_icon(self, building_nid) -> Optional[QIcon]:
        pix = building_model.get_pixmap(self.data.get(building_nid))
        if pix:
            return QIcon(pix.scaled(32, 32))
        return None

    def _on_delete(self, nid: NID) -> bool:
        """
        Returns whether the user wants to proceed with deletion
        """
        building = self.data.get(nid)
        affected_buildings = building_components.get_buildings_using(ComponentType.Building, nid, self._db)

        deletion_tabs = []
        if affected_buildings:
            from app.editor.building_editor.building_model import BuildingModel
            model = BuildingModel
            msg = "Deleting Building <b>%s</b> would affect these buildings" % nid
            deletion_tabs.append(DeletionTab(affected_buildings, model, msg, "Skills"))

        if deletion_tabs:
            swap, ok = DeletionDialog.get_swap(deletion_tabs, BuildingBox(self, exclude=building), self)
            if ok:
                self._on_nid_changed(nid, swap.nid)
            else:
                return False
        return True

    def _on_nid_changed(self, old_nid: NID, new_nid: NID) -> None:
        swap_values(self._db.buildings.values(), ComponentType.Building, old_nid, new_nid)

# Testing
# Run "python -m app.editor.skill_editor.new_skill_tab" from main directory
if __name__ == '__main__':
    import sys
    from app.data.database.database import DB
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.data.resources.resources import RESOURCES
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
    DB.load('default.ltproj', CURRENT_SERIALIZATION_VERSION)
    RESOURCES.load('default.ltproj', CURRENT_SERIALIZATION_VERSION)
    window = NewBuildingDatabase(None, DB)
    window.show()
    app.exec_()
