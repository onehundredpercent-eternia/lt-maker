import unittest

from app.constants import COLORKEY


class BuildingPaletteTests(unittest.TestCase):
    """The color table that recolors a building sprite for a map style and team."""

    def setUp(self):
        from app.data.resources.combat_palettes import Palette
        from app.data.resources.resources import RESOURCES
        from app.data.database.database import DB
        from app.data.resources import building_palettes

        self.building_palettes = building_palettes
        self.DB = DB

        # A reference ramp: the colorkey, 13 map colors, then the 2 team colors.
        num_map = building_palettes.NUM_MAP_COLORS
        self.ref_map = [(10 * i, 0, 0) for i in range(1, num_map + 1)]
        self.ref_team = [(0, 10, 0), (0, 20, 0)]
        self.style_map = [(0, 0, 10 * i) for i in range(1, num_map + 1)]

        # The palette catalog is a global shared with every other test, so put
        # back whatever was there (see tearDown)
        self.saved_palettes = list(RESOURCES.combat_palettes)
        RESOURCES.combat_palettes.clear()
        RESOURCES.combat_palettes.append(
            Palette.from_list('building_ref', [COLORKEY] + self.ref_map + self.ref_team))
        RESOURCES.combat_palettes.append(
            Palette.from_list('journey', [COLORKEY] + self.style_map))

        DB.teams.add_defaults()

    def tearDown(self):
        from app.data.resources.resources import RESOURCES
        RESOURCES.combat_palettes.clear()
        for palette in self.saved_palettes:
            RESOURCES.combat_palettes.append(palette)

    def test_map_colors_come_from_the_style(self):
        conversion = self.building_palettes.get_conversion_dict('journey', 'player')
        for ref_color, style_color in zip(self.ref_map, self.style_map):
            self.assertEqual(conversion[ref_color], style_color)

    def test_team_colors_come_from_the_team(self):
        team = self.DB.teams.get('player')
        conversion = self.building_palettes.get_conversion_dict('journey', 'player')
        self.assertEqual(conversion[self.ref_team[0]], team.building_color_primary)
        self.assertEqual(conversion[self.ref_team[1]], team.building_color_secondary)

    def test_teams_recolor_differently(self):
        player = self.building_palettes.get_conversion_dict('journey', 'player')
        enemy = self.building_palettes.get_conversion_dict('journey', 'enemy')
        self.assertNotEqual(player[self.ref_team[0]], enemy[self.ref_team[0]])
        # ...but the map colors are identical on the same map
        self.assertEqual(player[self.ref_map[0]], enemy[self.ref_map[0]])

    def test_colorkey_is_never_converted(self):
        conversion = self.building_palettes.get_conversion_dict('journey', 'player')
        self.assertNotIn(tuple(COLORKEY), conversion)
        self.assertEqual(len(conversion),
                         self.building_palettes.NUM_MAP_COLORS
                         + self.building_palettes.NUM_TEAM_COLORS)

    def test_missing_style_leaves_map_colors_alone(self):
        # A map with no style set still recolors for the team, and leaves the rest
        # in the reference ramp rather than crashing or drawing transparent.
        conversion = self.building_palettes.get_conversion_dict(None, 'player')
        self.assertNotIn(self.ref_map[0], conversion)
        self.assertIn(self.ref_team[0], conversion)

    def test_short_reference_ramp_is_logged(self):
        # A mis-authored ramp lands the team colors on the wrong entries, so say so
        # loudly rather than silently under-converting.
        from app.data.resources.combat_palettes import Palette
        from app.data.resources.resources import RESOURCES
        RESOURCES.combat_palettes.remove_key('building_ref')
        RESOURCES.combat_palettes.append(
            Palette.from_list('building_ref', [COLORKEY] + self.ref_map))
        with self.assertLogs(level='ERROR') as logged:
            self.building_palettes.get_conversion_dict('journey', 'player')
        self.assertIn('building_ref', logged.output[0])

    def test_missing_reference_ramp_converts_nothing(self):
        from app.data.resources.resources import RESOURCES
        RESOURCES.combat_palettes.clear()
        self.assertEqual(self.building_palettes.get_conversion_dict('journey', 'player'), {})


if __name__ == '__main__':
    unittest.main()
