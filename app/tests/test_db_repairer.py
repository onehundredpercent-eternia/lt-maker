from app.data.database.levels import OBJECTIVE_KEYS
from app.data.database.level_units import GenericUnit, UniqueUnit, UnitGroup
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

    def test_good_unit_repair(self):
        before_repair = self.db.units[0].save()
        self.db_repairer.repair_units()
        after_repair = self.db.units[0].save()
        self.assertEqual(before_repair, after_repair)

    def test_bad_unit_repair(self):
        unit = self.db.units[0]
        FALSE_ITEM = ["Elixir_Of_Immortality", False]
        unit.starting_items.append(FALSE_ITEM)

        FALSE_CLASS = "Gaiden_Harrier"
        unit.klass = FALSE_CLASS

        del unit.bases['STR']

        FALSE_SKILL = [69, "Rightful_God_Emperor_Of_Mankind"]
        unit.learned_skills.append(FALSE_SKILL)

        del unit.wexp_gain['Sword']

        FALSE_PORTRAIT = 'Dorian_Gray'
        unit.portrait_nid = FALSE_PORTRAIT

        self.db_repairer.repair_units()

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

    def test_good_level_repair(self):
        before_repair = self.db.levels[0].save()
        self.db_repairer.repair_levels()
        after_repair = self.db.levels[0].save()
        self.assertEqual(before_repair, after_repair)

    def test_bad_level_properties_repair(self):
        level = self.db.levels[0]
        level.tilemap = "Mordor"
        level.bg_tilemap = "Coruscant"
        level.party = "Donner"

        FALSE_MUSIC_KEY = "battle_coda"
        FALSE_MUSIC = "Flight_of_the_Valkyries"
        level.music[FALSE_MUSIC_KEY] = FALSE_MUSIC
        level.music['player_phase'] = FALSE_MUSIC

        level.objective = {}

        FALSE_UNIT = "Don_Quixote"
        level.roam_unit = FALSE_UNIT

        self.db_repairer.repair_levels()

        self.assertIsNone(level.tilemap)
        self.assertIsNone(level.bg_tilemap)
        self.assertEqual(level.party, self.db.parties[0].nid)
        self.assertFalse(FALSE_MUSIC_KEY in level.music.keys())
        self.assertIsNone(level.music['player_phase'])
        for key in OBJECTIVE_KEYS:
            self.assertTrue(key in level.objective)
        self.assertEqual(level.roam_unit, self.db.units[0].nid)

    def test_bad_level_units_repair(self):
        level = self.db.levels[0]

        FALSE_LEVEL_UNIT = "Hatsune_Miku"
        level.units.append(UniqueUnit(FALSE_LEVEL_UNIT))

        additional_units = ['Gumi', 'Flower', 'Luka', 'Rin', 'Len', 'Kaai']
        for unit_nid in additional_units:
            level.units.append(GenericUnit(unit_nid))
        DOUBLED_TRAVELER = 'Gumi'
        UNIT_WITH_TRAVELER = 'Flower'
        level.units.get(UNIT_WITH_TRAVELER).starting_position = (0, 0)
        level.units.get(UNIT_WITH_TRAVELER).starting_traveler = DOUBLED_TRAVELER
        SECOND_UNIT_WITH_TRAVELER = 'Luka'
        level.units.get(SECOND_UNIT_WITH_TRAVELER).starting_position = (0, 1)
        level.units.get(SECOND_UNIT_WITH_TRAVELER).starting_traveler = DOUBLED_TRAVELER

        UNIT_NOT_ON_MAP = 'Rin'
        level.units.get(UNIT_NOT_ON_MAP).starting_traveler = 'Len'

        UNIT_CARRYING_ITSELF = 'Kaai'
        level.units.get(UNIT_CARRYING_ITSELF).starting_traveler = UNIT_CARRYING_ITSELF

        FALSE_CLASS = "Proletariat"
        FALSE_FACTION = "Centrism"
        ACCEPTABLE_ITEM = self.db.items[0].nid
        FALSE_ITEM = "Fountain_Of_Youth"
        ACCEPTABLE_SKILL = self.db.skills[0].nid
        FALSE_SKILL = "Proc_Skills_Cant_Hurt_You"
        FALSE_PLAYER = "ready_player_1"
        FALSE_AI = 'Jarvis'
        FALSE_TRAVELER = 'Hime'
        PROBLEMATIC_GENERIC_UNIT = 'Kafu'
        level.units.append(GenericUnit(nid=PROBLEMATIC_GENERIC_UNIT, variant=None, level=1,
                                       klass=FALSE_CLASS, faction=FALSE_FACTION,
                                       starting_items=[[ACCEPTABLE_ITEM, True], [FALSE_ITEM, False]],
                                       starting_skills=[ACCEPTABLE_SKILL, FALSE_SKILL],
                                       team=FALSE_PLAYER, ai=FALSE_AI, roam_ai=FALSE_AI, starting_traveler=FALSE_TRAVELER))

        self.db_repairer.repair_levels()

        all_level_units = [unit.nid for unit in level.units]
        self.assertFalse(FALSE_LEVEL_UNIT in all_level_units)

        problematic_unit = level.units.get(PROBLEMATIC_GENERIC_UNIT)
        if not isinstance(problematic_unit, GenericUnit):
            raise Exception("Should never be hit")
        self.assertEqual(problematic_unit.klass, self.db.classes[0].nid)
        self.assertEqual(problematic_unit.faction, self.db.factions[0].nid)
        self.assertEqual(len(problematic_unit.starting_items), 1)
        self.assertEqual(problematic_unit.starting_items[0][0], ACCEPTABLE_ITEM)
        self.assertEqual(len(problematic_unit.starting_skills), 1)
        self.assertEqual(problematic_unit.starting_skills[0], ACCEPTABLE_SKILL)
        self.assertEqual(problematic_unit.team, self.db.teams[0])
        self.assertIsNone(problematic_unit.ai)
        self.assertIsNone(problematic_unit.roam_ai)
        self.assertIsNone(problematic_unit.starting_traveler)

        self.assertIsNone(level.units.get(UNIT_WITH_TRAVELER).starting_traveler)
        self.assertIsNone(level.units.get(SECOND_UNIT_WITH_TRAVELER).starting_traveler)
        self.assertIsNone(level.units.get(UNIT_NOT_ON_MAP).starting_traveler)
        self.assertIsNone(level.units.get(UNIT_CARRYING_ITSELF).starting_traveler)

    def test_bad_level_groups_repair(self):
        level = self.db.levels[0]
        GOOD_UNIT = 'Hatsune_Miku'
        level.units.append(GenericUnit(GOOD_UNIT))
        FLAWED_GROUP = 'Weather_Underground'
        bad_group = UnitGroup(FLAWED_GROUP, [GOOD_UNIT, 'Kafu'], {'Luka': (2, 3)})
        level.unit_groups.append(bad_group)

        self.db_repairer.repair_levels()

        group = level.unit_groups.get(FLAWED_GROUP)
        if not group:
            return
        self.assertFalse('Kafu' in group.units)
        self.assertFalse('Luka' in group.positions)
        self.assertEqual(group.positions[GOOD_UNIT], (0, 0))

if __name__ == '__main__':
    unittest.main()
