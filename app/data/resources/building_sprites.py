from pathlib import Path
from typing import List, Optional
from typing_extensions import override

from app.data.category import CategorizedCatalog
from app.data.resources.base_catalog import ManifestCatalog
from app.data.resources.resource_prefab import WithResources
from app.utilities.data import Prefab


class BuildingSprite(WithResources, Prefab):
    """A single flat map sprite for a building.

    The image is authored in the project's `building_ref` reference ramp: the
    first 13 non-colorkey colors vary with the tilemap's building style, the
    last 2 vary with the owning team. See `app/engine/building_sprite.py`.

    The image is a whole number of tiles wide and tall, but the gameplay
    footprint lives on `BuildingPrefab.size`, not here.
    """

    def __init__(self, nid, full_path=None):
        self.nid = nid
        self.full_path = full_path
        self.image = None
        self.pixmap = None

    @override
    def set_full_path(self, full_path):
        self.full_path = full_path

    @override
    def used_resources(self) -> List[Optional[Path]]:
        return [Path(self.full_path)]

    def get_pixmap(self):
        from PyQt5.QtGui import QPixmap
        if not self.pixmap:
            self.pixmap = QPixmap(self.full_path)
        return self.pixmap

    def save(self):
        return self.nid

    @classmethod
    def restore(cls, nid):
        return cls(nid)


class BuildingSpriteCatalog(ManifestCatalog[BuildingSprite], CategorizedCatalog[BuildingSprite]):
    manifest = 'building_sprites.json'
    title = 'building sprites'
    datatype = BuildingSprite
