import sys
import unittest

from app.tests import qt_headless  # noqa: F401 -- before any QApplication

from PyQt5.QtWidgets import QApplication

import app.engine.building_component_access as BCA
from app.data.database.buildings import BuildingPrefab
from app.data.database.database import DB
from app.data.database.klass import Klass
from app.editor.editor_locale import init_locale
from app.engine import city_funcs
from app.tests.engine_harness import EngineTestCase
from app.tests.test_city_capture import add_building_prefabs, add_city
from app.utilities.data import Data

LEVEL = '0'

# Classes and items of testing_proj
SWORD_CLASS = 'Myrmidon'
BARE_CLASS = 'Dancer'
SWORD = 'Iron_Sword'
POTION = 'Vulnerary'


class KlassDefaultItemsTests(EngineTestCase):
    '''What a unit of a class is drafted with lives on the class'''

    def test_a_class_has_no_default_items_until_it_is_given_some(self):
        self.assertEqual([], DB.classes.get(SWORD_CLASS).default_items)

    def test_default_items_survive_a_save_and_load(self):
        klass = DB.classes.get(SWORD_CLASS)
        klass.default_items = [[SWORD, False], [POTION, True]]
        restored = Klass.restore(klass.save())
        self.assertEqual([[SWORD, False], [POTION, True]], restored.default_items)

    def test_saving_does_not_share_the_rows_with_the_class(self):
        klass = DB.classes.get(SWORD_CLASS)
        klass.default_items = [[SWORD, False]]
        saved = klass.save()
        saved['default_items'][0][0] = POTION
        self.assertEqual([[SWORD, False]], klass.default_items)

    def test_a_class_saved_before_default_items_existed_has_none(self):
        saved = DB.classes.get(SWORD_CLASS).save()
        del saved['default_items']
        self.assertEqual([], Klass.restore(saved).default_items)

    def test_renaming_an_item_follows_it_into_the_class(self):
        klass = DB.classes.get(SWORD_CLASS)
        klass.default_items = [[SWORD, False], [POTION, True]]
        klass.replace_item_nid(SWORD, 'Steel_Sword')
        self.assertEqual(['Steel_Sword', POTION], klass.get_items())

    def test_a_new_class_gets_each_of_its_values_in_the_right_field(self):
        klass = DB.classes.create_new(DB)
        stats = set(DB.stats.keys())
        self.assertEqual(0, klass.upkeep_cost)
        self.assertEqual([], klass.default_items)
        self.assertEqual([], klass.learned_skills)
        self.assertEqual([], klass.fields)
        for stat_list in klass.get_stat_lists():
            self.assertEqual(stats, set(stat_list.keys()))
        self.assertEqual({stat.nid: stat.maximum for stat in DB.stats}, klass.max_stats)
        self.assertEqual(set(DB.weapons.keys()), set(klass.wexp_gain.keys()))


class DraftedUnitItemsTests(EngineTestCase):
    def setUp(self):
        super().setUp()
        add_building_prefabs()
        DB.buildings.append(BuildingPrefab(
            'Barracks', 'Barracks', '', None,
            components=Data([BCA.restore_component(
                ('produces_units', [[SWORD_CLASS, 1, 0, 0, 0], [BARE_CLASS, 1, 0, 0, 0]]))])))
        self.harness = self.start_harness()
        self.game = self.harness.start_level(LEVEL)
        self.harness.run_until_state('free')
        self.city = add_city(self.game, 'Capital', 'player', (11, 7))
        DB.classes.get(SWORD_CLASS).default_items = [[SWORD, False], [POTION, True]]

    def draft(self, klass):
        return city_funcs.draft_unit(self.city, {'klass': klass, 'level': 1})

    def test_a_drafted_unit_carries_its_classs_default_items(self):
        unit = self.draft(SWORD_CLASS)
        self.assertEqual([SWORD, POTION], [item.nid for item in unit.items])
        self.assertEqual([False, True], [item.droppable for item in unit.items])

    def test_a_drafted_unit_can_fight_with_them(self):
        unit = self.draft(SWORD_CLASS)
        self.assertEqual(SWORD, unit.get_weapon().nid)

    def test_each_drafted_unit_gets_items_of_its_own(self):
        first, second = self.draft(SWORD_CLASS), self.draft(SWORD_CLASS)
        self.assertIsNot(first.items[0], second.items[0])
        self.assertEqual([[SWORD, False], [POTION, True]], DB.classes.get(SWORD_CLASS).default_items)

    def test_a_class_with_no_default_items_is_drafted_empty_handed(self):
        self.assertEqual([], self.draft(BARE_CLASS).items)

    def test_a_drafted_units_items_survive_a_save_and_load(self):
        unit = self.draft(SWORD_CLASS)
        self.harness.round_trip()
        self.assertEqual([SWORD, POTION], [item.nid for item in self.game.get_unit(unit.nid).items])


class ClassEditorDefaultItemsTests(EngineTestCase):
    '''The class editor shows a class's default items, and the item editor keeps them
    pointing at the right item'''

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        init_locale()

    def make_properties(self):
        from app.editor.class_editor.new_class_properties import NewClassProperties
        klass = DB.classes.get(SWORD_CLASS)
        klass.default_items = [[SWORD, False]]
        properties = NewClassProperties(None, klass)
        self.addCleanup(properties.deleteLater)
        return klass, properties

    def test_the_editor_lists_the_classs_default_items(self):
        klass, properties = self.make_properties()
        self.assertEqual([[SWORD, False]], properties.item_widget.get_items())

    def test_adding_an_item_in_the_editor_adds_it_to_the_class(self):
        klass, properties = self.make_properties()
        properties.item_widget.add_new_item()
        self.assertEqual([SWORD, DB.items[0].nid], klass.get_items())

    def test_removing_an_item_in_the_editor_removes_it_from_the_class(self):
        klass, properties = self.make_properties()
        properties.item_widget.remove_last_item()
        self.assertEqual([], klass.default_items)

    def test_switching_class_shows_the_other_classs_items(self):
        klass, properties = self.make_properties()
        properties.set_current(DB.classes.get(BARE_CLASS))
        self.assertEqual([], properties.item_widget.get_items())
        self.assertEqual([[SWORD, False]], klass.default_items)

    def test_renaming_an_item_in_the_item_editor_renames_it_in_classes(self):
        from app.editor.item_editor.item_model import ItemModel
        klass = DB.classes.get(SWORD_CLASS)
        klass.default_items = [[SWORD, False]]
        ItemModel.on_nid_changed(None, SWORD, 'Renamed_Sword')
        self.assertEqual(['Renamed_Sword'], klass.get_items())


if __name__ == '__main__':
    unittest.main()
