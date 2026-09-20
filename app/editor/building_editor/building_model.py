from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB

from app.extensions.custom_gui import DeletionTab, DeletionDialog
from app.editor.base_database_gui import DragDropCollectionModel
from app.editor.custom_widgets import BuildingBox
from app.data.database import building_components
from app.data.database.components import ComponentType, swap_values

def get_pixmap(building):
    """The building's map sprite in its reference colors.

    Deliberately unrecolored: the building list has no map style or owning team
    to recolor against. See `map_view.get_building_pixmap` for the painted map.
    """
    if not building:  # e.g. nid already deleted from the catalog
        return None
    res = RESOURCES.building_sprites.get(building.map_sprite_nid)
    if not res or not res.full_path:
        return None
    pixmap = res.get_pixmap()
    if not pixmap or pixmap.isNull():
        return None
    return pixmap

class BuildingModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            building = self._data[index.row()]
            text = building.nid
            return text
        elif role == Qt.DecorationRole:
            building = self._data[index.row()]
            pix = get_pixmap(building)
            if pix:
                pix = pix.scaled(32, 32)
                return QIcon(pix)
        return None

    def delete(self, idx):
        # Check to make sure nothing else is using me!!!
        building = self._data[idx]
        if len(self._data) > 1:  # So we have something to swap to
            nid = building.nid
            affected_buildings = building_components.get_buildings_using(ComponentType.Building, nid, DB)
            
            deletion_tabs = []
            if affected_buildings:
                model = BuildingModel
                msg = "Deleting Building <b>%s</b> would affect these buildings" % nid
                deletion_tabs.append(DeletionTab(affected_buildings, model, msg, "Buildings"))

            if deletion_tabs:
                swap, ok = DeletionDialog.get_swap(deletion_tabs, BuildingBox(self.window, exclude=building), self.window)
                if ok:
                    self.on_nid_changed(swap.nid, nid)
                else:
                    return
        # Delete watchers
        super().delete(idx)

    def on_nid_changed(self, old_nid, new_nid):
        swap_values(DB.buildings.values(), ComponentType.Building, old_nid, new_nid)
        swap_values(DB.techs.values(), ComponentType.Building, old_nid, new_nid)

    def create_new(self):
        new_building = DB.buildings.create_new(DB)
        return new_building
