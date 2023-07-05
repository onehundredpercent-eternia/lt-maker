import unittest

from app.editor.ai_editor import ai_model
from app.editor.class_editor import class_model
from app.editor.difficulty_mode_editor import difficulty_mode_model
from app.editor.event_editor import event_model
from app.editor.faction_editor import faction_model
from app.editor.item_editor import item_model
from app.editor.lore_editor import lore_model
from app.editor.party_editor import party_model
from app.editor.skill_editor import skill_model
from app.editor.stat_editor import stat_model
from app.editor.team_editor import team_model
from app.editor.terrain_editor import terrain_model
from app.editor.unit_editor import unit_model
from app.editor.weapon_editor import weapon_model

class ObjectCreationUnitTests(unittest.TestCase):
    """
    # Tests that the editor's creation API correctly adds the object to the database
    # Does not currently test creation of:
    # - equations
    # - mcost rows/columns
    # - tags
    # - weapon ranks
    # - game var slots
    # - support ranks
    # - support pairs
    # - affinities
    # - raw data
    # - levels
    # - translations
    # Constants, Support Constants, and Minimap data don't have new information added to them by the user
    """
    def setUp(self):
        from app.data.database.database import DB
        DB.load('testing_proj.ltproj')

    def _test_create_new(self, model, data):
        """
        # Generic test used by the rest of the testing functions below.
        # Counts number of elements before and after and makes sure we've increased by one.
        # Also makes sure the command itself just works.
        """
        number_of_elems = len(data)
        collection_model = model(data, None)
        collection_model.create_new()
        # confirm we added an element
        self.assertEqual(number_of_elems + 1, len(data))

    def test_create_unit(self):
        data = DB.units
        model = unit_model.UnitModel
        self._test_create_new(model, data)

    def test_create_class(self):
        data = DB.classes
        model = class_model.ClassModel
        self._test_create_new(model, data)

    def test_create_team(self):
        data = DB.teams
        model = team_model.TeamModel
        self._test_create_new(model, data)

    def test_create_item(self):
        data = DB.items
        model = item_model.ItemModel
        self._test_create_new(model, data)

    def test_create_skill(self):
        data = DB.skills
        model = skill_model.SkillModel
        self._test_create_new(model, data)

    def test_create_faction(self):
        data = DB.factions
        model = faction_model.FactionModel
        self._test_create_new(model, data)

    def test_create_party(self):
        data = DB.parties
        model = party_model.PartyModel
        self._test_create_new(model, data)

    def test_create_weapon_type(self):
        data = DB.weapons
        model = weapon_model.WeaponModel
        self._test_create_new(model, data)

    def test_create_stat(self):
        data = DB.stats
        model = stat_model.StatModel
        self._test_create_new(model, data)

    def test_create_lore(self):
        data = DB.lore
        model = lore_model.LoreModel
        self._test_create_new(model, data)

    def test_create_difficulty_mode(self):
        data = DB.difficulty_modes
        model = difficulty_mode_model.DifficultyModeModel
        self._test_create_new(model, data)

    def test_create_ai(self):
        data = DB.ai
        model = ai_model.AIModel
        self._test_create_new(model, data)

    def test_create_terrain(self):
        data = DB.terrain
        model = terrain_model.TerrainModel
        self._test_create_new(model, data)

    def test_create_event(self):
        data = DB.events
        model = event_model.EventModel
        self._test_create_new(model, data)
