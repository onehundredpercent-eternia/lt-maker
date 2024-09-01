from typing import Dict

from app.data.serialization.type_0_serializer import ObjectCanSaveSerializer

CURRENT_GLOBAL_SERIALIZATION_VERSION = 0

SERIALIZATION_VERSION_MAP: Dict[int, type] = {
    CURRENT_GLOBAL_SERIALIZATION_VERSION: ObjectCanSaveSerializer
}