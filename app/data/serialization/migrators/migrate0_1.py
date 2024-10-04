from app.data.serialization.migrators.migrator_base import MigratorBase
from app.utilities.typing import NestedPrimitiveDict

class MigratorV0_V1(MigratorBase):
    def migrate_database(self, db_dict: NestedPrimitiveDict):
        return db_dict

    def migrate_resources(self, resource_dict: NestedPrimitiveDict):
        return resource_dict