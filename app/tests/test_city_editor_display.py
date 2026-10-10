import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.tests import qt_headless  # noqa: F401  (before the first QApplication)
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import QApplication

import app.engine.building_component_access as BCA
from app.constants import TILEHEIGHT, TILEWIDTH
from app.data.cities import City
from app.data.database.buildings import BuildingPrefab
from app.data.database.database import DB
from app.utilities.data import Data

_app = QApplication.instance() or QApplication(sys.argv)

# Needs a QApplication, since importing it builds pixmaps
from app.editor import map_view  # noqa: E402

TOWN_HALL = 'TestTownHall'
FARM = 'TestFarm'


class CityMarkerTests(unittest.TestCase):
    '''The level editor marks a city over its whole center, as the engine sees it'''

    def setUp(self):
        DB.buildings.append(BuildingPrefab(
            TOWN_HALL, 'Town Hall', '', None, size=(2, 2),
            components=Data([BCA.restore_component(('city_center', None))])))
        DB.buildings.append(BuildingPrefab(FARM, 'Farm', '', None))
        self.addCleanup(DB.buildings.remove_key, TOWN_HALL)
        self.addCleanup(DB.buildings.remove_key, FARM)

    def make_city(self, position, buildings) -> City:
        city = City('Capital')
        city.position = position
        city.buildings = buildings
        return city

    def test_a_city_with_a_town_hall_is_marked_over_all_four_tiles(self):
        city = self.make_city((3, 4), [[FARM, (1, 1)], [TOWN_HALL, (3, 4)]])
        center = map_view.get_city_center_positions(city)
        self.assertEqual({(3, 4), (4, 4), (3, 5), (4, 5)}, set(center))
        self.assertEqual(QRect(3 * TILEWIDTH, 4 * TILEHEIGHT, 2 * TILEWIDTH, 2 * TILEHEIGHT),
                         map_view.get_bounding_rect(center))

    def test_the_marker_follows_the_town_hall_not_the_city_position(self):
        city = self.make_city((3, 4), [[TOWN_HALL, (8, 8)]])
        self.assertEqual({(8, 8), (9, 8), (8, 9), (9, 9)},
                         set(map_view.get_city_center_positions(city)))

    def test_an_unplaced_town_hall_leaves_the_city_on_its_own_tile(self):
        city = self.make_city((3, 4), [[TOWN_HALL, None]])
        self.assertEqual([(3, 4)], map_view.get_city_center_positions(city))

    def test_a_city_without_a_town_hall_is_marked_on_its_own_tile(self):
        city = self.make_city((3, 4), [[FARM, (1, 1)]])
        self.assertEqual([(3, 4)], map_view.get_city_center_positions(city))

    def test_an_unplaced_city_has_no_marker(self):
        self.assertEqual([], map_view.get_city_center_positions(self.make_city(None, [])))

    def test_a_placement_covers_the_buildings_whole_footprint(self):
        self.assertEqual({(8, 8), (9, 8), (8, 9), (9, 9)},
                         set(map_view.get_placement_positions(TOWN_HALL, (8, 8))))
        self.assertEqual([(1, 1)], map_view.get_placement_positions(FARM, (1, 1)))
        self.assertEqual([], map_view.get_placement_positions(FARM, None))

    def paint(self, city: City, selected: bool = False) -> QPixmap:
        """Runs the level editor's city painting over a blank white 8x8 tile map"""
        working_image = QPixmap(8 * TILEWIDTH, 8 * TILEHEIGHT)
        working_image.fill(QColor(255, 255, 255))
        painter_menu = MagicMock()
        painter_menu.get_current.return_value = city if selected else None
        painter_menu.get_current_building.return_value = None
        view = SimpleNamespace(
            working_image=working_image,
            current_level=SimpleNamespace(cities=[city]),
            main_editor=SimpleNamespace(city_painter_menu=painter_menu),
            get_building_pixmap=lambda building, team_nid: None)
        map_view.NewMapView.paint_cities(view)
        return working_image

    def is_painted(self, image, tile) -> bool:
        """Whether the middle of a tile is no longer the blank map's white"""
        x = tile[0] * TILEWIDTH + TILEWIDTH // 2
        y = tile[1] * TILEHEIGHT + TILEHEIGHT // 2
        return image.pixelColor(x, y) != QColor(255, 255, 255)

    def test_the_marker_is_painted_on_every_center_tile_and_nowhere_else(self):
        city = self.make_city((3, 4), [[TOWN_HALL, (3, 4)]])
        image = self.paint(city).toImage()
        center = {(3, 4), (4, 4), (3, 5), (4, 5)}
        painted = {(x, y) for x in range(8) for y in range(8) if self.is_painted(image, (x, y))}
        self.assertEqual(center, painted)

    def test_the_selected_city_is_outlined_around_its_whole_center(self):
        city = self.make_city((3, 4), [[TOWN_HALL, (3, 4)]])
        city.team = 'player'
        plain = self.paint(city).toImage()
        outlined = self.paint(city, selected=True).toImage()
        # The outline runs along the top left of the anchor and the far edge of the
        # opposite corner, two tiles away
        self.assertNotEqual(plain.pixelColor(3 * TILEWIDTH, 4 * TILEHEIGHT),
                            outlined.pixelColor(3 * TILEWIDTH, 4 * TILEHEIGHT))
        self.assertNotEqual(plain.pixelColor(5 * TILEWIDTH, 6 * TILEHEIGHT),
                            outlined.pixelColor(5 * TILEWIDTH, 6 * TILEHEIGHT))
        # ...and no longer cuts through the middle of the center
        self.assertEqual(plain.pixelColor(4 * TILEWIDTH, 5 * TILEHEIGHT - 2),
                         outlined.pixelColor(4 * TILEWIDTH, 5 * TILEHEIGHT - 2))


if __name__ == '__main__':
    unittest.main()
