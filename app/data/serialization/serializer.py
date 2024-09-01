from abc import ABC, abstractmethod
from typing import List, TypeVar

from app.data.serialization.command import SerializeCommand
from app.data.serialization.serialization_options import SerializeOptions
from app.utilities.data import Data

T = TypeVar('T', bound=Data)

class Serializer(ABC):
    @abstractmethod
    def serialize_catalog(self, catalog: Data, catalog_name: str, options: SerializeOptions) -> List[SerializeCommand]:
        pass

    @abstractmethod
    def deserialize_catalog(self, catalog_type: T, catalog_name: str, options: SerializeOptions) -> T:
        pass