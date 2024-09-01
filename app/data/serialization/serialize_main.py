from __future__ import annotations
from pathlib import Path
from typing import List, TypeVar
from app.data.serialization.command import SerializeCommand
from app.data.serialization.serialization_options import SerializeOptions
from app.data.serialization.serializer import Serializer
from app.data.serialization.versions import SERIALIZATION_VERSION_MAP
from app.utilities.data import Data

T = TypeVar('T', bound=Data)

class SerializerController():
    root_dir: Path
    serializer: Serializer

    def __init__(self, root_dir: Path, version: int):
        self.root_dir = root_dir
        self.serializer = SERIALIZATION_VERSION_MAP.get(version)()

    def serialize_catalog(self, catalog: Data, catalog_name: str, options: SerializeOptions) -> List[SerializeCommand]:
        self.serializer.serialize_catalog(catalog, catalog_name)

    def deserialize_catalog(self, catalog_type: T, catalog_name: str, options: SerializeOptions) -> T:
        self.serializer.deserialize_catalog(catalog_type, catalog_name)