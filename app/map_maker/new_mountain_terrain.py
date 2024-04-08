from __future__ import annotations

from typing import List, Set
from app.utilities.typing import Pos

from PyQt5.QtGui import QPixmap

from app.map_maker.utilities import flood_fill
from app.map_maker.terrain import Terrain

class NewMountainTerrain(Terrain):
    terrain_like = ('Mountain',)

    @property
    def check_flood_fill(self) -> bool:
        return True

    def determine_sprite(self, tilemap, pos: Pos, autotile_num: int) -> QPixmap:
        pix = self.get_pixmap(coord, autotile_num)
        return pix

    def initial_process(self):
        pass

    def _get_mountain_groups(self, tilemap) -> List[Set[Pos]]:
        positions: Set[Pos] = tilemap.get_all_terrain(self.nid)
        mountain_groups: List[Set[Pos]] = []

        # Get all groups of mountains
        counter = 0
        limit = int(1e6)
        while positions and counter < limit:
            pos = positions.pop()
            near_positions: Set[Pos] = flood_fill(tilemap, pos)
            mountain_groups.append(near_positions)
            for near_pos in near_positions:
                positions.discard(near_pos)
            counter += 1
        if counter >= limit:
            raise RuntimeError("Unexpected infinite loop in mountain flood_fill")
        return mountain_groups

    def _process_group(self, tilemap, group: Set[Pos]):
        pass

    def single_process(self, tilemap):
        mountain_groups: List[Set[Pos]] = self._get_mountain_groups(tilemap)

        for group in mountain_groups:
            # Check whether anything in this group has been updated
            if not (group & tilemap.terrain_grid_to_update):
                continue
            self._process_group(tilemap, group)
