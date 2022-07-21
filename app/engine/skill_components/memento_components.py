from app.data.skill_components import SkillComponent, SkillTags
from app.data.components import Type

from app.utilities import utils
from app.engine import equations, action, item_funcs, static_random, skill_system, combat_calcs, target_system
from app.engine.combat import playback as pb
from app.engine.game_state import game

class MementoHitBonus(SkillComponent):
    nid = 'memento_hit_bonus'
    desc = "Gives out bonus to hit when another character can attack the same unit"
    tag = SkillTags.CUSTOM

    expose = Type.Int
    value = 10

    def dynamic_accuracy(self, unit, item, target, mode, attack_info, base_value):
        if mode == 'attack' and target and target.position:
            for other_unit in game.get_all_units():
                if other_unit is unit:
                    continue
                if skill_system.check_ally(unit, other_unit):
                    # Unit and other unit can both attack target
                    if target.position in target_system.get_attacks(other_unit, force=True):
                        return self.value
        return 0

class MementoShove(SkillComponent):
    nid = 'memento_shove'
    desc = "All attacks shove target after combat"
    tag = SkillTags.CUSTOM

    def _check_shove(self, unit_to_move, anchor_pos, magnitude):
        offset_x = utils.clamp(unit_to_move.position[0] - anchor_pos[0], -1, 1)
        offset_y = utils.clamp(unit_to_move.position[1] - anchor_pos[1], -1, 1)
        new_position = (unit_to_move.position[0] + offset_x,
                        unit_to_move.position[1] + offset_y)

        mcost = game.movement.get_mcost(unit_to_move, new_position)
        if game.tilemap.check_bounds(new_position) and \
                not game.board.get_unit(new_position) and \
                mcost < 99:
            return new_position
        return False

    """
    Do 1.5x damage when the unit would be shoved into an obstacle
    """
    # def damage_multiplier(self, unit, item, target, mode, attack_info, base_value):
    #     if not skill_system.ignore_forced_movement(target) and mode != 'splash':
    #         new_position = self._check_shove(target, unit.position, 1)
    #         if new_position:
    #             return 1
    #         else:
    #             return 1.5
    #     return 1

    def cleanup_combat(self, playback, unit, item, target, mode):
        marks = [mark for mark in playback if mark.nid in ('mark_hit', 'mark_crit') and mark.attacker is unit and mark.defender is target]
        did_hit = len(marks) > 0
        if did_hit and not skill_system.ignore_forced_movement(target) and mode != 'splash':
            new_position = self._check_shove(target, unit.position, 1)
            if new_position:
                action.do(action.ForcedMovement(target, new_position))
                playback.append(pb.ShoveHit(unit, item, target))

class MementoTempo(SkillComponent):
    nid = 'memento_tempo'
    desc = "Gives +4 DEF if attacked last player phase, +4 POW otherwise"
    tag = SkillTags.CUSTOM

    def init(self, skill):
        self.skill.data['_has_attacked'] = False
        self.skill.data['_last_turn'] = -1

    def end_combat(self, playback, attacker, main_item, defender, mode):
        if mode == 'attack' and defender and skill_system.check_enemy(attacker, defender):
            action.do(action.SetObjData(self.skill, '_has_attacked', True))

    def on_endstep(self, actions, playback, unit):
        if self.skill.data['_has_attacked']:
            action.do(action.SetObjData(self.skill, '_last_turn', game.turncount))
            action.do(action.SetObjData(self.skill, '_has_attacked', False))
        else:
            action.do(action.SetObjData(self.skill, '_last_turn', -1))
            
    def on_end_chapter(self, unit, skill):
        action.do(action.SetObjData(self.skill, '_last_turn', -1))

    def stat_change(self, unit) -> dict:
        if game.turncount > 0:
            if game.turncount > self.skill.data['_last_turn'] + 1:
                return {'POW': 4}
            else:
                return {'DEF': 4}
        return {}

class WitchWarp(SkillComponent):
    nid = 'witch_warp'
    desc = "Allows unit to witch warp to the given units"
    tag = SkillTags.CUSTOM

    expose = (Type.List, Type.Unit)

    def witch_warp(self, unit) -> list:
        positions = []
        for val in self.value:
            u = game.get_unit(val)
            if u and u.position:
                partner_pos = u.position
            else:
                continue
            if partner_pos:
                positions += target_system.get_adjacent_positions(partner_pos)
        return positions

class MementoAttackStanceDouble(SkillComponent):
    nid = 'memento_attack_stance_double'
    desc = "Unit will ALWAYS double while supporting in a pairup"
    tag = SkillTags.CUSTOM

    def attack_stance_double(self, unit) -> bool:
        return True

class MementoInitiateFullMoon(SkillComponent):
    nid = 'memento_initiate_full_moon'
    desc = "Unit can initiate and partake of full moon bonuses"
    tag = SkillTags.CUSTOM

    def init(self, skill):
        self.skill.data['_last_turn_with_kill'] = -1

    def _activate_full_moon(self, unit):
        action.do(action.ChangeField(unit, 'full_moon', True))
        # A E S T H E T I C

    def _deactivate_full_moon(self, unit):
        action.do(action.ChangeField(unit, 'full_moon', False))
        # A E S T H E T I C

    def keep_full_moon(self) -> bool:
        # You've gone a turn without killing anybody
        return self.skill.data['_last_turn_with_kill'] >= game.turncount - 2

    def on_upkeep(self, actions, playback, unit):
        if keep_full_moon():
            pass
        else:
            self._deactivate_full_moon(unit)
            
    def unit_sprite_flicker_tint(self, unit, skill):
        if unit.get_field('full_moon', False):
            return ((255, 255, 255), 900, 300)
        return None

    def end_combat(self, playback, unit, item, target, mode):
        playbacks = [p for p in playback if p.nid in ('damage_hit', 'damage_crit') and p.attacker == unit and \
                     (p.defender.is_dying or p.defender.dead)]
        if playbacks:
            self._activate_full_moon(unit)
            action.do(action.SetObjData(self.skill, '_last_turn_with_kill', game.turncount))

    def modify_damage(self, unit, item):
        return 2 if unit.get_field('full_moon', False) else 0

    def modify_accuracy(self, unit, item):
        return 20 if unit.get_field('full_moon', False) else 0

class MementoImmortal(SkillComponent):
    nid = 'memento_immortal'
    desc = "Unit ignores first damage taken each phase"
    tag = SkillTags.CUSTOM

    expose = Type.Int
    value = 1

    def init(self, skill):
        self.skill.data['charge'] = self.value
        self.skill.data['total_charge'] = self.value

    def after_take_hit(self, actions, playback, unit, item, target, mode, attack_info):
        if self.skill.data['charge'] > 0:
            # Remove any acts that reduce my HP!
            did_something = False
            for act in reversed(actions):
                if isinstance(act, action.ChangeHP) and act.num < 0 and act.unit == unit:
                    actions.remove(act)
                    did_something = True

            if did_something:
                actions.append(action.TriggerCharge(unit, self.skill))

    def on_end_chapter(self, unit, skill):
        self.skill.data['charge'] = self.skill.data['total_charge']

    def trigger_charge(self, unit, skill):
        new_value = self.skill.data['charge'] - 1
        action.do(action.SetObjData(self.skill, 'charge', new_value))

    def on_upkeep(self, actions, playback, unit):
        if self.skill.data['charge'] < self.skill.data['total_charge']:
            new_value = self.skill.data['total_charge']
            actions.append(action.SetObjData(self.skill, 'charge', new_value))

    def on_endstep(self, actions, playback, unit):
        if self.skill.data['charge'] < self.skill.data['total_charge']:
            new_value = self.skill.data['total_charge']
            actions.append(action.SetObjData(self.skill, 'charge', new_value))

class MementoRage(SkillComponent):
    nid = 'memento_rage'
    desc = "After killing an enemy, if under 50% hp, unit refreshes, heals to full, and gains skill."
    tag = SkillTags.CUSTOM

    expose = Type.Skill
    value = None

    def end_combat(self, playback, unit, item, target, mode):
        if target and target.get_hp() <= 0 and \
                unit.get_hp() < unit.get_max_hp() / 2. and \
                self.value not in [skill.nid for skill in unit.skills]:
            action.do(action.Reset(unit))
            action.do(action.SetHP(unit, unit.get_max_hp()))
            action.do(action.AddSkill(unit, self.value))
            action.do(action.TriggerCharge(unit, self.skill))

class MementoWitchTeleport(SkillComponent):
    nid = 'memento_witch_teleport'
    desc = "After taking damage, unit teleports away."
    tag = SkillTags.CUSTOM

    def after_take_hit(self, actions, playback, unit, item, target, mode, attack_info):
        # Check if we took damage
        damage = [p for p in playback if p.nid == 'damage_hit' and p.defender == unit and p.true_damage > 0]
        if damage and unit.position:
            valid_positions = [(x, y) for x in range(game.tilemap.width) for y in range(game.tilemap.height)]
            valid_positions = [pos for pos in valid_positions if not game.get_unit(pos) and utils.calculate_distance(pos, unit.position) and game.movement.check_weakly_traversable(unit, pos)]
            if valid_positions:
                pos = game.get_random_choice(valid_positions)
                actions.append(action.TriggerCharge(unit, self.skill))
                actions.append(action.Warp(unit, pos))
