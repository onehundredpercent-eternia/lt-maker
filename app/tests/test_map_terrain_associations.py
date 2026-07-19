import unittest
from pathlib import Path
from unittest import mock

from app.data.database.map_terrain_associations import (
    DEFAULT_ASSOCIATIONS, FALLBACK_NID, MapTerrainAssociations)
from app.map_maker.terrain import Terrain
from app.utilities.serialization import load_json


class MapTerrainAssociationsTests(unittest.TestCase):
    def test_completeness(self):
        # Every Terrain enum member must have a default association.
        missing = [t for t in Terrain.list() if t not in DEFAULT_ASSOCIATIONS]
        self.assertEqual([], missing, "Missing default associations for: %s" % missing)

    def test_validity_against_default_ltproj(self):
        # Every default nid must exist in default.ltproj's terrain data.
        terrain_json_path = Path('default.ltproj', 'game_data', 'terrain.json')
        terrain_data = load_json(terrain_json_path)
        valid_nids = {entry['nid'] for entry in terrain_data}
        for terrain, nid in DEFAULT_ASSOCIATIONS.items():
            self.assertIn(
                nid, valid_nids,
                "Terrain.%s maps to nid %r, which is not present in default.ltproj terrain.json" %
                (terrain.name, nid))

    def test_lookup_order_override_beats_default(self):
        assoc = MapTerrainAssociations()
        default_nid = DEFAULT_ASSOCIATIONS[Terrain.GRASS]
        self.assertEqual(default_nid, assoc.get(Terrain.GRASS))

        assoc.set(Terrain.GRASS, 'some_override_nid')
        self.assertEqual('some_override_nid', assoc.get(Terrain.GRASS))

        assoc.clear(Terrain.GRASS)
        self.assertEqual(default_nid, assoc.get(Terrain.GRASS))

    def test_lookup_fallback_when_terrain_missing_from_default(self):
        # Exercise the real get() fallback path; patch.dict restores the
        # module dict afterward even if the test fails.
        defaults_without_grass = {
            t: n for t, n in DEFAULT_ASSOCIATIONS.items() if t is not Terrain.GRASS}
        assoc = MapTerrainAssociations()
        with mock.patch.dict(
                'app.data.database.map_terrain_associations.DEFAULT_ASSOCIATIONS',
                defaults_without_grass, clear=True):
            self.assertEqual(FALLBACK_NID, assoc.get(Terrain.GRASS))
        self.assertIn(Terrain.GRASS, DEFAULT_ASSOCIATIONS)

    def test_save_restore_round_trip(self):
        assoc = MapTerrainAssociations()
        assoc.set(Terrain.GRASS, 'custom1')
        assoc.set(Terrain.MOUNTAIN, 'custom2')

        saved = assoc.save()

        restored = MapTerrainAssociations()
        restored.restore(saved)

        self.assertEqual(assoc.overrides, restored.overrides)
        self.assertEqual('custom1', restored.get(Terrain.GRASS))
        self.assertEqual('custom2', restored.get(Terrain.MOUNTAIN))

    def test_restore_none_does_not_crash(self):
        assoc = MapTerrainAssociations()
        assoc.set(Terrain.GRASS, 'custom1')
        assoc.restore(None)
        self.assertEqual({}, assoc.overrides)

    def test_restore_empty_does_not_crash(self):
        assoc = MapTerrainAssociations()
        assoc.restore([])
        self.assertEqual({}, assoc.overrides)

    def test_restore_unknown_terrain_name_skipped(self):
        assoc = MapTerrainAssociations()
        assoc.restore([('NOT_A_REAL_TERRAIN', 'whatever'), ('GRASS', 'custom1')])
        self.assertEqual({Terrain.GRASS: 'custom1'}, assoc.overrides)


if __name__ == '__main__':
    unittest.main()
