from pathlib import Path

from PyQt5.QtGui import QIcon, QPainter, QPixmap

from app.data.database.database import Database
from app.data.resources.icons import IconCatalog, IconSheet
from app.data.resources.resources import Resources
from app.editor.icon_editor.icon_view import icon_slice
from app.editor.settings.main_settings_controller import MainSettingsController
from app.utilities.data import Data


def maybe_migrate_db_and_resources(r: Resources, db: Database, settings: MainSettingsController):
    def unify_icon_sheet(name: str, catalog: IconCatalog):
        icons = catalog
        loc = Path(settings.get_current_project()) / 'resources' / name
        # import from old version
        def num_icons(sheet: IconSheet):
            if not sheet.pixmap:
                sheet.pixmap = QPixmap(sheet.full_path)
            return sheet.pixmap.width() * sheet.pixmap.height() / sheet.size[0] / sheet.size[1]
        unified_catalog = icons.datatype("__icons", (Path(loc) / "__icons.png").__str__())
        n_icons = sum([num_icons(sheet) for sheet in icons])
        pwidth = int(640 / icons.datatype.size[0])
        pheight = n_icons // pwidth + 1
        new_pixmap = QPixmap(pwidth * icons.datatype.size[0], pheight * icons.datatype.size[1])
        x, y = 0, 0
        with QPainter(new_pixmap) as painter:
            for sheet in icons:
                for icon in icon_slice(sheet, sheet.size[0], sheet.size[1]):
                    painter.drawPixmap(x * icons.datatype.size[0], y * icons.datatype.size[1], icon.pixmap)
                    new_alias = sheet.get_alias(icon.icon_index)
                    unified_catalog.set_alias(new_alias, (x, y))
                    unified_catalog._categories[new_alias] = sheet.nid
                    x += 1
                    if x == pwidth:
                        x = 0
                        y += 1
        new_pixmap.save((Path(loc) / '__icons.png').__str__())
        return unified_catalog

    def update_icon_indices(catalog: Data, unified_catalog: IconCatalog, original_catalog: IconCatalog):
        for obj in catalog:
            nid = obj.icon_nid
            index = obj.icon_index
            if nid:
                new_index = unified_catalog.get_index(original_catalog.get(nid).get_alias(index))
                obj.icon_index = new_index
                obj.icon_nid = '__icons'

    unified_icon16 = unify_icon_sheet('icons16', r.icons16)
    unified_icon32 = unify_icon_sheet('icons32', r.icons32)
    unified_icon80 = unify_icon_sheet('icons80', r.icons80)
    update_icon_indices(db.items, unified_icon16, r.icons16)
    update_icon_indices(db.affinities, unified_icon16, r.icons16)
    update_icon_indices(db.factions, unified_icon32, r.icons32)
    update_icon_indices(db.skills, unified_icon16, r.icons16)
    update_icon_indices(db.classes, unified_icon80, r.icons80)
    update_icon_indices(db.weapons, unified_icon16, r.icons16)
    r.icons16.clear()
    r.icons16.append(unified_icon16)
    r.icons32.clear()
    r.icons32.append(unified_icon32)
    r.icons80.clear()
    r.icons80.append(unified_icon80)