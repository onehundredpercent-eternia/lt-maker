from __future__ import annotations

from typing import TYPE_CHECKING, Type

from app.data.resources.base_catalog import ManifestCatalog

if TYPE_CHECKING:
    from app.map_maker.map_prefab import MapPrefab


class MapPrefabCatalog(ManifestCatalog['MapPrefab']):
    manifest = 'map_prefabs.json'
    title = 'map_prefabs'

    @property
    def datatype(self) -> Type['MapPrefab']:
        from app.map_maker.map_prefab import MapPrefab
        return MapPrefab
