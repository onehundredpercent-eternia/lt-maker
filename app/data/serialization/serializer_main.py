from __future__ import annotations
from typing import List, TypeVar
from app.data.serialization.serializer import Serializer
from app.data.serialization.versions import SERIALIZATION_VERSION_MAP
from app.utilities.data import Data
from app.utilities.typing import NestedPrimitiveDict

T = TypeVar('T', bound=Data)

class SerializerController(Serializer):
    serializer: Serializer

    def __init__(self, version: int):
        self.serializer = SERIALIZATION_VERSION_MAP.get(version)()

    def serialize_catalog(self, catalog: Data, catalog_name: str) -> NestedPrimitiveDict:
        return self.serializer.serialize_catalog(catalog, catalog_name)