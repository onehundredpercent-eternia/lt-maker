from __future__ import annotations

from typing import Dict, List, Optional

from app.utilities.typing import NID, Pos
from app.utilities.data import Data

from app.constants import TILEWIDTH, TILEHEIGHT, AUTOTILE_FRAMES

from app.data.database.database import DB

from app.map_maker.map_prefab import MapPrefab
from app.map_maker.terrain import Terrain
from app.map_maker.palette_collection import PALETTES, PaletteCollection
from app.map_maker.painter_database import create_painters
from app.map_maker.pygame_renderers import SimpleRenderer
from app.map_maker.pygame_renderers.renderer_database import create_renderers
from app.map_maker.pygame_renderers.draw_tilemap import process_dirty_positions

from app.engine import engine
from app.engine.objects.tilemap import TileMapObject, LayerObject


def _resolve_palette(collection: Data[PaletteCollection], nid: Optional[NID]) -> PaletteCollection:
    """project override -> the requested nid if it still exists -> index 0"""
    if nid:
        found = collection.get(nid)
        if found is not None:
            return found
    return collection[0]


def _build_renderers(prefab: MapPrefab) -> Dict[Terrain, SimpleRenderer]:
    """Renderers (and their painters) built fresh for this one prefab.

    Deliberately does NOT use the process-wide PAINTERS/RENDERERS singletons
    -- see the painter-singleton discussion in map_prefab_engine_plan.md
    Phase 3. Giving each MapPrefabTileMapObject its own painters means engine
    rendering can never mutate state (e.g. MountainPainter.gui_processing,
    or its mountain_process_finished/mountain_processing callbacks) that the
    Qt map_maker editor's own renderers/painters depend on, regardless of
    process/import ordering."""
    outdoor_palette = _resolve_palette(PALETTES.outdoor_palettes(), prefab.current_outdoor_palette)
    indoor_palette = _resolve_palette(PALETTES.indoor_palettes(), prefab.current_indoor_palette)
    return create_renderers(outdoor_palette, indoor_palette, painters=create_painters())


class MapPrefabTileMapObject(TileMapObject):
    """A TileMapObject backed by a live app.map_maker.map_prefab.MapPrefab,
    rendered through the pygame_renderers painter/renderer pipeline instead
    of tileset resources.

    Rendered once at construction time and baked into a single 'base'
    LayerObject (base image + AUTOTILE_FRAMES autotile overlay images), so
    per-frame cost is identical to a normal TileMapObject (cull + blit).
    Runtime terrain edits (change_terrain) re-run the painters only on the
    positions MapPrefab marks dirty and patch the cached surfaces in place.
    """

    def __init__(self) -> None:
        super().__init__()
        # Always populated by from_prefab()/restore() before use -- mirrors
        # TileMapObject's own `self.nid: NID = None` convention for
        # attributes that a bare __init__() leaves temporarily unset.
        self.prefab: MapPrefab = None  # type: ignore[assignment]
        self.renderers: Dict[Terrain, SimpleRenderer] = {}

    @classmethod
    def from_prefab(cls, prefab: MapPrefab) -> MapPrefabTileMapObject:
        self = cls()
        # Deep copy of clean data only (no Surface copying) -- runtime edits
        # must never mutate the RESOURCES-owned prefab.
        self.prefab = MapPrefab.restore(prefab.save())
        self.prefab.reset_all()

        self.nid = self.prefab.nid
        self.width = self.prefab.width
        self.height = self.prefab.height
        self.autotile_fps = self.prefab.autotile_fps
        self.layers = Data()

        self.renderers = _build_renderers(self.prefab)

        process_dirty_positions(self.prefab, self.renderers, autotile_num=0)
        self.prefab.terrain_grid_to_update.clear()

        layer = LayerObject('base', False, self)
        layer.visible = True
        map_size = (self.width * TILEWIDTH, self.height * TILEHEIGHT)
        layer.image = engine.create_surface(map_size, transparent=True)
        layer.pixel_bounds = [0, 0, map_size[0], map_size[1]]

        for pos, sprite in self.prefab.tile_grid.items():
            if pos not in self.prefab.autotile_set:
                layer.image.blit(sprite, (pos[0] * TILEWIDTH, pos[1] * TILEHEIGHT))

        if self.prefab.autotile_set:
            layer.autotile_images = [
                engine.create_surface(map_size, transparent=True)
                for _ in range(AUTOTILE_FRAMES)
            ]
            for pos in self.prefab.autotile_set:
                self._blit_autotile_frames(layer, pos)

        self.layers.append(layer)

        self.weather = []
        self.animations = []
        self.high_animations = []
        return self

    def _blit_autotile_frames(self, layer: LayerObject, pos: Pos) -> None:
        terrain = self.prefab.get_terrain(pos)
        if terrain is None:
            return
        renderer = self.renderers.get(terrain)
        if renderer is None:
            return
        px = (pos[0] * TILEWIDTH, pos[1] * TILEHEIGHT)
        for frame in range(AUTOTILE_FRAMES):
            sprite = renderer.determine_sprite(self.prefab, pos, frame)
            layer.autotile_images[frame].blit(sprite, px)

    def get_terrain(self, pos: Pos) -> NID:
        terrain = self.prefab.terrain_grid.get(pos)
        if terrain is None:
            return '0'
        return DB.map_terrain_associations.get(terrain)

    def get_layer(self, pos: Pos) -> Optional[NID]:
        if pos in self.prefab.terrain_grid:
            return 'base'
        return None

    def change_terrain(self, pos: Pos, terrain: Optional[Terrain]) -> None:
        """Runtime terrain edit: re-paints only the positions MapPrefab
        marks dirty (the changed tile plus any neighbors whose sprite
        depends on it -- edges, flood-filled blobs, etc.) and patches the
        cached base/autotile surfaces in place. Mountain/sea/cliff flood-fill
        groups redo their whole blob; the mountain re-solve is synchronous,
        which is fine for infrequent runtime changes but could hitch for a
        large connected mountain range."""
        layer = self.layers.get('base')
        old_terrain = self.prefab.get_terrain(pos)
        if terrain is None:
            self.prefab.erase_terrain(pos, old_terrain)
        else:
            self.prefab.set(pos, old_terrain, terrain)

        # Snapshot before process_dirty_positions's caller (us) clears it --
        # these are exactly the positions that got a new tile_grid sprite
        # (or, for erased positions, need their old sprite removed).
        # NOTE: MapPrefab.erase_terrain deliberately does NOT add `pos`
        # itself to terrain_grid_to_update (nothing to paint there anymore)
        # -- but we still need to clear its old sprite from our baked
        # surfaces, so it must always be included here regardless.
        dirty_positions: List[Pos] = list(self.prefab.terrain_grid_to_update | {pos})
        process_dirty_positions(self.prefab, self.renderers, autotile_num=0)
        self.prefab.terrain_grid_to_update.clear()

        map_size = (self.width * TILEWIDTH, self.height * TILEHEIGHT)
        for p in dirty_positions:
            rect = (p[0] * TILEWIDTH, p[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
            engine.fill(layer.image, (0, 0, 0, 0), rect)
            for autotile_image in layer.autotile_images:
                engine.fill(autotile_image, (0, 0, 0, 0), rect)

            p_terrain = self.prefab.get_terrain(p)
            if p_terrain is None:
                continue  # Erased -- leave the now-cleared rect blank

            if p in self.prefab.autotile_set:
                if not layer.autotile_images:
                    # First autotile position this map has ever had
                    layer.autotile_images = [
                        engine.create_surface(map_size, transparent=True)
                        for _ in range(AUTOTILE_FRAMES)
                    ]
                self._blit_autotile_frames(layer, p)
            else:
                sprite = self.prefab.tile_grid.get(p)
                if sprite is not None:
                    layer.image.blit(sprite, (p[0] * TILEWIDTH, p[1] * TILEHEIGHT))

        if not self.prefab.autotile_set and layer.autotile_images:
            # Last autotile position removed -- drop the (now fully
            # transparent) overlay surfaces so per-frame draw skips them.
            layer.autotile_images = []

    def save(self) -> dict:
        s_dict = super().save()
        # Authoritative for restore: carries the *current* (possibly
        # runtime-modified) terrain grid, autotile_set, seed and palettes --
        # not just the resource nid. This is what makes suspend/load and
        # turnwheel game-over restore keep runtime terrain edits.
        s_dict['prefab'] = self.prefab.save()
        return s_dict

    @classmethod
    def restore(cls, s_dict: dict) -> MapPrefabTileMapObject:
        # Deliberately does not touch RESOURCES.map_prefabs -- the saved
        # dict is authoritative, unlike TileMapObject.restore.
        prefab = MapPrefab.restore(s_dict['prefab'])
        self = cls.from_prefab(prefab)
        self.restore_weather_and_animations(s_dict)
        return self
