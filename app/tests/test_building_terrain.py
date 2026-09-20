import unittest
from unittest.mock import MagicMock

from app.engine.game_state import GameState


class FakeBuilding:
    """Minimal stand-in for a BuildingObject for terrain-override tests."""
    next_uid = 1

    def __init__(self, position, terrain, size=(1, 1)):
        self.uid = FakeBuilding.next_uid
        FakeBuilding.next_uid += 1
        self.position = position
        self.terrain = terrain
        self.size = size

    @property
    def occupied_positions(self):
        if not self.position:
            return []
        return self.positions_at(self.position)

    def positions_at(self, position):
        width, height = self.size
        return [(position[0] + dx, position[1] + dy)
                for dx in range(width) for dy in range(height)]


class FakeCity:
    def __init__(self, buildings):
        self.buildings = buildings


class BuildingTerrainTests(unittest.TestCase):
    def setUp(self):
        # Bypass the heavy GameState.__init__; seed only what get_terrain_nid /
        # the override helpers read.
        self.game = GameState.__new__(GameState)
        self.game.building_terrain_overrides = {}
        self.game.building_position_index = {}
        self.game.city_registry = {}
        self.tilemap = MagicMock()
        self.tilemap.get_terrain = MagicMock(return_value='Plains')
        # No TERRAIN region by default.
        self.game.get_region_under_pos = MagicMock(return_value=None)

    def test_building_overrides_layer(self):
        self.game.add_terrain_override(FakeBuilding((3, 5), 'Fort'))
        self.assertEqual(self.game.get_terrain_nid(self.tilemap, (3, 5)), 'Fort')
        # A tile with no building falls through to the layer terrain.
        self.assertEqual(self.game.get_terrain_nid(self.tilemap, (4, 5)), 'Plains')

    def test_building_overrides_terrain_region(self):
        # A TERRAIN region paints 'Forest' at the tile...
        region = MagicMock()
        region.sub_nid = 'Forest'
        self.game.get_region_under_pos = MagicMock(return_value=region)
        # ...but a building still wins.
        building = FakeBuilding((3, 5), 'Fort')
        self.game.add_terrain_override(building)
        self.assertEqual(self.game.get_terrain_nid(self.tilemap, (3, 5)), 'Fort')
        # Without the building, the region wins over the layer.
        self.game.remove_terrain_override(building)
        self.assertEqual(self.game.get_terrain_nid(self.tilemap, (3, 5)), 'Forest')

    def test_remove_restores_original(self):
        building = FakeBuilding((3, 5), 'Fort')
        self.game.add_terrain_override(building)
        self.assertEqual(self.game.get_terrain_nid(self.tilemap, (3, 5)), 'Fort')
        self.game.remove_terrain_override(building)
        self.assertEqual(self.game.get_terrain_nid(self.tilemap, (3, 5)), 'Plains')

    def test_falsy_terrain_is_no_override(self):
        # A building without a terrain (None / empty) contributes no override.
        self.game.add_terrain_override(FakeBuilding((3, 5), None))
        self.assertNotIn((3, 5), self.game.building_terrain_overrides)
        self.assertEqual(self.game.get_terrain_nid(self.tilemap, (3, 5)), 'Plains')

    def test_unplaced_building_is_no_override(self):
        self.game.add_terrain_override(FakeBuilding(None, 'Fort'))
        self.assertEqual(self.game.building_terrain_overrides, {})

    def test_rebuild_from_cities(self):
        placed = FakeBuilding((1, 1), 'Fort')
        unplaced = FakeBuilding(None, 'Fort')
        no_terrain = FakeBuilding((2, 2), None)
        self.game.city_registry = {'city': FakeCity([placed, unplaced, no_terrain])}
        # Pre-seed a stale override to prove rebuild clears first.
        self.game.building_terrain_overrides = {(9, 9): 'Stale'}

        self.game.rebuild_terrain_overrides()

        self.assertEqual(self.game.building_terrain_overrides, {(1, 1): 'Fort'})

    def test_footprint_covers_every_tile(self):
        # A 2x2 building is anchored at its top left tile and overrides all four.
        building = FakeBuilding((3, 5), 'Fort', size=(2, 2))
        self.game.add_terrain_override(building)
        for pos in ((3, 5), (4, 5), (3, 6), (4, 6)):
            self.assertEqual(self.game.get_terrain_nid(self.tilemap, pos), 'Fort')
        # Just outside the footprint is untouched.
        self.assertEqual(self.game.get_terrain_nid(self.tilemap, (5, 5)), 'Plains')

        self.game.remove_terrain_override(building)
        self.assertEqual(self.game.building_terrain_overrides, {})
        self.assertEqual(self.game.building_position_index, {})

    def test_terrainless_building_still_occupies_tiles(self):
        # A building with no terrain contributes no override, but its footprint
        # is still occupied so nothing else may be built on top of it.
        building = FakeBuilding((3, 5), None, size=(2, 1))
        self.game.add_terrain_override(building)
        self.assertEqual(self.game.building_terrain_overrides, {})
        self.assertEqual(self.game.building_position_index,
                         {(3, 5): building.uid, (4, 5): building.uid})

    def test_remove_leaves_another_buildings_tiles_alone(self):
        keeper = FakeBuilding((3, 5), 'Fort')
        self.game.add_terrain_override(keeper)
        # A building that was never placed there must not evict the keeper.
        self.game.remove_terrain_override(FakeBuilding((3, 5), 'Fort'))
        self.assertEqual(self.game.get_terrain_nid(self.tilemap, (3, 5)), 'Fort')


if __name__ == '__main__':
    unittest.main()
