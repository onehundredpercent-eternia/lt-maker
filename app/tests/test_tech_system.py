import json
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import logging
import unittest
from unittest.mock import MagicMock

import pygame

import app.engine.tech_component_access as TCA
from app.data.database.database import DB
from app.data.database.tech_components import Combine, GrantTarget
from app.data.database.techs import TechPrefab
from app.data.resources.resources import RESOURCES
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
from app.engine import action, tech_funcs
from app.events import event_commands, event_functions, event_validators
from app.utilities import str_utils
from app.utilities.data import Data

AVALON_TECHS = os.path.join('..', 'avalon', 'avalon.ltproj', 'game_data', 'techs.json')

# Legacy flag keys whose component was renamed. The migration is still lossless: the old
# key lands on the new component, which publishes the new key.
RENAMED_KEYS = {'city_pop_cap_bonus': 'city_pop_bonus'}


def setUpModule():
    pygame.init()
    pygame.display.set_mode((1, 1))


def comp(nid, value=None):
    """A tech component, optionally with a value. NewMultipleOptions components merge a
    partial dict over their defaults, exactly as they do when restored from disk."""
    if value is None:
        return TCA.get_component(nid)
    return TCA.restore_component((nid, value))


def make_tech(nid, name='', cost=0, requires=None, conditions=None, components=None):
    return TechPrefab(nid, name, renown_cost=cost, requires=requires,
                      conditions=conditions, components=Data(components or []))


class _TechTestCaseMixin:
    """A real running game singleton with a seeded DB.techs catalog.

    action.UnlockTech and event_functions both reach the module-level `game`
    singleton (renown lives on game.teams' TeamObjects, and action.do appends
    to game.action_log), so drive that rather than a fresh GameState.
    """

    @classmethod
    def setUpClass(cls):
        DB.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        RESOURCES.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        # RESOURCES.load() resets app.sprites.SPRITES to image-less entries;
        # driver.start() reloads them during real startup. Mirror that step.
        from app.engine import sprites as engine_sprites
        engine_sprites.load_images()

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.techs = [
            make_tech('IronWeapons', 'Iron Weapons', cost=100,
                      components=[comp('weapon_tier', 1)]),
            make_tech('SteelWeapons', 'Steel Weapons', cost=250,
                      requires=['IronWeapons'],
                      components=[comp('weapon_tier', 2)]),
            make_tech('CityCap1', 'Increase City Cap 1', cost=150,
                      components=[comp('city_pop_bonus', 5)]),
            make_tech('CityCap2', 'Increase City Cap 2', cost=300,
                      requires=['CityCap1'],
                      components=[comp('city_pop_bonus', 5)]),
            make_tech('MageTraining', 'Mage Training', cost=200,
                      components=[comp('draft_unlock', ['Mage']),
                                  comp('build_unlock', ['Library'])]),
            make_tech('ClericTraining', 'Cleric Training', cost=200,
                      components=[comp('draft_unlock', ['Cleric'])]),
            make_tech('EliteInfantry', 'Elite Infantry', cost=200,
                      components=[comp('custom_flag', {'key': 'elite_promote_infantry',
                                                       'value': 'True', 'combine': 'or'})]),
            make_tech('NeverUnlockable', 'Never Unlockable', cost=0,
                      conditions=['False']),
        ]
        for tech in self.techs:
            DB.techs.append(tech)

        from app.engine.game_state import game
        game.build_new()
        self.game = game
        self.team = game.teams.get('player')
        self.team.renown = 1000
        self.team.research.clear()
        tech_funcs.invalidate_flag_cache(self.team)

    def tearDown(self):
        logging.disable(logging.NOTSET)
        for tech in self.techs:
            DB.techs.delete(tech)

    def unlock(self, tech_nid, free=False):
        action.do(action.UnlockTech(self.team, tech_nid, free=free))


class TechFlagCacheTests(_TechTestCaseMixin, unittest.TestCase):
    """The combine policies, and the laziness/invalidation of the flag cache."""

    def test_unknown_key_returns_default(self):
        self.assertEqual(0, tech_funcs.get_tech_value(self.team, 'weapon_tier'))
        self.assertEqual(7, tech_funcs.get_tech_value(self.team, 'weapon_tier', 7))
        self.assertEqual(set(), tech_funcs.get_tech_set(self.team, 'draft_unlock'))

    def test_combine_max_takes_highest_not_latest(self):
        self.unlock('SteelWeapons')
        self.unlock('IronWeapons')
        self.assertEqual(2, tech_funcs.get_tech_value(self.team, 'weapon_tier'))

    def test_combine_sum_stacks(self):
        self.unlock('CityCap1')
        self.assertEqual(5, tech_funcs.get_tech_value(self.team, 'city_pop_bonus'))
        self.unlock('CityCap2')
        self.assertEqual(10, tech_funcs.get_tech_value(self.team, 'city_pop_bonus'))

    def test_combine_set_accumulates_across_techs(self):
        self.unlock('MageTraining')
        self.unlock('ClericTraining')
        self.assertEqual({'Mage', 'Cleric'}, tech_funcs.get_tech_set(self.team, 'draft_unlock'))
        # A multi-effect tech writes every one of its flags
        self.assertEqual({'Library'}, tech_funcs.get_tech_set(self.team, 'build_unlock'))

    def test_one_set_component_can_hold_several_nids(self):
        # The component's value is a list, so a single tech can unlock several classes
        DB.techs.get('MageTraining').components.get('draft_unlock').value = ['Mage', 'Monk']
        self.unlock('MageTraining')
        self.assertEqual({'Mage', 'Monk'}, tech_funcs.get_tech_set(self.team, 'draft_unlock'))

    def test_combine_or_is_boolean(self):
        self.assertFalse(tech_funcs.get_tech_value(self.team, 'elite_promote_infantry'))
        self.unlock('EliteInfantry')
        self.assertTrue(tech_funcs.get_tech_value(self.team, 'elite_promote_infantry'))

    def test_get_tech_set_returns_a_copy(self):
        self.unlock('MageTraining')
        got = tech_funcs.get_tech_set(self.team, 'draft_unlock')
        got.add('Brigand')
        self.assertEqual({'Mage'}, tech_funcs.get_tech_set(self.team, 'draft_unlock'))

    def test_cache_survives_reads_and_invalidates_on_unlock(self):
        self.unlock('CityCap1')
        tech_funcs.get_tech_value(self.team, 'city_pop_bonus')
        self.assertIsNotNone(self.team._tech_flag_cache)
        self.unlock('CityCap2')
        self.assertIsNone(self.team._tech_flag_cache)
        self.assertEqual(10, tech_funcs.get_tech_value(self.team, 'city_pop_bonus'))

    def test_flag_cache_is_not_serialized(self):
        self.unlock('CityCap1')
        tech_funcs.get_tech_value(self.team, 'city_pop_bonus')
        s_dict = self.team.save()
        self.assertNotIn('_tech_flag_cache', s_dict)
        self.assertEqual(['CityCap1'], s_dict['research'])
        self.assertEqual(self.team.renown, s_dict['renown'])

        from app.engine.objects.team import TeamObject
        restored = TeamObject.restore(s_dict)
        self.assertIsNone(restored._tech_flag_cache)
        self.assertEqual(5, tech_funcs.get_tech_value(restored, 'city_pop_bonus'))


class TechComponentFlagTests(unittest.TestCase):
    """Each component owns its flag key and combine policy; a designer cannot set either.
    The parameterized keys build their key from their own value."""

    @classmethod
    def setUpClass(cls):
        DB.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)

    def test_fixed_key_components(self):
        self.assertEqual([('city_pop_bonus', 5, Combine.SUM)],
                         comp('city_pop_bonus', 5).flags())
        self.assertEqual([('weapon_tier', 3, Combine.MAX)],
                         comp('weapon_tier', 3).flags())
        self.assertEqual([('draft_unlock', ['Mage'], Combine.SET)],
                         comp('draft_unlock', ['Mage']).flags())

    def test_resource_bonus_builds_its_key_from_its_tag(self):
        self.assertEqual([('mine_resource_bonus', 2, Combine.SUM)],
                         comp('resource_bonus', {'building_tag': 'Mine', 'amount': 2}).flags())

    def test_upkeep_reduction_builds_its_key_from_its_tag(self):
        self.assertEqual([('upkeep_cost_Mounted', 1, Combine.SUM)],
                         comp('upkeep_cost_reduction', {'unit_tag': 'Mounted', 'amount': 1}).flags())

    def test_parameterized_component_with_no_tag_contributes_nothing(self):
        self.assertEqual([], comp('upkeep_cost_reduction', {'unit_tag': None, 'amount': 1}).flags())

    def test_grant_components_contribute_no_flags(self):
        self.assertEqual([], comp('grant_skill', {'skills': ['Canto']}).flags())
        self.assertEqual([], comp('upgrade_items').flags())

    def test_custom_flag_coerces_its_text_value(self):
        def value_of(raw):
            return comp('custom_flag', {'key': 'k', 'value': raw, 'combine': 'max'}).flags()[0][1]
        self.assertEqual(2, value_of('2'))
        self.assertEqual(0.25, value_of('0.25'))
        self.assertIs(True, value_of('True'))
        self.assertIs(False, value_of('false'))
        self.assertEqual('Mage', value_of('Mage'))

    def test_custom_flag_with_no_key_contributes_nothing(self):
        self.assertEqual([], comp('custom_flag', {'key': '', 'value': '1'}).flags())

    def test_restored_components_do_not_share_state(self):
        # A NewMultipleOptions component rebuilds its dict, and a List component copies,
        # so two restores of the same nid must not alias one another.
        a = comp('grant_skill', {'skills': ['Canto']})
        b = comp('grant_skill', {'skills': ['Vantage']})
        self.assertEqual(['Canto'], a.value['skills'])
        self.assertEqual(['Vantage'], b.value['skills'])
        c, d = comp('draft_unlock', ['Mage']), comp('draft_unlock', ['Cleric'])
        c.value.append('Monk')
        self.assertEqual(['Cleric'], d.value)


class CanUnlockTests(_TechTestCaseMixin, unittest.TestCase):
    def test_requires_prerequisite(self):
        self.assertFalse(tech_funcs.can_unlock(self.team, 'SteelWeapons'))
        self.unlock('IronWeapons')
        self.assertTrue(tech_funcs.can_unlock(self.team, 'SteelWeapons'))

    def test_requires_enough_renown(self):
        self.team.renown = 99
        self.assertFalse(tech_funcs.can_unlock(self.team, 'IronWeapons'))
        self.team.renown = 100
        self.assertTrue(tech_funcs.can_unlock(self.team, 'IronWeapons'))

    def test_already_owned_is_not_unlockable(self):
        self.unlock('IronWeapons')
        self.assertFalse(tech_funcs.can_unlock(self.team, 'IronWeapons'))

    def test_failing_condition_blocks(self):
        self.assertFalse(tech_funcs.can_unlock(self.team, 'NeverUnlockable'))

    def test_unknown_tech_is_not_unlockable(self):
        self.assertFalse(tech_funcs.can_unlock(self.team, 'NotATech'))


class UnlockTechActionTests(_TechTestCaseMixin, unittest.TestCase):
    def test_unlock_charges_renown_and_records_tech(self):
        self.unlock('IronWeapons')
        self.assertEqual(['IronWeapons'], self.team.research)
        self.assertEqual(900, self.team.renown)
        self.assertTrue(tech_funcs.has_tech(self.team, 'IronWeapons'))

    def test_free_flag_skips_the_renown_payment(self):
        self.unlock('IronWeapons', free=True)
        self.assertEqual(['IronWeapons'], self.team.research)
        self.assertEqual(1000, self.team.renown)
        self.assertEqual(1, tech_funcs.get_tech_value(self.team, 'weapon_tier'))

    def test_unlock_is_not_gated_on_can_unlock(self):
        # No prerequisite, and not enough renown: the action forces it anyway.
        self.team.renown = 0
        self.assertFalse(tech_funcs.can_unlock(self.team, 'SteelWeapons'))
        self.unlock('SteelWeapons')
        self.assertTrue(tech_funcs.has_tech(self.team, 'SteelWeapons'))
        self.assertEqual(-250, self.team.renown)

    def test_unlock_is_idempotent(self):
        self.unlock('IronWeapons')
        self.unlock('IronWeapons')
        self.assertEqual(['IronWeapons'], self.team.research)
        self.assertEqual(900, self.team.renown)

    def test_unknown_tech_is_a_no_op(self):
        self.unlock('NotATech')
        self.assertEqual([], self.team.research)
        self.assertEqual(1000, self.team.renown)

    def test_reversing_a_redundant_unlock_leaves_the_first_one_standing(self):
        # Two unlocks of the same tech (a UI unlock then a scripted one, say). The second
        # is a no-op, so turnwheeling back over it must not strip the nid off `research`
        # while the first unlock's renown payment and effects are still applied.
        first = action.UnlockTech(self.team, 'CityCap1')
        action.do(first)
        second = action.UnlockTech(self.team, 'CityCap1')
        action.do(second)
        second.reverse()
        self.assertEqual(['CityCap1'], self.team.research)
        self.assertEqual(850, self.team.renown)
        self.assertEqual(5, tech_funcs.get_tech_value(self.team, 'city_pop_bonus'))

    def test_reversing_an_unknown_tech_unlock_touches_nothing(self):
        act = action.UnlockTech(self.team, 'NotATech')
        action.do(act)
        act.reverse()
        self.assertEqual([], self.team.research)
        self.assertEqual(1000, self.team.renown)

    def test_executing_a_redundant_unlock_does_not_re_record_it(self):
        first = action.UnlockTech(self.team, 'CityCap1')
        action.do(first)
        second = action.UnlockTech(self.team, 'CityCap1')
        action.do(second)
        second.reverse()
        second.execute()
        self.assertEqual(['CityCap1'], self.team.research)
        self.assertEqual(850, self.team.renown)

    def test_reverse_refunds_and_drops_the_tech(self):
        act = action.UnlockTech(self.team, 'CityCap1')
        action.do(act)
        self.assertEqual(5, tech_funcs.get_tech_value(self.team, 'city_pop_bonus'))
        act.reverse()
        self.assertEqual([], self.team.research)
        self.assertEqual(1000, self.team.renown)
        self.assertEqual(0, tech_funcs.get_tech_value(self.team, 'city_pop_bonus'))

    def test_execute_redoes_after_reverse(self):
        act = action.UnlockTech(self.team, 'CityCap1')
        action.do(act)
        act.reverse()
        act.execute()
        self.assertEqual(['CityCap1'], self.team.research)
        self.assertEqual(850, self.team.renown)
        self.assertEqual(5, tech_funcs.get_tech_value(self.team, 'city_pop_bonus'))

    def test_reverse_of_a_free_unlock_does_not_refund(self):
        act = action.UnlockTech(self.team, 'IronWeapons', free=True)
        action.do(act)
        act.reverse()
        self.assertEqual([], self.team.research)
        self.assertEqual(1000, self.team.renown)

    def test_change_renown_action_reverses(self):
        act = action.ChangeRenown(self.team, -400)
        action.do(act)
        self.assertEqual(600, self.team.renown)
        act.reverse()
        self.assertEqual(1000, self.team.renown)

    def test_tech_is_recorded_before_effects_are_built(self):
        # upgrade_items reads weapon_tier while UnlockTech builds its sub-actions,
        # so the tech must already be in team.research by then or the sweep reads
        # the stale, pre-unlock tier.
        seen = []
        tech = make_tech('TierAndSweep', 'Tier And Sweep', cost=0,
                         components=[comp('weapon_tier', 3), comp('upgrade_items')])
        DB.techs.append(tech)
        self.techs.append(tech)
        real_get_grant_target_units = tech_funcs.get_grant_target_units

        def spy(team, grant_target, grant_target_arg=''):
            seen.append(self.game.get_tech_value(team, 'weapon_tier'))
            return real_get_grant_target_units(team, grant_target, grant_target_arg)

        tech_funcs.get_grant_target_units = spy
        try:
            self.unlock('TierAndSweep')
        finally:
            tech_funcs.get_grant_target_units = real_get_grant_target_units
        self.assertEqual([3], seen)


class GrantSkillTests(_TechTestCaseMixin, unittest.TestCase):
    """A grant_skill component holds a *list* of skills, so one tech can grant several."""

    def setUp(self):
        super().setUp()
        from app.engine.objects.unit import UnitObject
        prefab = DB.units[0]
        self.unit = UnitObject.from_prefab(prefab, new_nid='TechGrantTestUnit')
        self.unit.team = 'player'
        self.game.register_unit(self.unit)

    def tearDown(self):
        self.game.unregister_unit(self.unit)
        super().tearDown()

    def _add_grant_tech(self, skills, target='team_units', arg=None):
        tech = make_tech('GrantsSkills', 'Grants Skills', cost=0,
                         components=[comp('grant_skill', {'skills': skills,
                                                          'grant_target': target,
                                                          'grant_target_arg': arg})])
        DB.techs.append(tech)
        self.techs.append(tech)
        return tech

    def test_unlock_grants_every_skill_in_the_list(self):
        self._add_grant_tech(['Canto', 'Fort'])
        self.unlock('GrantsSkills')
        nids = [s.nid for s in self.unit.skills]
        self.assertIn('Canto', nids)
        self.assertIn('Fort', nids)

    def test_reverse_removes_every_granted_skill(self):
        self._add_grant_tech(['Canto', 'Fort'])
        act = action.UnlockTech(self.team, 'GrantsSkills')
        action.do(act)
        act.reverse()
        nids = [s.nid for s in self.unit.skills]
        self.assertNotIn('Canto', nids)
        self.assertNotIn('Fort', nids)

    def test_grant_target_tag_skips_units_without_the_tag(self):
        self._add_grant_tech(['Canto'], target='units_with_tag', arg='NotARealTagAnywhere')
        self.unlock('GrantsSkills')
        self.assertNotIn('Canto', [s.nid for s in self.unit.skills])

    def test_get_tech_skills_re_derives_the_whole_list_for_a_new_unit(self):
        self._add_grant_tech(['Canto', 'Fort'])
        self.unlock('GrantsSkills')
        from app.engine.objects.unit import UnitObject
        newcomer = UnitObject.from_prefab(DB.units[0], new_nid='TechGrantNewcomer')
        newcomer.team = 'player'
        nids = [s.nid for s in tech_funcs.get_tech_skills(newcomer)]
        self.assertIn('Canto', nids)
        self.assertIn('Fort', nids)


class CityPopBonusTests(_TechTestCaseMixin, unittest.TestCase):
    """city_pop_bonus reaches cities two ways: existing ones are topped up by the unlock
    (reversibly), later ones read the flag when they are built from their prefab."""

    def setUp(self):
        super().setUp()
        self.city = self._make_city('TechPopTestCity', 'player', 3)
        self.game.register_city(self.city)

    def tearDown(self):
        self.game.city_registry.pop(self.city.nid, None)
        super().tearDown()

    def _make_city(self, nid, team, population):
        from app.data.cities import City
        from app.engine.objects.city import CityObject
        prefab = City(nid)
        prefab.team = team
        prefab.population = population
        return CityObject.from_prefab(prefab)

    def test_unlock_raises_population_of_cities_the_team_already_owns(self):
        self.unlock('CityCap1')
        self.assertEqual(8, self.city.population)

    def test_bonus_stacks_across_techs(self):
        self.unlock('CityCap1')
        self.unlock('CityCap2')
        self.assertEqual(13, self.city.population)

    def test_reverse_takes_the_population_back(self):
        act = action.UnlockTech(self.team, 'CityCap1')
        action.do(act)
        act.reverse()
        self.assertEqual(3, self.city.population)

    def test_another_teams_city_is_untouched(self):
        enemy_city = self._make_city('TechPopTestEnemyCity', 'enemy', 3)
        self.game.register_city(enemy_city)
        try:
            self.unlock('CityCap1')
            self.assertEqual(3, enemy_city.population)
        finally:
            self.game.city_registry.pop(enemy_city.nid, None)

    def test_a_city_built_after_the_unlock_starts_with_the_bonus(self):
        self.unlock('CityCap1')
        later = self._make_city('TechPopTestLaterCity', 'player', 3)
        self.assertEqual(8, later.population)
        # ...and only once: the unlock sweep already ran, so it is not also topped up
        self.assertEqual(8, later.population)


class TechSerializationTests(unittest.TestCase):
    """Round-tripping the component shape, and reading the legacy `effects` shape."""

    @classmethod
    def setUpClass(cls):
        DB.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)

    def test_component_round_trip(self):
        tech = make_tech('MageTraining', 'Mage Training', cost=200,
                         requires=['IronWeapons'], conditions=['True'],
                         components=[comp('draft_unlock', ['Mage', 'Monk']),
                                     comp('upkeep_cost_reduction',
                                          {'unit_tag': 'Mounted', 'amount': 2}),
                                     comp('grant_skill',
                                          {'skills': ['Canto', 'Fort'],
                                           'grant_target': 'units_with_tag',
                                           'grant_target_arg': 'Mounted'})])
        restored = TechPrefab.restore(tech.save())
        self.assertEqual('MageTraining', restored.nid)
        self.assertEqual(200, restored.renown_cost)
        self.assertEqual(['IronWeapons'], restored.requires)
        self.assertEqual(['True'], restored.conditions)
        self.assertIsInstance(restored.icon_index, tuple)
        self.assertEqual(['draft_unlock', 'upkeep_cost_reduction', 'grant_skill'],
                         [c.nid for c in restored.components])
        self.assertEqual(['Mage', 'Monk'], restored.components.get('draft_unlock').value)
        self.assertEqual([('upkeep_cost_Mounted', 2, Combine.SUM)],
                         restored.components.get('upkeep_cost_reduction').flags())
        grant = restored.components.get('grant_skill')
        self.assertEqual(['Canto', 'Fort'], grant.skills)
        self.assertEqual(GrantTarget.UNITS_WITH_TAG, grant.grant_target)
        self.assertEqual('Mounted', grant.grant_target_arg)

    def test_round_trip_does_not_alias_the_saved_value(self):
        tech = make_tech('T', components=[comp('draft_unlock', ['Mage'])])
        saved = tech.save()
        restored = TechPrefab.restore(saved)
        restored.components.get('draft_unlock').value.append('Monk')
        self.assertEqual(['Mage'], saved['components'][0][1])

    def test_component_prefab_is_accessible_by_nid(self):
        tech = make_tech('T', components=[comp('weapon_tier', 2)])
        self.assertEqual(2, tech['weapon_tier'].value)
        self.assertIsNone(tech['draft_unlock'])


class LegacyEffectMigrationTests(unittest.TestCase):
    """A project written before effects became components still has an `effects` list on
    disk. It must load into the equivalent components, producing the same flag keys."""

    @classmethod
    def setUpClass(cls):
        DB.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)

    def restore_legacy(self, effects, **kwargs):
        dat = {'nid': 'Legacy', 'renown_cost': 0, 'effects': effects}
        dat.update(kwargs)
        return TechPrefab.restore(dat)

    def flags_of(self, tech):
        return [f for c in tech.components for f in c.flags()]

    def test_legacy_fixed_key_flag(self):
        # 'city_pop_cap_bonus' is also the one legacy key that was renamed - it must land
        # on the component that replaced it rather than degrading to a CustomFlag.
        tech = self.restore_legacy([{'kind': 'flag', 'key': 'city_pop_cap_bonus',
                                     'value': 5, 'combine': 'sum'}])
        self.assertEqual(['city_pop_bonus'], [c.nid for c in tech.components])
        self.assertEqual([('city_pop_bonus', 5, Combine.SUM)], self.flags_of(tech))

    def test_legacy_set_flags_merge_into_one_component(self):
        tech = self.restore_legacy([
            {'kind': 'flag', 'key': 'draft_unlock', 'value': 'Mage', 'combine': 'set'},
            {'kind': 'flag', 'key': 'draft_unlock', 'value': 'Cleric', 'combine': 'set'},
            {'kind': 'flag', 'key': 'build_unlock', 'value': 'Library', 'combine': 'set'},
        ])
        self.assertEqual(['draft_unlock', 'build_unlock'], [c.nid for c in tech.components])
        self.assertEqual(['Mage', 'Cleric'], tech.components.get('draft_unlock').value)

    def test_legacy_parameterized_keys(self):
        tech = self.restore_legacy([
            {'kind': 'flag', 'key': 'farm_resource_bonus', 'value': 1, 'combine': 'sum'},
            {'kind': 'flag', 'key': 'upkeep_cost_Mounted', 'value': 1, 'combine': 'sum'},
        ])
        self.assertEqual(['resource_bonus', 'upkeep_cost_reduction'],
                         [c.nid for c in tech.components])
        self.assertEqual([('farm_resource_bonus', 1, Combine.SUM),
                          ('upkeep_cost_Mounted', 1, Combine.SUM)], self.flags_of(tech))

    def test_legacy_unwired_key_becomes_a_custom_flag(self):
        tech = self.restore_legacy([{'kind': 'flag', 'key': 'hero_pool_tier',
                                     'value': 2, 'combine': 'max'}])
        self.assertEqual(['custom_flag'], [c.nid for c in tech.components])
        self.assertEqual([('hero_pool_tier', 2, Combine.MAX)], self.flags_of(tech))

    def test_legacy_grant_skill_becomes_a_one_element_list(self):
        tech = self.restore_legacy([{'kind': 'grant_skill', 'skill_nid': 'Canto',
                                     'grant_target': 'units_with_tag',
                                     'grant_target_arg': 'Mounted'}])
        grant = tech.components.get('grant_skill')
        self.assertEqual(['Canto'], grant.skills)
        self.assertEqual(GrantTarget.UNITS_WITH_TAG, grant.grant_target)
        self.assertEqual('Mounted', grant.grant_target_arg)

    def test_legacy_upgrade_items(self):
        tech = self.restore_legacy([{'kind': 'upgrade_items', 'grant_target': 'team_units'}])
        self.assertEqual(GrantTarget.TEAM_UNITS,
                         tech.components.get('upgrade_items').grant_target)

    def test_components_key_wins_over_a_legacy_effects_key(self):
        tech = TechPrefab.restore({'nid': 'T', 'components': [['weapon_tier', 3]],
                                   'effects': [{'kind': 'flag', 'key': 'weapon_tier',
                                                'value': 1, 'combine': 'max'}]})
        self.assertEqual([('weapon_tier', 3, Combine.MAX)], self.flags_of(tech))

    @unittest.skipUnless(os.path.exists(AVALON_TECHS), 'avalon project not checked out')
    def test_the_real_avalon_catalog_migrates_with_identical_flag_keys(self):
        """The 20 hand-authored avalon techs are the ground truth for this migration:
        every flag key they produced before must still be produced, modulo the keys that
        were deliberately renamed (RENAMED_KEYS)."""
        with open(AVALON_TECHS) as f:
            raw = json.load(f)
        expected = {}
        for dat in raw:
            keys = set()
            for effect in dat['effects']:
                if effect.get('kind', 'flag') == 'flag':
                    keys.add(RENAMED_KEYS.get(effect['key'], effect['key']))
            expected[dat['nid']] = keys

        self.assertEqual(20, len(raw))
        for dat in raw:
            tech = TechPrefab.restore(dat)
            got = {key for c in tech.components for key, _, _ in c.flags()}
            self.assertEqual(expected[dat['nid']], got, tech.nid)
            # Nothing may be dropped: a flag-less tech must still carry its grant component
            self.assertEqual(len([e for e in dat['effects']
                                  if e.get('kind', 'flag') != 'flag']),
                             len([c for c in tech.components if not c.flags()]),
                             tech.nid)


class TechGatedValueTests(_TechTestCaseMixin, unittest.TestCase):
    """city_funcs derives the tech-locked class/building nids from DB.techs itself."""

    def test_gated_values_read_list_valued_set_components(self):
        from app.engine import city_funcs
        DB.techs.get('MageTraining').components.get('draft_unlock').value = ['Mage', 'Monk']
        self.assertEqual({'Mage', 'Monk', 'Cleric'}, city_funcs._tech_gated_values('draft_unlock'))
        self.assertEqual({'Library'}, city_funcs._tech_gated_values('build_unlock'))

    def test_a_nid_no_tech_mentions_is_not_gated(self):
        from app.engine import city_funcs
        self.assertNotIn('Brigand', city_funcs._tech_gated_values('draft_unlock'))


class TechEventFunctionTests(_TechTestCaseMixin, unittest.TestCase):
    """Phase 5: the `add_renown` and `unlock_tech` event commands."""

    def _make_fake_event(self):
        fake_event = MagicMock()
        fake_event.game = self.game  # the real singleton -- action.py reads it too
        fake_event.logger = MagicMock()
        return fake_event

    def test_add_renown_grants_and_logs_action(self):
        fake_event = self._make_fake_event()
        before_len = len(self.game.action_log.actions)

        event_functions.add_renown(fake_event, 'player', 150)

        self.assertEqual(1150, self.team.renown)
        self.assertEqual(before_len + 1, len(self.game.action_log.actions))
        self.assertIsInstance(self.game.action_log.actions[-1], action.ChangeRenown)
        fake_event.logger.error.assert_not_called()

    def test_add_renown_accepts_a_negative_amount(self):
        fake_event = self._make_fake_event()
        event_functions.add_renown(fake_event, 'player', -400)
        self.assertEqual(600, self.team.renown)

    def test_add_renown_rejects_an_unknown_team(self):
        fake_event = self._make_fake_event()
        event_functions.add_renown(fake_event, 'not_a_team', 150)
        self.assertEqual(1000, self.team.renown)
        fake_event.logger.error.assert_called()

    def test_unlock_tech_unlocks_and_logs_action(self):
        fake_event = self._make_fake_event()
        before_len = len(self.game.action_log.actions)

        event_functions.unlock_tech(fake_event, 'player', 'IronWeapons')

        self.assertTrue(tech_funcs.has_tech(self.team, 'IronWeapons'))
        self.assertEqual(900, self.team.renown)
        self.assertEqual(before_len + 1, len(self.game.action_log.actions))
        self.assertIsInstance(self.game.action_log.actions[-1], action.UnlockTech)
        fake_event.logger.error.assert_not_called()

    def test_unlock_tech_free_flag_skips_the_cost(self):
        fake_event = self._make_fake_event()
        event_functions.unlock_tech(fake_event, 'player', 'IronWeapons', flags={'free'})
        self.assertTrue(tech_funcs.has_tech(self.team, 'IronWeapons'))
        self.assertEqual(1000, self.team.renown)

    def test_unlock_tech_forces_past_prerequisites(self):
        fake_event = self._make_fake_event()
        event_functions.unlock_tech(fake_event, 'player', 'SteelWeapons')
        self.assertTrue(tech_funcs.has_tech(self.team, 'SteelWeapons'))
        self.assertFalse(tech_funcs.has_tech(self.team, 'IronWeapons'))
        self.assertEqual(2, tech_funcs.get_tech_value(self.team, 'weapon_tier'))

    def test_unlock_tech_rejects_an_unknown_team(self):
        fake_event = self._make_fake_event()
        event_functions.unlock_tech(fake_event, 'not_a_team', 'IronWeapons')
        self.assertEqual([], self.team.research)
        fake_event.logger.error.assert_called()

    def test_unlock_tech_rejects_an_unknown_tech(self):
        fake_event = self._make_fake_event()
        event_functions.unlock_tech(fake_event, 'player', 'NotATech')
        self.assertEqual([], self.team.research)
        self.assertEqual(1000, self.team.renown)
        fake_event.logger.error.assert_called()

    def test_classic_parse_path(self):
        # Mirror event.py's run_command: parse the raw command text,
        # convert_parse it, snake-case the keys, call.
        command, _ = event_commands.parse_text_to_command('unlock_tech;player;IronWeapons;free')
        parameters, flags = event_commands.convert_parse(command, None)
        parameters = {str_utils.camel_to_snake(k): v for k, v in parameters.items()}
        self.assertEqual({'team': 'player', 'tech': 'IronWeapons'}, parameters)
        self.assertIn('free', flags)

        fake_event = self._make_fake_event()
        event_functions.unlock_tech(fake_event, **parameters, flags=flags)
        self.assertTrue(tech_funcs.has_tech(self.team, 'IronWeapons'))
        self.assertEqual(1000, self.team.renown)

    def test_add_renown_classic_parse_path_converts_to_int(self):
        command, _ = event_commands.parse_text_to_command('add_renown;player;150')
        parameters, flags = event_commands.convert_parse(command, None)
        parameters = {str_utils.camel_to_snake(k): v for k, v in parameters.items()}
        self.assertIsInstance(parameters['renown'], int)

        fake_event = self._make_fake_event()
        event_functions.add_renown(fake_event, **parameters, flags=flags)
        self.assertEqual(1150, self.team.renown)


class TechValidatorTests(_TechTestCaseMixin, unittest.TestCase):
    def test_tech_validator_accepts_known_nids_only(self):
        validator = event_validators.get('Tech')(DB, RESOURCES)
        self.assertEqual('IronWeapons', validator.validate('IronWeapons', None))
        self.assertIsNone(validator.validate('NotATech', None))

    def test_tech_validator_lists_every_tech(self):
        validator = event_validators.get('Tech')(DB, RESOURCES)
        entries = [nid for _, nid in validator.valid_entries()]
        self.assertIn('IronWeapons', entries)
        self.assertIn('MageTraining', entries)


if __name__ == '__main__':
    unittest.main()
