from pathlib import Path
from typing import List, TypeVar
from app.data.serialization.command import SCommand, SerializeCommand
from app.data.serialization.serialization_options import SerializeOptions
from app.data.serialization.serializer import Serializer
from app.utilities.data import Data

T = TypeVar('T', bound=Data)

class ObjectCanSaveSerializer(Serializer):
    def serialize_catalog(self, catalog: Data, catalog_name: str, options: SerializeOptions) -> List[SerializeCommand]:
        if options.as_chunks:
            as_list = catalog.save()
            commands = []
            for obj in as_list:
                path_to_obj = Path(catalog_name) / obj['nid']
                commands.append(SerializeCommand(path_to_obj, obj, SCommand.WRITE))
        else:
            as_list = catalog.save()
            return [SerializeCommand(catalog_name, as_list, SCommand.WRITE)]

    def deserialize_catalog(self, catalog_type: T, catalog_name: str, options: SerializeOptions) -> T:
        pass