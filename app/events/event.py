from __future__ import annotations
from app.engine.text_evaluator import TextEvaluator

import ast
import logging
from typing import Any, Callable, Dict, List, Set, Tuple

import app.engine.config as cf
import app.engine.graphics.ui_framework as uif
from app.constants import WINHEIGHT, WINWIDTH
from app.data.database import DB
from app.data.level_units import GenericUnit, UniqueUnit
from app.engine import (action, background, banner, dialog, engine, evaluate,
                        icons, image_mods, item_funcs, item_system,
                        skill_system, static_random, target_system, unit_funcs)
from app.engine.animations import MapAnimation
from app.engine.combat import interaction
from app.engine.game_menus.menu_components.generic_menu.simple_menu_wrapper import \
    SimpleMenuUI
from app.engine.game_state import game
from app.engine.graphics.dialog.narration_dialogue import NarrationDialogue
from app.engine.graphics.ui_framework.premade_animations.animation_templates import \
    fade_anim, translate_anim
from app.engine.graphics.ui_framework.ui_framework import UIComponent
from app.engine.graphics.ui_framework.ui_framework_animation import \
    InterpolationType
from app.engine.graphics.ui_framework.ui_framework_layout import HAlignment
from app.engine.objects.item import ItemObject
from app.engine.objects.overworld import OverworldNodeObject
from app.engine.objects.tilemap import TileMapObject
from app.engine.objects.unit import UnitObject
from app.engine.overworld.overworld_actions import OverworldMove
from app.engine.overworld.overworld_movement_manager import \
    OverworldMovementManager
from app.engine.sound import SOUNDTHREAD
from app.events import event_commands, regions
from app.events.event_portrait import EventPortrait
from app.events.screen_positions import parse_screen_position
from app.events.speak_style import SpeakStyle
from app.events import event_functions, overworld_event_functions
from app.resources.resources import RESOURCES
from app.sprites import SPRITES
from app.utilities import str_utils, utils
from app.utilities.enums import Alignments
from app.utilities.typing import NID, Point

# Get all event command implementations
general_funcs = {func: getattr(event_functions, func) for func in dir(event_functions) if callable(getattr(event_functions, func)) and not func.startswith("__")}
overworld_funcs = {func: getattr(overworld_event_functions, func) for func in dir(overworld_event_functions) if callable(getattr(overworld_event_functions, func)) and not func.startswith("__")}
general_funcs.update(overworld_funcs)
function_catalog: Dict[NID, Callable] = general_funcs

class Event():
    _transition_speed = 250
    _transition_color = (0, 0, 0)

    true_vals = ('t', 'true', '1', 'y', 'yes')

    skippable = {"speak", "wait", "bop_portrait",
                 "sound", "location_card", "credits", "ending"}

    def __init__(self, nid, commands, unit=None, unit2=None, item=None, position=None, region=None):
        self.nid = nid
        self.commands: List[event_commands.EventCommand] = commands.copy()
        self.command_idx = 0

        self.background = None

        self.unit = unit
        self.unit2 = unit2
        self.item = item
        self.position = position
        self.region = region

        self.portraits: Dict[str, EventPortrait] = {}
        self.text_boxes: List[dialog.Dialog] = []
        self.other_boxes: List[Tuple[NID, Any]] = []
        self.overlay_ui = uif.UIComponent.create_base_component()

        self.prev_state = None
        self.state = 'processing'

        self.turnwheel_flag = 0  # Whether to enter the turnwheel state after this event is finished
        self.battle_save_flag = 0  # Whether to enter the battle save state after this event is finished

        self.wait_time: int = 0

        # Handles keeping the order that unit sprites should be drawn
        self.priority_counter = 1
        self.do_skip = False
        self.super_skip = False

        self.if_stack = [] # Keeps track of how many ifs we've encountered while searching for the bad ifs 'end'.
        self.parse_stack = [] # Keeps track of whether we've encountered a truth this level or not

        # For transition
        self.transition_state = None
        self.transition_progress = 0
        self.transition_update = 0
        self.transition_speed = self._transition_speed
        self.transition_color = self._transition_color

        # For map animations
        self.animations = []

        # a way of passing key input events down to individual events
        # map between name of listener, and listener function
        self.functions_listening_for_input: Dict[str, Callable[[str]]] = {}

        # a way for any arbitrary event to block state processing until an arbitrary condition is fulfilled
        self.should_remain_blocked: List[Callable[[], bool]] = []

        # a method of queueing unblocked actions that require updating (e.g. movement)
        # update functions should return False once they are finished (so they can be removed from the queue)
        # they should receive an argument that represents whether or not we're in skip mode to facilitate skipping
        # and avoid infinite loops.
        # maps name to function
        self.should_update: Dict[str, Callable[[bool], bool]] = {}

        self.logger = logging.getLogger()

        self.text_evaluator = TextEvaluator(self.logger, game, self.unit, self.unit2, self.item, self.position, self.region)

    @property
    def unit1(self):
        return self.unit

    def save(self):
        ser_dict = {}
        ser_dict['nid'] = self.nid
        ser_dict['commands'] = self.commands
        ser_dict['command_idx'] = self.command_idx
        ser_dict['unit1'] = self.unit.nid if self.unit else None
        ser_dict['unit2'] = self.unit2.nid if self.unit2 else None
        ser_dict['region'] = self.region.nid if self.region else None
        ser_dict['item'] = self.item.uid if self.item else None
        ser_dict['position'] = self.position
        ser_dict['if_stack'] = self.if_stack
        ser_dict['parse_stack'] = self.parse_stack
        return ser_dict

    @classmethod
    def restore(cls, ser_dict):
        unit = game.get_unit(ser_dict['unit1'])
        unit2 = game.get_unit(ser_dict['unit2'])
        region = game.get_region(ser_dict['region'])
        item = game.get_item(ser_dict.get('item'))
        position = ser_dict['position']
        commands = ser_dict['commands']
        nid = ser_dict['nid']
        self = cls(nid, commands, unit, unit2, item, position, region)
        self.command_idx = ser_dict['command_idx']
        self.if_stack = ser_dict['if_stack']
        self.parse_stack = ser_dict['parse_stack']
        return self

    def update(self):
        current_time = engine.get_time()
        # update all internal updates, remove the ones that are finished
        self.should_update = {name: to_update for name, to_update in self.should_update.items() if not to_update(self.do_skip)}

        # Update movement so that no_block works correctly
        if game.movement:
            game.movement.update()

        # Can move through its own internal state up to 5 times in a frame
        counter = 0
        while counter < 5:
            counter += 1
            if self.state != self.prev_state:
                self.prev_state = self.state
                self.logger.debug("Event State: %s", self.state)

            if self.state == 'waiting':
                if current_time > self.wait_time:
                    self.state = 'processing'
                else:
                    break

            elif self.state == 'processing':
                if self.command_idx >= len(self.commands):
                    self.end()
                else:
                    self.process()
                if self.state == 'paused':
                    break  # Necessary so we don't go right back to processing

            elif self.state == 'dialog':
                if self.text_boxes:
                    if self.text_boxes[-1].is_done():
                        action.do(action.LogDialog(self.text_boxes[-1]))
                        self.state = 'processing'
                else:
                    self.state = 'processing'

            elif self.state == 'paused':
                self.state = 'processing'

            elif self.state == 'complete':
                break

            elif self.state == 'blocked':
                # state is blocked; try to unblock
                should_still_be_blocked = False
                for check_still_blocked in self.should_remain_blocked:
                    if check_still_blocked(): # we haven't fulfilled unblock conditions
                        should_still_be_blocked = True
                        break
                if should_still_be_blocked:
                    break
                else:
                    # resume execution and clear blockers
                    self.should_remain_blocked.clear()
                    self.state = 'processing'

        # Handle transition
        if self.transition_state:
            perc = (current_time - self.transition_update) / self.transition_speed
            if self.transition_state == 'open':
                perc = 1 - perc
            self.transition_progress = utils.clamp(perc, 0, 1)
            if perc < 0:
                self.transition_state = None

    def take_input(self, event):
        if event == 'START' or event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            self.skip(event == 'START')

        elif event == 'SELECT' or event == 'RIGHT' or event == 'DOWN':
            if self.state == 'dialog':
                if not cf.SETTINGS['talk_boop']:
                    SOUNDTHREAD.play_sfx('Select 1')
                self.hurry_up()

        for listener in self.functions_listening_for_input.values():
            listener(event)

    def draw(self, surf):
        self.animations = [anim for anim in self.animations if not anim.update()]
        for anim in self.animations:
            anim.draw(surf, offset=(-game.camera.get_x(), -game.camera.get_y()))

        if self.background:
            self.background.draw(surf)

        delete = [key for key, portrait in self.portraits.items() if portrait.update()]
        for key in delete:
            del self.portraits[key]

        # draw all uiframework elements
        ui_surf = self.overlay_ui.to_surf()
        surf.blit(ui_surf, (0, 0))

        sorted_portraits = sorted(self.portraits.values(), key=lambda x: x.priority)
        for portrait in sorted_portraits:
            portrait.draw(surf)

        # Draw other boxes
        self.other_boxes = [(nid, box) for (nid, box) in self.other_boxes if box.update()]
        for _, box in self.other_boxes:
            box.draw(surf)

        # Draw text/dialog boxes
        # if self.state == 'dialog':
        if not self.do_skip:
            to_draw = []
            for dialog_box in reversed(self.text_boxes):
                if not dialog_box.is_complete():
                    to_draw.insert(0, dialog_box)
                if dialog_box.solo_flag:
                    break
            for dialog_box in to_draw:
                dialog_box.update()
                dialog_box.draw(surf)

        # Fade to black
        if self.transition_state:
            s = engine.create_surface((WINWIDTH, WINHEIGHT), transparent=True)
            s.fill((*self.transition_color, int(255 * self.transition_progress)))
            surf.blit(s, (0, 0))

        return surf

    def end(self):
        self.state = 'complete'

    def process(self):
        while self.command_idx < len(self.commands) and self.state == 'processing':
            command = self.commands[self.command_idx]
            try:
                if self.handle_conditional(command):
                    if self.handle_loop(command):
                        pass  # Just builds the next commands
                    elif self.do_skip and command.nid in self.skippable:
                        pass
                    else:
                        self.run_command(command)
                self.command_idx += 1
            except Exception as e:
                raise Exception("Event execution failed with error in command %s" % command) from e

    def handle_loop(self, command: event_commands.EventCommand) -> bool:
        """
        Returns true if a loop was found
        """
        self.logger.disabled = False
        if command.nid == 'for':
            self.logger.info('%s: %s, %s', command.nid, command.parameters, command.flags)
            show_warning = True
            if 'no_warn' in command.flags:
                show_warning = False
            iterator_nid = command.parameters['Nid']
            cond = command.parameters['Expression']
            cond = self._evaluate_all(cond)
            try:
                arg_list = evaluate.evaluate(cond, self.unit, self.unit2, self.item, self.position, self.region)
                arg_list = [self._object_to_str(arg) for arg in arg_list]
            except Exception as e:
                self.logger.error("%s: Could not evaluate {%s}" % (e, cond))
                return False
            if not arg_list:
                if show_warning:
                    self.logger.warning("Arg list is empty for: %s" % (cond))

            # template and paste all commands inside the for loop
            # to find the correct endf, we'll need to make sure that
            # every nested for-loop is accounted for
            internal_fors = 0

            curr_idx = self.command_idx + 1
            curr_command = self.commands[curr_idx]
            looped_commands: List[event_commands.EventCommand] = []
            while curr_command.nid != 'endf' or internal_fors > 0:
                if curr_command.nid == 'for':
                    internal_fors += 1
                if curr_command.nid == 'endf':
                    internal_fors -= 1
                looped_commands.append(curr_command)
                curr_idx += 1
                if curr_idx > len(self.commands):
                    self.logger.error("%s: could not find end command for loop %s" % ('handle_conditional', cond))
                    return False
                curr_command = self.commands[curr_idx]

            # remove the initial for-loop, as we've templated out all the child fors
            self.commands = self.commands[:self.command_idx + 1] + self.commands[curr_idx:]
            for arg in reversed(arg_list):
                for command in reversed(looped_commands):
                    new_command = command.__class__.copy(command)
                    if iterator_nid:
                        new_command.parameters = {k: v.replace('{' + iterator_nid + '}', arg) for k, v in new_command.parameters.items()}
                    self.commands.insert(self.command_idx + 1, new_command)
            return True
        return False

    def handle_conditional(self, command) -> bool:
        """
        Returns true if the processor should be processing this command
        """
        self.logger.disabled = False
        if command.nid == 'if':
            self.logger.info('%s: %s, %s', command.nid, command.parameters, command.flags)
            if not self.if_stack or self.if_stack[-1]:
                try:
                    cond = command.parameters['Expression']
                    cond = self._evaluate_all(cond)
                    truth = bool(evaluate.evaluate(cond, self.unit, self.unit2, self.item, self.position, self.region))
                except Exception as e:
                    self.logger.error("%s: Could not evaluate {%s}" % (e, cond))
                    truth = False
                self.logger.info("Result: %s" % truth)
                self.if_stack.append(truth)
                self.parse_stack.append(truth)
            else:
                self.if_stack.append(False)
                self.parse_stack.append(True)
            return False
        elif command.nid == 'elif':
            self.logger.info('%s: %s, %s', command.nid, command.parameters, command.flags)
            if not self.if_stack:
                self.logger.error("Syntax Error somewhere in script. 'elif' needs to be after if statement.")
                return False
            # If we haven't encountered a truth yet
            if not self.parse_stack[-1]:
                try:
                    cond = command.parameters['Expression']
                    cond = self._evaluate_all(cond)
                    truth = bool(evaluate.evaluate(cond, self.unit, self.unit2, self.item, self.position, self.region))
                except Exception as e:
                    self.logger.error("Could not evaluate {%s}" % cond)
                    truth = False
                self.if_stack[-1] = truth
                self.parse_stack[-1] = truth
                self.logger.info("Result: %s" % truth)
            else:
                self.if_stack[-1] = False
            return False
        elif command.nid == 'else':
            self.logger.info('%s: %s, %s', command.nid, command.parameters, command.flags)
            if not self.if_stack:
                self.logger.error("Syntax Error somewhere in script. 'else' needs to be after if statement.")
                return False
            # If the most recent is False but the rest below are non-existent or true
            if not self.parse_stack[-1]:
                self.if_stack[-1] = True
                self.parse_stack[-1] = True
            else:
                self.if_stack[-1] = False
            return False
        elif command.nid == 'end':
            self.logger.info('%s: %s, %s', command.nid, command.parameters, command.flags)
            if self.if_stack:
                self.if_stack.pop()
            if self.parse_stack:
                self.parse_stack.pop()
            return False

        if self.if_stack and not self.if_stack[-1]:
            return False
        return True

    def skip(self, super_skip=False):
        self.do_skip = True
        self.super_skip = super_skip
        if self.state != 'paused':
            self.state = 'processing'
        self.transition_state = None
        self.hurry_up()
        self.text_boxes.clear()
        self.other_boxes.clear()
        self.should_remain_blocked.clear()
        while self.should_update:
            self.should_update = {name: to_update for name, to_update in self.should_update.items() if not to_update(self.do_skip)}

    def hurry_up(self):
        if self.text_boxes:
            self.text_boxes[-1].hurry_up()

    def run_command(self, command: event_commands.EventCommand):
        self.logger.info('%s: %s, %s', command.nid, command.parameters, command.flags)

        parameters, flags = event_commands.convert_parse(command, self._evaluate_all)

        # Handle the weird cases where we don't want to handle evaluation
        if command.nid == 'choice':
            unevaled_parameters, flags = event_commands.convert_parse(command, None)
            parameters['Choices'] = unevaled_parameters['Choices']
        elif command.nid == 'table':
            unevaled_parameters, flags = event_commands.convert_parse(command, None)
            parameters['TableData'] = unevaled_parameters['TableData']

        if 'no_warn' in flags:
            self.logger.disabled = True
        else:
            self.logger.disabled = False
        parameters = {str_utils.camel_to_snake(k): v for k, v in parameters.items()}
        function_catalog[command.nid](self, **parameters, flags=flags)

        if command.nid == 'overworld_cinematic':
            self.start_overworld_cinematic(command)

        elif command.nid == 'set_overworld_position':
            values, flags = event_commands.convert_parse(command)
            self.set_overworld_position(*values, flags=flags)

        elif command.nid == 'reveal_overworld_node':
            self.reveal_overworld_node(command)

        elif command.nid == 'reveal_overworld_road':
            self.reveal_overworld_road(command)

        elif command.nid == 'disable_overworld_entity':
            self.disable_overworld_entity(command)

        elif command.nid == 'overworld_move_unit':
            values, flags = event_commands.convert_parse(command)
            self.overworld_move_unit(*values, flags=flags)

        elif command.nid == 'toggle_narration_mode':
            self.toggle_narration(command)

        elif command.nid == 'narrate':
            self.overworld_speak(command)

        elif command.nid == 'create_overworld_entity':
            self.create_overworld_entity(command)

        elif command.nid == 'set_overworld_menu_option_enabled':
            values, flags = event_commands.convert_parse(command, self._evaluate_all)
            self.set_overworld_menu_option_enabled(*values, flags)

        elif command.nid == 'set_overworld_menu_option_visible':
            values, flags = event_commands.convert_parse(command, self._evaluate_all)
            self.set_overworld_menu_option_visible(*values, flags)

    def _object_to_str(self, obj) -> str:
        if hasattr(obj, 'uid'):
            return str(obj.uid)
        elif hasattr(obj, 'nid'):
            return str(obj.nid)
        else:
            return str(obj)

    def _evaluate_all(self, text: str) -> str:
        return self.text_evaluator._evaluate_all(text)

    def _place_unit(self, unit, position, entry_type):
        if self.do_skip:
            action.do(action.ArriveOnMap(unit, position))
        elif entry_type == 'warp':
            action.do(action.WarpIn(unit, position))
        elif entry_type == 'swoosh':
            action.do(action.SwooshIn(unit, position))
        elif entry_type == 'fade':
            action.do(action.FadeIn(unit, position))
        else:  # immediate
            action.do(action.ArriveOnMap(unit, position))

    def _move_unit(self, movement_type, placement, follow, unit, position):
        position = tuple(position)
        position = self.check_placement(unit, position, placement)
        if not position:
            self.logger.warning("Couldn't determine valid position for %s?", unit.nid)
            return
        if movement_type == 'immediate' or self.do_skip:
            action.do(action.Teleport(unit, position))
        elif movement_type == 'warp':
            action.do(action.Warp(unit, position))
        elif movement_type == 'fade':
            action.do(action.FadeMove(unit, position))
        elif movement_type == 'normal':
            if unit.position == position:
                # Don't bother if identical
                return
            path = target_system.get_path(unit, position)
            action.do(action.Move(unit, position, path, event=True, follow=follow))

    def _add_unit_from_direction(self, unit, position, direction, placement) -> bool:
        offsets = [-1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6, -7, 7]
        final_pos = None

        if direction == 'west':
            test_pos = (0, position[1])
            for x in offsets:
                if game.movement.check_traversable(unit, test_pos):
                    final_pos = test_pos
                    break
                else:
                    test_pos = (0, position[1] + x)
        elif direction == 'east':
            test_pos = (game.tilemap.width - 1, position[1])
            for x in offsets:
                if game.movement.check_traversable(unit, test_pos):
                    final_pos = test_pos
                    break
                else:
                    test_pos = (game.tilemap.width - 1, position[1] + x)
        elif direction == 'north':
            test_pos = (position[0], 0)
            for x in offsets:
                if game.movement.check_traversable(unit, test_pos):
                    final_pos = test_pos
                    break
                else:
                    test_pos = (position[0] + x, 0)
        elif direction == 'south':
            test_pos = (position[0], game.tilemap.height - 1)
            for x in offsets:
                if game.movement.check_traversable(unit, test_pos):
                    final_pos = test_pos
                    break
                else:
                    test_pos = (position[1] + x, game.tilemap.height - 1)
        if final_pos:
            final_pos = self.check_placement(unit, final_pos, placement)
        if final_pos:
            action.do(action.ArriveOnMap(unit, final_pos))
            return True
        return False

    def _get_position(self, next_pos, unit, group, unit_nid=None):
        if unit_nid is None:
            unit_nid = unit.nid
        if not next_pos:
            position = group.positions.get(unit_nid)
        elif next_pos.lower() == 'starting':
            position = unit.starting_position
        elif ',' in next_pos:
            position = self.parse_pos(next_pos)
        else:
            other_group = game.level.unit_groups.get(next_pos)
            position = other_group.positions.get(unit_nid)
        return position

    def _check_placement(self, unit, position, placement):
        if not game.board.check_bounds(position):
            self.logger.error("%s: position out of bounds %s", 'check_placement', position)
            return None
        current_occupant = game.board.get_unit(position)
        if current_occupant:
            if placement == 'giveup':
                self.logger.warning("Check placement (giveup): Unit already present on tile %s", position)
                return None
            elif placement == 'stack':
                return position
            elif placement == 'closest':
                position = target_system.get_nearest_open_tile(unit, position)
                if not position:
                    self.logger.warning("Somehow wasn't able to find a nearby open tile")
                    return None
                return position
            elif placement == 'push':
                new_pos = target_system.get_nearest_open_tile(current_occupant, position)
                action.do(action.ForcedMovement(current_occupant, new_pos))
                return position
        else:
            return position

    def _copy_unit(self, unit_nid):
        level_prefab = DB.levels.get(game.level.nid)
        level_unit_prefab = level_prefab.units.get(unit_nid)
        if not level_unit_prefab:
            self.logger.warning("Could not find level unit prefab for unit with nid: %s", unit_nid)
            return None
        new_nid = str_utils.get_next_int(level_unit_prefab.nid, game.unit_registry.keys())
        level_unit_prefab.nid = new_nid
        new_unit = UnitObject.from_prefab(level_unit_prefab, game.current_mode)
        level_unit_prefab.nid = unit_nid  # Set back to old nid
        new_unit.position = None
        new_unit.dead = False
        new_unit.party = game.current_party
        game.full_register(new_unit)
        return new_unit

    def _get_item_in_inventory(self, values):
        unit = self.get_unit(values[0])
        if not unit:
            self.logger.error("Couldn't find unit with nid %s" % values[0])
            return None, None
        item_id = values[1]
        inids = [item.nid for item in unit.items]
        iuids = [item.uid for item in unit.items]
        if (item_id not in inids) and (not str_utils.is_int(item_id) or not int(item_id) in iuids):
            self.logger.error("Couldn't find item with id %s" % values[1])
            return None, None
        item = [item for item in unit.items if (item.nid == item_id or (str_utils.is_int(item_id) and item.uid == int(item_id)))][0]
        return unit, item

    def _apply_stat_changes(self, unit, stat_changes, flags):
        klass = DB.classes.get(unit.klass)
        # clamp stat changes
        stat_changes = {k: utils.clamp(v, -unit.stats[k], klass.max_stats.get(k) - unit.stats[k]) for k, v in stat_changes.items()}

        immediate = 'immediate' in flags

        action.do(action.ApplyStatChanges(unit, stat_changes))
        if not immediate:
            game.memory['stat_changes'] = stat_changes
            game.exp_instance.append((unit, 0, None, 'stat_booster'))
            game.state.change('exp')
            self.state = 'paused'

    def _apply_growth_changes(self, unit, growth_changes):
        action.do(action.ApplyGrowthChanges(unit, growth_changes))

    def start_overworld_cinematic(self, command):
        values, flags = event_commands.parse(command, self._evaluate_all)
        if values:
            overworld_nid = values[0]
        else:
            if DB.overworlds.values():
                overworld_nid = DB.overworlds.values()[0].nid
            else:
                self.logger.error('No overworlds in the DB - why are you calling the overworld command?')
                return
        # save level state
        self.prev_game_boundary = game.boundary
        self.prev_board = game.board
        from app.engine.overworld.overworld_states import OverworldFreeState
        OverworldFreeState.set_up_overworld_game_state(overworld_nid)

    def set_overworld_position(self, entity_nid: NID, location: NID | Tuple[float, float], flags={}):
        if isinstance(location, tuple): # setting to a direct coordinate
            display_pos = location
            overworld = game.overworld_controller
            entity = overworld.entities[entity_nid]
            if entity is None:
                self.logger.error('{}: Party with NID {} not found.'.format('set_overworld_position', entity_nid))
                return
            entity.display_position = display_pos
        else: # setting position to node
            overworld_node_nid: NID = location
            overworld = game.overworld_controller
            entity = overworld.entities[entity_nid]
            node = overworld.nodes[overworld_node_nid]
            if entity is None or node is None:
                if entity is None:
                    self.logger.error('{}: Party with NID {} not found.'.format('set_overworld_position', entity_nid))
                if node is None:
                    self.logger.error('{}: Node with NID {} not found.'.format('set_overworld_position', overworld_node_nid))
                return
            # both node and entity exist
            if overworld_node_nid not in overworld.revealed_node_nids:
                # node isn't enabled yet
                self.logger.error('{}: Node {} exists, but is not yet enabled in overworld {}.'.format('set_overworld_position', overworld_node_nid, overworld._overworld.nid))
                return
            else:
                # both exist and node is enabled
                # move the entity
                entity.on_node = node.nid
        if 'no_animate' not in flags:
            entity.sprite.set_transition('fade_in')

    def reveal_overworld_node(self, command):
        values, flags = event_commands.parse(command, self._evaluate_all)
        overworld_node_nid: NID = values[0]
        if len(values) > 1:
            force = values[1]
        else:
            force = False
        overworld = game.overworld_controller
        node = overworld.nodes[overworld_node_nid]
        if not node:
            self.logger.error('{}: Node with NID {} not found'.format('reveal_overworld_node', overworld_node_nid))
            return
        overworld.enable_node(overworld_node_nid)
        if not force and not self.do_skip:
            node.sprite.set_transition('fade_in')
            self.wait_time = engine.get_time() + node.sprite.transition_time
            self.state = 'waiting'

    def reveal_overworld_road(self, command):
        values, flags = event_commands.parse(command, self._evaluate_all)
        node_1_nid: NID = values[0]
        node_2_nid: NID = values[1]
        if len(values) > 2:
            force = values[2]
        else:
            force = False
        overworld = game.overworld_controller
        # both nodes should be enabled
        if node_1_nid not in overworld.revealed_node_nids or node_2_nid not in overworld.revealed_node_nids:
            return
        # both nodes should be neighbors
        if node_2_nid not in overworld.connected_nodes(node_1_nid, force=True):
            return

        road = overworld.get_road(node_1_nid, node_2_nid, True)
        if not road:
            self.logger.error('{}: Road between nodes {} and {} not found'.format('reveal_overworld_road', node_1_nid, node_2_nid))
            return
        overworld.enable_road(road.nid)
        if not force and not self.do_skip:
            road.sprite.set_transition('fade_in')
            self.wait_time = engine.get_time() + road.sprite.transition_time
            self.state = 'waiting'

    def disable_overworld_entity(self, command):
        values, flags = event_commands.parse(command, self._evaluate_all)
        entity = game.overworld_controller.entities.get(values[0], None)
        if not entity:
            self.logger.error("%s: No such entity exists with nid %s", "disable_overworld_entity", values[0])
            return
        if 'no_animate' not in flags:
            entity.sprite.set_transition('fade_out')
        entity.on_node = None
        entity.display_position = None

    def overworld_move_unit(self, entity_nid: NID, target_location: Tuple[int, int] | NID,
                            speed_adj: float, path: List[Point], flags={}):
        # default values
        if speed_adj is None:
            speed_adj = 5

        # function
        entity = game.overworld_controller.entities.get(entity_nid, None)
        if not entity.display_position:
            self.logger.error("%s: Attempting to move entity %s with no position - is it on the overworld?", 'overworld_move_unit', entity_nid)
            return

        follow = 'no_follow' not in flags
        block = 'no_block' not in flags
        disable_after = 'disable_after' in flags
        mute = 'no_sound' in flags

        if disable_after:
            def disable_func():
                entity.sprite.set_transition('fade_out')
                entity.on_node = None
                entity.display_position = None
        else:
            def disable_func():
                pass

        if not entity:
            self.logger.error("%s: Couldn't find entity %s", "overworld_move_unit", entity_nid)
            return
        if not entity.display_position:
            self.logger.error("Unit not on map!")
            return
        if path:
            # i'm disabling linger for arbitrary paths as a default, because i think it makes more sense that way
            movement = OverworldMove(entity, None, game.overworld_controller, event=True, follow=follow, speed_adj=speed_adj, path=path, linger=0, after_move_callback=disable_func, mute=mute)
            if self.do_skip: # we are skipping; resolve this instantly
                entity.display_position = path[-1]
                return
        elif isinstance(target_location, NID):
            target_node: OverworldNodeObject = game.overworld_controller.nodes.get(target_location, None)
            if entity.on_node: # we're pathfinding to a node
                entity_node = game.overworld_controller.nodes[entity.on_node]
                if game.overworld_controller.any_path(entity_node, target_node): # if there is a path from the unit to this node
                    if self.do_skip: # we are skipping; resolve this instantly
                        entity.on_node = target_node.nid
                        return
            movement = OverworldMove(entity, target_node, game.overworld_controller, event=True, follow=follow, speed_adj=speed_adj, after_move_callback=disable_func, mute=mute)
        elif isinstance(target_location, Tuple):
            path = [target_location]
            movement = OverworldMove(entity, None, game.overworld_controller, event=True, follow=follow, speed_adj=speed_adj, path=path, linger=0, after_move_callback=disable_func, mute=mute)
            if self.do_skip: # we are skipping; resolve this instantly
                entity.display_position = path[-1]
                return
        else:
            self.logger.error("%s: No valid path or target location specified: path: %s | target_location: %s", "overworld_move_unit", str(path), str(target_location))
            return

        if block:
            movement.queue(game.movement)
            self.state = 'paused'
            game.state.change('overworld_movement')
            return
        # else switch internal state
        if not hasattr(self, 'overworld_movement_manager'):
            self.overworld_movement_manager = OverworldMovementManager(game.overworld_controller)
        movement.queue(self.overworld_movement_manager)
        if follow:
            game.camera.do_slow_pan(1000)
            game.camera.set_center(entity.display_position[0], entity.display_position[1])
        if 'overworld_movement' not in self.should_update.keys(): # queue continuous update function if not exists
            def update_movement(should_skip: bool):
                if should_skip:
                    self.overworld_movement_manager.finish_all_movement()
                    return True
                # make sure the camera is centered first
                if not game.camera.at_rest():
                    return False
                self.overworld_movement_manager.update()
                focal_unit_nid = self.overworld_movement_manager.get_following_unit()
                if focal_unit_nid:
                    focal_unit = game.overworld_controller.entities[focal_unit_nid]
                    unit_position = focal_unit.display_position
                    game.cursor.set_pos((round(unit_position[0]), round(unit_position[1])))
                    game.camera.set_center(*unit_position)
                if len(self.overworld_movement_manager) <= 0:
                    return True
                return False
            self.should_update['overworld_movement'] = update_movement

    def toggle_narration(self, command):
        values, flags = event_commands.parse(command, self._evaluate_all)
        toggle_which = values[0].lower()
        if len(values) > 1:
            anim_duration = int(values[1])
        else:
            anim_duration = 1000
        # initialize if the component doesn't exist
        if not self.overlay_ui.has_child('event_narration'):
            narration_component = NarrationDialogue('event_narration', self.overlay_ui, anim_duration)
            self.overlay_ui.add_child(narration_component)
            narration_component.disable()
        else:
            narration_component: NarrationDialogue = self.overlay_ui.get_child('event_narration')

        # animate in or out
        if not self.do_skip:
            if toggle_which == 'open':

                narration_component.enter()
                self.wait_time = engine.get_time() + anim_duration
                self.state = 'waiting'
            else:
                narration_component: NarrationDialogue = self.overlay_ui.get_child('event_narration')
                narration_component.exit()
                self.wait_time = engine.get_time() + anim_duration
                self.state = 'waiting'

    def overworld_speak(self, command):
        if not self.overlay_ui.has_child('event_narration'):
            self.logger.error("%s: Not currently in overworld narration mode", "overworld_speak")
            return

        narration_component: NarrationDialogue = self.overlay_ui.get_child('event_narration')

        values, flags = event_commands.parse(command, self._evaluate_all)
        narrator = values[0]
        dialogue = values[1]

        # add the hurry up handler if it doesn't already exist
        if 'event_narration_listener' not in self.functions_listening_for_input:
            def handle_input(event):
                narration_component.hurry_up(event)
            self.functions_listening_for_input['event_narration_listener'] = handle_input

        narration_component.push_text(narrator, dialogue)
        if 'no_block' in flags or self.do_skip:
            pass
        else:
            # block state execution while dialogue resolves
            def should_block():
                return not narration_component.finished()
            self.should_remain_blocked.append(should_block)
            self.state = 'blocked'

    def create_overworld_entity(self, command):
        from app.engine.objects.overworld import OverworldEntityObject
        values, flags = event_commands.parse(command, self._evaluate_all)
        entity_nid = values[0]
        if 'delete' in flags:
            game.overworld_controller.delete_entity(entity_nid)
            return
        if entity_nid in game.overworld_controller.entities.keys():
            self.logger.error('%s: Entity with nid %s already exists', 'create_overworld_entity', entity_nid)
            return
        if len(values) > 1 and values[1]:
            unit_nid = values[1]
            if unit_nid not in DB.units.keys():
                self.logger.error('%s: No such unit with nid %s', 'create_overworld_entity', unit_nid)
            if values[2] in DB.teams:
                team_nid = values[2]
            else:
                team_nid = 'player'
            new_entity = OverworldEntityObject.from_unit_prefab(entity_nid, None, unit_nid, team_nid)
            game.overworld_controller.add_entity(new_entity)

    def set_overworld_menu_option_enabled(self, node_nid: NID, option_nid: NID, setting: bool, flags: Dict):
        overworld = game.overworld_controller
        overworld.toggle_menu_option_enabled(node_nid, option_nid, not setting)

    def set_overworld_menu_option_visible(self, node_nid: NID, option_nid: NID, setting: bool, flags: Dict):
        overworld = game.overworld_controller
        overworld.toggle_menu_option_visible(node_nid, option_nid, setting)

    def _parse_pos(self, text: str, is_float=False):
        position = None
        if ',' in text:
            text = text.replace(')', '').replace('(', '')
            if is_float:
                position = tuple(float(_) for _ in text.split(','))
            else:
                position = tuple(int(_) for _ in text.split(','))
        elif text == '{position}':
            position = self.position
        elif not game.is_displaying_overworld() and self.get_unit(text):
            position = self.get_unit(text).position
        elif game.is_displaying_overworld() and self.get_overworld_location_of_object(text):
            position = self.get_overworld_location_of_object(text).position
        else:
            valid_regions = \
                [tuple(region.position) for region in game.level.regions
                 if text == region.sub_nid and region.position and
                 not game.board.get_unit(region.position)]
            if valid_regions:
                position = static_random.shuffle(valid_regions)[0]
        return position

    def _get_unit(self, text) -> UnitObject:
        if text in ('{unit}', '{unit1}'):
            return self.unit
        elif text == '{unit2}':
            return self.unit2
        elif text == '{created_unit}':
            return self.created_unit
        else:
            return game.get_unit(text)

    def get_overworld_location_of_object(self, text, entity_only=False, node_only=False) -> OverworldNodeObject:
        if game.overworld_controller:
            if not node_only and text in game.overworld_controller.entities:
                entity_at_nid = game.overworld_controller.entities[text]
                if entity_at_nid:
                    return entity_at_nid.node

            if not entity_only and text in game.overworld_controller.nodes:
                node_at_nid = game.overworld_controller.nodes[text]
                if node_at_nid:
                    return node_at_nid
        return None
