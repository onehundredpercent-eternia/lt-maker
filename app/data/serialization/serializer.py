from abc import ABC, abstractmethod
from app.utilities.data import Data
from app.utilities.typing import NestedPrimitiveDict

class Serializer(ABC):
    @abstractmethod
    def serialize_catalog(self, catalog: Data, catalog_name: str) -> NestedPrimitiveDict:
        pass