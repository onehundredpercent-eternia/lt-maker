from typing import List
from app.data.serialization.migrators.migrator_base import MigratorBase
from app.utilities.typing import NestedPrimitiveDict

class MigratorV0_V1(MigratorBase):
    def migrate_database(self, db_dict: NestedPrimitiveDict):
        # migrated wexp gain to be a dataclass dict
        for unit in db_dict.get("units", []):
            new_wexp_gain = {}
            for wexp_gain_nid, wexp_gain_tuple in unit.get('wexp_gain', {}).items():
                new_wexp_gain[wexp_gain_nid] = {
                    'usable': bool(wexp_gain_tuple[0]),
                    'wexp_gain': wexp_gain_tuple[1],
                    'cap': wexp_gain_tuple[2]
                }
            unit['wexp_gain'] = new_wexp_gain
        for klass in db_dict.get('classes', []):
            new_wexp_gain = {}
            for wexp_gain_nid, wexp_gain_tuple in klass.get('wexp_gain', {}).items():
                new_wexp_gain[wexp_gain_nid] = {
                    'usable': bool(wexp_gain_tuple[0]),
                    'wexp_gain': wexp_gain_tuple[1],
                    'cap': wexp_gain_tuple[2]
                }
            klass['wexp_gain'] = new_wexp_gain
        return db_dict

    def migrate_resources(self, resource_dict: NestedPrimitiveDict):
        # migrate fonts - they were formerly sometimes saved as 3-tuples, but must be loaded as 4-tuples as that's the official spec
        fonts: List[NestedPrimitiveDict] = resource_dict.get('fonts', [])
        for font in fonts:
            for color_name, palette in font.get('palettes', {}).items(): # palettes are a list of Color4s
                for rgba in palette: # rgba is, ideally, a Color4 (4-list), but sometimes it's a Color3 (3-list)
                    if len(rgba) == 3:
                        rgba.append(255)
        return resource_dict