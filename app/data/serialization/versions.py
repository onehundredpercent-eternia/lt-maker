from typing import Dict, Type

from app.data.serialization.serializer import Serializer
from app.data.serialization.type_0_serializer import ObjectCanSaveSerializer

CURRENT_GLOBAL_SERIALIZATION_VERSION = 0

SERIALIZATION_VERSION_MAP: Dict[int, Type[Serializer]] = {
    CURRENT_GLOBAL_SERIALIZATION_VERSION: ObjectCanSaveSerializer
}
