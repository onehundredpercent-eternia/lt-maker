from typing import List
from app.data.serialization.migrators.migrator_base import MigratorBase
from app.utilities.typing import NestedPrimitiveDict

class MigratorV0_V1(MigratorBase):
    def migrate_database(self, db_dict: NestedPrimitiveDict):
        return db_dict

    def migrate_resources(self, resource_dict: NestedPrimitiveDict):
        # migrate fonts - they were formerly sometimes saved as 3-tuples, but must be loaded as 4-tuples as that's the official spec
        fonts: List[NestedPrimitiveDict] = resource_dict.get('fonts', [])
        for font in fonts:
            for color_name, palette in font.get('palettes', {}).items():
                for rgba in palette:
                    if len(rgba) == 3:
                        rgba.append(255)
        return resource_dict