import json
from pathlib import Path
import re
from typing import List, TypeVar
from app.data.category import CategorizedCatalog
from app.data.serialization.command import SCommand, SerializeCommand
from app.data.serialization.json_utils import to_json
from app.data.serialization.serialization_options import SerializeOptions
from app.data.serialization.serializer import Serializer
from app.utilities.data import Data

T = TypeVar('T', bound=Data)

class ObjectCanSaveSerializer(Serializer):
    def serialize_catalog(self, catalog: Data, catalog_name: str, options: SerializeOptions) -> List[SerializeCommand]:
        commands = []
        if isinstance(catalog, CategorizedCatalog):
            category_list = catalog.categories.save()
            commands.append(SerializeCommand(Path(catalog_name + ".category.json"), to_json(category_list), SCommand.WRITE))
        if options.as_chunks:
            as_list = catalog.save()
            orderkeys = []
            for obj in as_list:
                name = obj['nid']
                name = re.sub(r'[\\/*?:"<>|]', "", name)
                name = name.replace(' ', '_')
                path_to_obj = Path(catalog_name) / (name + ".json")
                # need to wrap this in a list because we expect this to be in list format due to legacy reasons
                commands.append(SerializeCommand(path_to_obj, to_json([obj]), SCommand.WRITE))
                orderkeys.append(name)
            commands.append(SerializeCommand(Path(catalog_name) / ".orderkeys", to_json(orderkeys), SCommand.WRITE))
        else:
            as_list = catalog.save()
            commands.append(SerializeCommand(catalog_name + ".json", to_json(as_list), SCommand.WRITE))
        return commands

    def deserialize_catalog(self, catalog_type: T, catalog_name: str, options: SerializeOptions) -> T:
        pass