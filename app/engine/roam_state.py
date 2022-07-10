from app.utilities import utils
from app.events.regions import RegionType

from app.engine.sound import get_sound_thread
from app.engine.state import MapState
from app.engine.game_state import game
from app.engine import engine, info_menu, evaluate, target_system, action, ai_controller, skill_system, equations
from app.engine.input_manager import get_input_manager
from app.data.database import DB

import logging

class FreeRoamState(MapState):
    name = 'free_roam'

    def start(self):
        self.roam_unit = None
        self.last_move = 0

        # speed and direction variables
        self.speed = 0.00
        self.vspeed = 0.0
        self.hspeed = 0.0
        self.direction = [0, 0]

        # AI manager
        self.ai_handler = FreeRoamAIHandler()

    def begin(self):
        game.cursor.hide()

        if game.level.roam and game.level.roam_unit:
            roam_unit_nid = game.level.roam_unit
            if self.roam_unit and self.roam_unit.nid != roam_unit_nid:
                self.rationalize()  # Rationalize original unit
                # Now get the new one
                self.roam_unit = game.get_unit(roam_unit_nid)
                game.cursor.cur_unit = self.roam_unit
                # Roam unit is no longer consider to be on the board
                game.leave(self.roam_unit)
            elif self.roam_unit:
                # Don't need to do anything --  just reusing the same unit
                pass
            elif game.get_unit(roam_unit_nid):
                self.roam_unit = game.get_unit(roam_unit_nid)
                game.cursor.cur_unit = self.roam_unit
                # Roam unit is no longer consider to be on the board
                game.leave(self.roam_unit)
            else:
                logging.error("Roam State unable to find roaming unit %s", roam_unit_nid)

        elif self.roam_unit:  # Have a roam unit and we shouldn't...
            # No roam unit assigned, time to go
            self.rationalize()

        if not self.roam_unit or not self.roam_unit.position:
            game.level.roam = False
            # Leave this state
            game.state.back()
            return 'repeat'

        rounded_pos = round(self.roam_unit.position[0]), round(self.roam_unit.position[1])
        game.cursor.set_pos(rounded_pos)

    def take_input(self, event):
        if not self.roam_unit:
            return

        base_speed = 0.008
        base_accel = 0.008
        running_accel = 0.01
        rounded_position = (round(self.roam_unit.position[0]), round(self.roam_unit.position[1]))

        if get_input_manager().is_pressed('BACK'):
            max_speed = 0.15
        else:
            max_speed = 0.1

        # Horizontal direction
        if (get_input_manager().is_pressed('LEFT') or get_input_manager().just_pressed('LEFT')) and self.roam_unit.position[0] > game.board.bounds[0]:
            self.last_move = engine.get_time()
            self.direction[0] = -5
        elif (get_input_manager().is_pressed('RIGHT') or get_input_manager().just_pressed('RIGHT')) and self.roam_unit.position[0] < game.board.bounds[2]:
            self.last_move = engine.get_time()
            self.direction[0] = 5

        if not get_input_manager().is_pressed('RIGHT') and self.direction[0] > 0:
            self.direction[0] -= 1

        if not get_input_manager().is_pressed('LEFT') and self.direction[0] < 0:
            self.direction[0] += 1

        # Vertical direction
        if (get_input_manager().is_pressed('UP') or get_input_manager().just_pressed('UP')) and self.roam_unit.position[1] > game.board.bounds[1]:
            self.last_move = engine.get_time()
            self.direction[1] = -5
        elif (get_input_manager().is_pressed('DOWN') or get_input_manager().just_pressed('DOWN')) and self.roam_unit.position[1] < game.board.bounds[3]:
            self.last_move = engine.get_time()
            self.direction[1] = 5

        if not get_input_manager().is_pressed('DOWN') and self.direction[1] > 0:
            self.direction[1] -= 1

        if not get_input_manager().is_pressed('UP') and self.direction[1] < 0:
            self.direction[1] += 1

        # Horizontal speed
        if self.direction[0] > 0 and self.can_move('RIGHT'):
            self.hspeed = self.speed
        elif self.direction[0] < 0 and self.can_move('LEFT'):
            self.hspeed = -self.speed
        else:
            self.hspeed = 0.0

        # Vertcal speed
        if self.direction[1] > 0 and self.can_move('DOWN'):
            self.vspeed = self.speed
        elif self.direction[1] < 0 and self.can_move('UP'):
            self.vspeed = -self.speed
        else:
            self.vspeed = 0.0

        # Actually move the unit
        if abs(self.hspeed) > base_speed or abs(self.vspeed) > base_speed:
            self.move(self.hspeed, self.vspeed)
            self.roam_unit.sprite.change_state('moving')
            self.roam_unit.sprite.handle_net_position((self.hspeed, self.vspeed))
            rounded_position = (round(self.roam_unit.position[0]), round(self.roam_unit.position[1]))

        game.camera.force_center(*self.roam_unit.position)

        if any((get_input_manager().just_pressed(direction) for direction in ('LEFT', 'RIGHT', 'UP', 'DOWN'))) \
                or any((get_input_manager().is_pressed(direction) for direction in ('LEFT', 'RIGHT', 'UP', 'DOWN'))):
            if self.speed < max_speed and get_input_manager().is_pressed('BACK'):
                self.speed += running_accel
            elif self.speed < max_speed:
                self.speed += base_accel
            elif self.speed > max_speed:
                self.speed -= running_accel
        elif self.speed >= base_speed or self.speed > max_speed:
            self.speed -= running_accel

        for region in game.level.regions:
            if region.contains(rounded_position) and region.interrupt_move:
                current_occupant = game.board.get_unit(rounded_position)
                if current_occupant:
                    rounded_position = target_system.get_nearest_open_tile(current_occupant, rounded_position)
                    self.roam_unit.position = rounded_position
                did_trigger = game.events.trigger('roaming_interrupt', self.roam_unit, position=self.roam_unit.position, local_args={'region': region})
                if did_trigger:
                    self.rationalize()
                if region.only_once and did_trigger:
                    action.do(action.RemoveRegion(region))

        if event == 'SELECT':
            other_unit = self.can_talk()
            region = self.can_visit()
            if other_unit:
                get_sound_thread().play_sfx('Select 2')
                did_trigger = game.events.trigger('on_talk', self.roam_unit, other_unit)
                if did_trigger:
                    action.do(action.RemoveTalk(self.roam_unit.nid, other_unit.nid))
                    self.rationalize()
            elif region:
                get_sound_thread().play_sfx('Select 2')
                did_trigger = game.events.trigger(region.sub_nid, self.roam_unit, position=self.roam_unit.position, local_args={'region': region})
                if did_trigger:
                    self.rationalize()
                if did_trigger and region.only_once:
                    action.do(action.RemoveRegion(region))
            else:
                get_sound_thread().play_sfx('Error')

        elif event == 'AUX':
            game.state.change('option_menu')

        elif event == 'INFO':
            other_unit = self.can_talk()
            did_trigger = game.events.trigger('roam_press_info', self.roam_unit, other_unit)
            if did_trigger:
                self.rationalize()
            else:
                info_menu.handle_info()

        elif event == 'START':
            did_trigger = game.events.trigger('roam_press_start', self.roam_unit)
            if did_trigger:
                get_sound_thread().play_sfx('Select 2')
                self.rationalize()
            else:
                get_sound_thread().play_sfx('Error')

    def update(self):
        super().update()
        self.ai_handler.update()
        if self.last_move and engine.get_time() - self.last_move > 166:
            self.last_move = 0
            self.roam_unit.sprite.change_state('normal')
            self.roam_unit.sound.stop()
            self.direction = [0, 0]

    def move(self, dx, dy):
        x, y = self.roam_unit.position
        self.roam_unit.position = x + dx, y + dy
        self.roam_unit.sound.play()
        rounded_pos = round(self.roam_unit.position[0]), round(self.roam_unit.position[1])
        game.cursor.set_pos(rounded_pos)

    def can_move(self, direc: str) -> bool:
        if direc == 'LEFT':
            check_x = int(round(self.roam_unit.position[0] - 0.4))
            check_y = int(round(self.roam_unit.position[1]))
            mcost = game.movement.get_mcost(self.roam_unit, (check_x, check_y))
            return mcost < 99 and self.no_bumps(check_x, check_y)
        elif direc == 'RIGHT':
            check_x = int(round(self.roam_unit.position[0] + 0.4))
            check_y = int(round(self.roam_unit.position[1]))
            mcost = game.movement.get_mcost(self.roam_unit, (check_x, check_y))
            return mcost < 99 and self.no_bumps(check_x, check_y)
        elif direc == 'UP':
            check_x = int(round(self.roam_unit.position[0]))
            check_y = int(round(self.roam_unit.position[1] - 0.4))
            mcost = game.movement.get_mcost(self.roam_unit, (check_x, check_y))
            return mcost < 99 and self.no_bumps(check_x, check_y)
        elif direc == 'DOWN':
            check_x = int(round(self.roam_unit.position[0]))
            check_y = int(round(self.roam_unit.position[1] + 0.4))
            mcost = game.movement.get_mcost(self.roam_unit, (check_x, check_y))
            return mcost < 99 and self.no_bumps(check_x, check_y)
        return True

    def no_bumps(self, x: int, y: int) -> bool:
        '''Used to detect if the space is occupied by an impassable unit'''
        new_pos = (x, y)
        if game.board.get_unit(new_pos):
            other_team = game.board.get_team(new_pos)
            if not other_team or utils.compare_teams(self.roam_unit.team, other_team):
                return True # Allies, this is fine
            else:  # Enemies
                return False
        return True

    def rationalize(self):
        """
        Done whenever the roam unit should be returned to a regular unit
        """
        new_pos = (int(round(self.roam_unit.position[0])), int(round(self.roam_unit.position[1])))
        current_occupant = game.board.get_unit(new_pos)
        if current_occupant:
            new_pos = target_system.get_nearest_open_tile(self.roam_unit, new_pos)
        self.roam_unit.position = new_pos
        game.arrive(self.roam_unit)
        self.roam_unit.sprite.change_state('normal')
        self.roam_unit.sound.stop()
        self.speed = 0
        self.vspeed = 0
        self.hspeed = 0
        self.roam_unit = None
        self.last_move = 0

    def can_talk(self):
        """
        Returns a unit if that unit is close enough to talk. Returns the closest unit if more than one is
        available, or None if not good targets
        """
        units = []
        for unit in game.units:
            if unit.position and unit is not self.roam_unit and self.roam_unit and \
                    utils.calculate_distance(self.roam_unit.position, unit.position) < 1:
                units.append(unit)
        units = list(sorted(units, key=lambda unit: utils.calculate_distance(self.roam_unit.position, unit.position)))
        if units:
            return units[0]
        return None

    def can_visit(self):
        """
        Returns first region that is close enough to visit
        """
        for region in game.level.regions:
            if region.region_type == RegionType.EVENT and region.fuzzy_contains(self.roam_unit.position):
                try:
                    truth = evaluate.evaluate(region.condition, self.roam_unit, position=self.roam_unit.position, local_args={'region': region})
                    if truth:
                        return region
                except Exception as e:
                    logging.error("%s: Could not evaluate {%s}" % (e, region.condition))
        return None

class FreeRoamAIHandler():
    """Handles and selects all valid units with AI in free roam
    Will:
        Maintain a list of valid units to check on
        Reload that list only when asked
        Iterate through that list to fulfill objective of each unit

    self.targets = Set[Units]
    """

    def __init__(self):
        self.targets = self.compose_target_list()

    def reload(self):
        self.targets = self.compose_target_list()

    def compose_target_list(self):
        targets = set()
        for unit in game.get_all_units():
            if hasattr(DB.ai.get(unit.get_ai()), 'roam_ai') and DB.ai.get(unit.get_ai()).roam_ai:
                targets.add(FreeRoamUnit(unit, FreeRoamAIController(unit)))
                game.leave(unit)
        return targets

    def update(self):
        for unit in self.targets:
            unit.ai.update()

class FreeRoamUnit():
    """A simple class focused on containing info
    for AI units in Free Roam"""
    def __init__(self, unit, ai):
        self.unit = unit
        self.ai = ai

class FreeRoamAIController(ai_controller.AIController):
    def __init__(self, unit):
        # Controls whether we should be skipping through the AI's turns
        self.do_skip: bool = False
        self.max_pause = 1000
        self.reset()
        self.unit = unit
        self.movement_manager = RoamMovementHandler(self.unit)

    def skip(self):
        self.do_skip = True

    def end_skip(self):
        self.do_skip = False

    def reset(self):
        self.unit = None
        self.state = "Init"

        self.behaviour_idx = 0
        self.behaviour = None
        self.inner_ai = None

        self.did_something = False
        self.pause = self.max_pause

        self.goal_position = None
        self.path = None

    def clean_up(self):
        self.goal_position = None
        self.goal_item = None
        self.goal_target = None

    def set_next_behaviour(self):
        behaviours = DB.ai.get(self.unit.get_ai()).behaviours
        if self.behaviour_idx < len(behaviours):
            self.behaviour = behaviours[self.behaviour_idx]
            self.behaviour_idx += 1
        else:
            self.behaviour = None
            self.behaviour_idx = 0

    def load_unit(self, unit):
        self.reset()
        self.unit = unit

    def update(self):
        self.think()

    def get_move_path(self):
        """Finds the path from the unit's position to the target
        Ideally called rarely"""
        return target_system.get_path(self.unit, self.goal_position, rationalize=True)[:-1]

    def move(self):
        """Called every update. Calls the movement manager to actually implement the move
        Checks if the path should be recalculated"""
        if not self.goal_position:
            return
        if self.goal_target and game.board.rationalize_pos(self.get_goal_position(self.goal_target)) != self.goal_position:
            self.set_path()
        if self.behaviour.action == "Move_away_from":
            self.smart_retreat()
        self.movement_manager.move()

    def get_targets(self):
        all_targets = []
        if self.behaviour.target == 'Unit':
            all_targets = [u for u in game.units if u.position]
        elif self.behaviour.target == 'Enemy':
            all_targets = [u for u in game.units if u.position and skill_system.check_enemy(self.unit, u)]
        elif self.behaviour.target == 'Ally':
            all_targets = [u for u in game.units if u.position and skill_system.check_ally(self.unit, u)]
        elif self.behaviour.target == 'Event':
            target_spec = self.behaviour.target_spec
            all_targets = []
            for region in game.level.regions:
                try:
                    if region.region_type == RegionType.EVENT and region.sub_nid == target_spec and (not region.condition or evaluate.evaluate(region.condition, self.unit, local_args={'region': region})):
                        all_targets += region.get_all_positions()
                except:
                    logging.warning("Region Condition: Could not parse %s" % region.condition)
            all_targets = list(set(all_targets))  # Remove duplicates
        elif self.behaviour.target == 'Position':
            if self.behaviour.target_spec == "Starting":
                if self.unit.starting_position:
                    all_targets = [self.unit.starting_position]
                else:
                    all_targets = []
            else:
                all_targets = [tuple(self.behaviour.target_spec)]
        if self.behaviour.target in ('Unit', 'Enemy', 'Ally'):
            all_targets = self.handle_roam_unit_spec(all_targets, self.behaviour)

        if self.behaviour.target != 'Position':
            if DB.constants.value('ai_fog_of_war'):
                all_targets = [pos for pos in all_targets if game.board.in_vision(pos, self.unit.team)]
        return all_targets

    def handle_roam_unit_spec(self, all_targets, behaviour):
        """A modified version of an AIController function
        Uses the unit instead of the unit's position
        This way we don't have to find the unit (which can't be done)"""
        target_spec = behaviour.target_spec
        if not target_spec:
            return all_targets
        invert = bool(behaviour.invert_targeting)
        # Uses ^ (which is XOR) to handle inverting the targeting
        if target_spec[0] == "Tag":
            all_targets = [unit for unit in all_targets if bool(target_spec[1] in unit.tags) ^ invert]
        elif target_spec[0] == "Class":
            all_targets = [unit for unit in all_targets if bool(unit.klass == target_spec[1]) ^ invert]
        elif target_spec[0] == "Name":
            all_targets = [unit for unit in all_targets if bool(unit.name == target_spec[1]) ^ invert]
        elif target_spec[0] == 'Faction':
            all_targets = [unit for unit in all_targets if bool(unit.faction == target_spec[1]) ^ invert]
        elif target_spec[0] == 'Party':
            all_targets = [unit for unit in all_targets if bool(unit.party == target_spec[1]) ^ invert]
        elif target_spec[0] == 'ID':
            all_targets = [unit for unit in all_targets if bool(unit.nid == target_spec[1]) ^ invert]
        elif target_spec[0] == 'Team':
            all_targets = [unit for unit in all_targets if bool(unit.team == target_spec[1]) ^ invert]
        return all_targets

    def prepare_move(self):
        """Happens when we first decide we'd like to move"""
        targets = self.get_targets()
        if targets:
            self.goal_target = targets[0]
            self.set_path()
        else:
            self.state = "Init"
            return None

    def set_path(self):
        """Sets our goal and updates movement manager information"""
        self.goal_position = target_system.get_nearest_open_tile(self.unit, game.board.rationalize_pos(self.get_goal_position(self.goal_target)))
        self.path = self.get_move_path()
        self.movement_manager.update_path(self.path)
        self.movement_manager.update_goal_pos(self.goal_position)

    def get_goal_position(self, target):
        """Since we don't just have tuples as goals, this
        returns the position of the target"""
        if hasattr(target, 'position'):
            return target.position
        return target

    def smart_retreat(self) -> bool:
        valid_positions = self.get_true_valid_moves()

        target_positions = self.get_targets()

        zero_move = max(target_system.find_potential_range(self.unit, True, True), default=0)
        single_move = zero_move + equations.parser.movement(self.unit)
        double_move = single_move + equations.parser.movement(self.unit)

        target_positions = {(self.get_goal_position(pos), utils.calculate_distance(self.unit.position, self.get_goal_position(pos))) for pos in target_positions}

        if self.behaviour.view_range == -4:
            pass
        elif self.behaviour.view_range == -3:
            target_positions = {(pos, mag) for pos, mag in target_positions if mag < double_move}
        elif self.behaviour.view_range == -2:
            target_positions = {(pos, mag) for pos, mag in target_positions if mag < single_move}
        elif self.behaviour.view_range == -1:
            target_positions = {(pos, mag) for pos, mag in target_positions if mag < zero_move}
        else:
            target_positions = {(pos, mag) for pos, mag in target_positions if mag < self.view_range}

        if target_positions and len(valid_positions) > 1:
            self.goal_target = utils.smart_farthest_away_pos(self.unit.position, valid_positions, target_positions)
            self.set_path()
            return True
        else:
            return False

    def think(self):
        time = engine.get_time()
        success = False
        self.did_something = False

        logging.info("*** AI Thinking... ***")

        while True:
            # Can spend up to half a frame thinking
            over_time = engine.get_true_time() - time >= 8
            logging.info("Current State: %s", self.state)

            if self.state == 'Init':
                self.start_time = engine.get_time()
                logging.info("Starting AI with nid: %s, position: %s, class: %s, AI: %s", self.unit.nid, self.unit.position, self.unit.klass, self.unit.get_ai())
                self.clean_up()
                # Get next behaviour
                self.set_next_behaviour()
                if self.behaviour:
                    logging.info(self.behaviour.action)
                    if self.behaviour.action == "None":
                        pass  # Try again
                    elif self.behaviour.action == 'Move_to':
                        self.state = "Moving"
                        self.inner_ai = self.prepare_move()
                    elif self.behaviour.action == "Move_away_from":
                        success = self.smart_retreat()
                        if success:
                            self.state = "Moving"
                        else:
                            self.state = "Init"  # Try another behaviour
                else:
                    self.state = 'Done'

            elif self.state == "Moving":
                self.move()

            if self.state == 'Done':
                self.did_something = success
                self.state = 'Init'
                return True

            if over_time:
                break

        return False

class RoamMovementHandler():
    def __init__(self, unit):
        # Controls the actual movement for roam units
        self.ai_speed = DB.ai.get(unit.get_ai()).roam_speed
        self.unit = unit
        self.last_move = 0
        self.path = []
        self.goal_position = None

        self.speed = 0.0
        self.vspeed = 0.0
        self.hspeed = 0.0
        self.direction = [0, 0]

        self.sprite_dir_time = self.ai_speed * 9 # Used to reduce unit sprite flickering
        self.cur_sprite_time = self.sprite_dir_time

    def update_path(self, path):
        """Setter for self.path"""
        self.path = path

    def update_goal_pos(self, pos):
        """Setter for self.goal_position"""
        self.goal_position = pos

    def move(self):
        """Times to see if we should move. Changes sprite if we've reached goal"""
        if self.goal_position != game.board.rationalize_pos(self.unit.position):
            current_time = engine.get_time()
            if current_time - self.last_move > self.ai_speed:
                self.last_move = current_time
                self.handle_direction(self.unit.position, self.path[-1])
        else:
            self.unit.sprite.change_state('normal')

    def handle_direction(self, pos, next_pos):
        """Handles the movement itself"""
        base_speed = 0.008
        base_accel = 0.008
        running_accel = 0.01
        max_speed = 0.15

        pos = game.board.rationalize_pos(pos)

        if next_pos[0] > pos[0]: # Going right
            self.hspeed = self.speed
        elif next_pos[0] < pos[0]: # Going left
            self.hspeed = -self.speed
        else:
            self.hspeed = 0

        if next_pos[1] > pos[1]: # Going up
            self.vspeed = self.speed
        elif next_pos[1] < pos[1]: # Going down
            self.vspeed = -self.speed
        else:
            self.vspeed = 0

        if self.speed < max_speed:
            self.speed += base_accel
        elif self.speed > max_speed:
            self.speed -= running_accel

        # Actually move the unit
        if abs(self.hspeed) > base_speed or abs(self.vspeed) > base_speed:
            self.make_move(self.hspeed, self.vspeed)
            self.cur_sprite_time -= self.ai_speed
            if self.cur_sprite_time <= 0 or self.unit.sprite.state == "normal":
                self.cur_sprite_time = self.sprite_dir_time
                self.unit.sprite.change_state('moving')
                self.unit.sprite.handle_net_position((self.hspeed, self.vspeed))

        rounded_pos = round(self.unit.position[0]), round(self.unit.position[1])
        if self.path[-1] == rounded_pos:
            self.path.pop()

    def make_move(self, dx, dy):
        x, y = self.unit.position
        self.unit.position = x + dx, y + dy
        self.unit.sound.play()