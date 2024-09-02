from app.data.category import CategorizedCatalog
from app.data.serialization.serializer import Serializer
from app.utilities.data import Data
from app.utilities.typing import NestedPrimitiveDict

class ObjectCanSaveSerializer(Serializer):
    def serialize_catalog(self, catalog: Data, catalog_name: str) -> NestedPrimitiveDict:
        s_dict: NestedPrimitiveDict = {}
        s_dict[catalog_name] = catalog.save()
        if isinstance(catalog, CategorizedCatalog):
            s_dict[catalog_name + '.category'] = catalog.categories.save()
        return s_dict