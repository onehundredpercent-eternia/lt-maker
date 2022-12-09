from app.data.database.weapons import WexpGain
import unittest
from unittest.mock import MagicMock, patch, call
from app.data.database.database_types import DatabaseType
from app.data.database_validator import DatabaseRepair, DatabaseValidatorEngine

from app.data.database.database import Database
from app.data.resources.resources import Resources

class DBRepairTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.resources = Resources()
        self.db.load('testing_proj.ltproj')
        self.resources.load('testing_proj.ltproj')
        self.db_repairer = DatabaseRepair(self.db, self.resources)

    def tearDown(self) -> None:
        pass

    def test_unit_repair(self):
        unit = self.db.units[0]
        FALSE_ITEM = ("Elixir_Of_Immortality", False)
        unit.starting_items.append(FALSE_ITEM)

        FALSE_CLASS = "Gaiden_Harrier"
        unit.klass = FALSE_CLASS

        del unit.bases['STR']

        FALSE_SKILL = (69, "Rightful_God_Emperor_Of_Mankind")
        unit.learned_skills.append(FALSE_SKILL)

        del unit.wexp_gain['Sword']

        FALSE_PORTRAIT = 'Dorian_Gray'
        unit.portrait_nid = FALSE_PORTRAIT

        self.db_repairer.autorepair_db()

        self.assertFalse(FALSE_ITEM in unit.starting_items)
        self.assertNotEqual(unit.klass, FALSE_CLASS)
        self.assertTrue(unit.klass in self.db.classes.keys())
        self.assertNotEqual(unit.bases.get('STR', None), None)
        self.assertEqual(unit.bases.get('STR', 0), 0)
        self.assertFalse(FALSE_SKILL in unit.learned_skills)
        self.assertNotEqual(unit.wexp_gain.get('Sword', None), None)
        sword_wexp = unit.wexp_gain.get('Sword')
        if sword_wexp:
            self.assertEqual(sword_wexp.wexp_gain, 0)
        self.assertIsNone(unit.portrait_nid)

if __name__ == '__main__':
    unittest.main()
