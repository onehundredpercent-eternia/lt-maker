from app.resources.resources import RESOURCES

from app.data.item_components import ItemComponent, ItemTags
from app.data.components import Type

from app.utilities import utils
from app.engine import target_system, skill_system, action, equations
from app.engine.combat import playback as pb
from app.engine.animations import MapAnimation
from app.engine.game_state import game 

class MementoEnemyCleaveAOE(ItemComponent):
    nid = 'memento_enemy_cleave_aoe'
    desc = "Gives Enemy Memento Cleave AOE"
    tag = ItemTags.CUSTOM

    def splash(self, unit, item, position) -> tuple:
        pos = unit.position
        x_diff = position[0] - pos[0]
        y_diff = position[1] - pos[1]
        if x_diff in (1, -1):
            splash_positions = {(position[0], position[1] - 1), (position[0], position[1] + 1)}
        elif y_diff in (1, -1):
            splash_positions = {(position[0] - 1, position[1]), (position[0] + 1, position[1])}
        else:
            splash_positions = set()
        
        splash_positions = {pos for pos in splash_positions if game.tilemap.check_bounds(pos)}
        splash = [game.board.get_unit(pos) for pos in splash_positions]
        splash = [s.position for s in splash if s and skill_system.check_enemy(unit, s)]
        main_target = position if game.board.get_unit(position) else None
        return main_target, splash

    def splash_positions(self, unit, item, position) -> set:
        pos = unit.position
        x_diff = position[0] - pos[0]
        y_diff = position[1] - pos[1]
        if x_diff in (1, -1):
            splash_positions = {(position[0], position[1] - 1), (position[0], position[1] + 1)}
        elif y_diff in (1, -1):
            splash_positions = {(position[0] - 1, position[1]), (position[0] + 1, position[1])}
        else:
            splash_positions = set()
        
        splash_positions = {pos for pos in splash_positions if game.tilemap.check_bounds(pos)}
        # Doesn't highlight allies positions
        splash = {pos for pos in splash_positions if not game.board.get_unit(pos) or skill_system.check_enemy(unit, game.board.get_unit(pos))}
        return splash

class MementoEnemyPierceAOE(ItemComponent):
    nid = 'memento_enemy_pierce_aoe'
    desc = "Gives Enemy Memento Pierce AOE"
    tag = ItemTags.CUSTOM

    def splash(self, unit, item, position) -> tuple:
        pos = unit.position
        x_diff = position[0] - pos[0]
        y_diff = position[1] - pos[1]
        splash_positions = {(position[0] + x_diff, position[1] + y_diff)}

        splash_positions = {pos for pos in splash_positions if game.tilemap.check_bounds(pos)}
        splash = [game.board.get_unit(pos) for pos in splash_positions]
        splash = [s.position for s in splash if s and skill_system.check_enemy(unit, s)]
        main_target = position if game.board.get_unit(position) else None
        return main_target, splash

    def splash_positions(self, unit, item, position) -> set:
        pos = unit.position
        x_diff = position[0] - pos[0]
        y_diff = position[1] - pos[1]
        splash_positions = {(position[0] + x_diff, position[1] + y_diff)}

        splash_positions = {pos for pos in splash_positions if game.tilemap.check_bounds(pos)}
        # Doesn't highlight allies positions
        splash = {pos for pos in splash_positions if not game.board.get_unit(pos) or skill_system.check_enemy(unit, game.board.get_unit(pos))}
        return splash

class MementoBurstAOE(ItemComponent):
    nid = 'memento_burst_aoe'
    desc = "Gives Memento Burst AOE"
    tag = ItemTags.CUSTOM

    expose = Type.Int
    value = 1

    def splash(self, unit, item, position) -> tuple:
        pos = unit.position
        x_diff = position[0] - pos[0]
        y_diff = position[1] - pos[1]
        if x_diff in (1, -1):
            splash_positions = {(position[0], position[1] - 1), (position[0], position[1] + 1)}
        elif y_diff in (1, -1):
            splash_positions = {(position[0] - 1, position[1]), (position[0] + 1, position[1])}
        else:
            splash_positions = set()
        
        splash_positions = {pos for pos in splash_positions if game.tilemap.check_bounds(pos)}
        splash = [game.board.get_unit(pos) for pos in splash_positions]
        splash = [s.position for s in splash if s and skill_system.check_enemy(unit, s)]
        main_target = position if game.board.get_unit(position) else None
        return main_target, splash

    def splash_positions(self, unit, item, position) -> set:
        unit_pos = unit.position
        splash_positions = {
            (unit_pos[0], unit_pos[1] - 1),
            (unit_pos[0], unit_pos[1] + 1),
            (unit_pos[0] - 1, unit_pos[1]),
            (unit_pos[0] + 1, unit_pos[1])
        }
        
        splash_positions = {pos for pos in splash_positions if game.tilemap.check_bounds(pos)}
        return splash_positions

class MementoPull(ItemComponent):
    nid = 'memento_pull'
    desc = "Item moves target toward user on hit, and if it cannot, applies this status instead"
    tag = ItemTags.CUSTOM

    expose = Type.Skill

    def _pull(self, user, target, magnitude: int) -> tuple:
        offset_x = utils.clamp(target.position[0] - user.position[0], -1, 1)
        offset_y = utils.clamp(target.position[1] - user.position[1], -1, 1)
        new_position_target = (target.position[0] - offset_x * magnitude,
                               target.position[1] - offset_y * magnitude)

        mcost_target = game.movement.get_mcost(target, new_position_target)

        if game.tilemap.check_bounds(new_position_target) and \
                not game.board.get_unit(new_position_target) and \
                mcost_target <= equations.parser.movement(target):
            return new_position_target
        return None

    def end_combat(self, playback, unit, item, target, mode):
        if not skill_system.ignore_forced_movement(target):
            new_position_target = self._pull(unit, target, 1)
            if new_position_target:
                action.do(action.ForcedMovement(target, new_position_target))
                playback.append(pb.ShoveHit(unit, item, target))
            else:  # Immobilize Status
                action.do(action.AddSkill(target, self.value, unit))

class MementoRallyStatus(ItemComponent):
    nid = 'memento_rally_status'
    desc = "Item gives this status to nearby allies after combat"
    tag = ItemTags.CUSTOM

    expose = Type.Skill
    distance = 2

    def end_combat(self, playback, unit, item, target, mode):
        if unit.dead or unit.is_dying:
            return
        # Only do this if you actually attempted to attack
        mark_playbacks = [p for p in playback if p.nid in ('mark_miss', 'mark_hit', 'mark_crit')]
        if any(p.attacker is unit for p in mark_playbacks):
            pass
        else:
            return

        for other in game.get_all_units():
            if other is not unit and other.team == unit.team and utils.calculate_distance(other.position, unit.position) <= self.distance:
                playback.append(pb.StatusHit(unit, item, other, self.value))
                action.do(action.AddSkill(other, self.value, unit))
                # A E S T H E T I C
                other.sprite.begin_flicker(200, (255, 255, 255))

        # Display Rally Sprite
        anim_nid = 'AOE_Rally'
        anim = RESOURCES.animations.get(anim_nid)
        if anim:
            anim = MapAnimation(anim, unit.position)
            game.tilemap.animations.append(anim)

class MementoRallyHeals(ItemComponent):
    nid = 'memento_rally_heal'
    desc = "Item heals this amount to nearby allies after combat"
    tag = ItemTags.CUSTOM

    expose = Type.Int
    value = 10
    distance = 2

    def _get_heal_amount(self, unit, target):
        empower_heal = skill_system.empower_heal(unit, target)
        empower_heal_received = skill_system.empower_heal_received(target, unit)
        return self.value + equations.parser.heal(unit) + empower_heal + empower_heal_received

    def end_combat(self, playback, unit, item, target, mode):
        from app.engine import gui

        if unit.dead or unit.is_dying:
            return
        # Only do this if you actually attempted to attack
        mark_playbacks = [p for p in playback if p.nid in ('mark_miss', 'mark_hit', 'mark_crit')]
        if any(p.attacker is unit for p in mark_playbacks):
            pass
        else:
            return
            
        for other in game.get_all_units():
            if other is not unit and other.team == unit.team and utils.calculate_distance(other.position, unit.position) <= self.distance:
                heal = self._get_heal_amount(unit, other)
                true_heal = min(heal, other.get_max_hp() - other.get_hp())
                playback.append(pb.HealHit(unit, item, other, heal, true_heal))
                action.do(action.ChangeHP(other, heal))
                # A E S T H E T I C
                other.sprite.begin_flicker(200, (96, 144, 232))
                str_damage = str(heal)
                for idx, num in enumerate(str_damage):
                    d = gui.DamageNumber(int(num, idx, len(str_damage), other.position, 'small_cyan'))
                    other.sprite.damage_numbers.append(d)

        # Display Rally Sprite
        anim_nid = 'AOE_Rally'
        anim = RESOURCES.animations.get(anim_nid)
        if anim:
            anim = MapAnimation(anim, unit.position)
            game.tilemap.animations.append(anim)

class MementoAnimaAvailable(ItemComponent):
    nid = 'memento_anima_available'
    desc = "Item can only be used when in the correct mode"
    tag = ItemTags.CUSTOM

    expose = Type.Item

    def available(self, unit, item) -> bool:
        for item in unit.items:
            if item.multi_item:
                first_subitem = item.subitems[0]
                if first_subitem.nid == self.value:
                    return True
        return False

class MementoFullMoonAvailable(ItemComponent):
    nid = 'memento_full_moon_available'
    desc = "Item can only be used when in full moon"
    tag = ItemTags.CUSTOM

    def available(self, unit, item) -> bool:
        return game.game_vars.get('full_moon', False)
