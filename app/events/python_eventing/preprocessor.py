from __future__ import annotations
import ast
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Type
from app.events.event_prefab import EventCatalog

from app.events.python_eventing.compilation import ast_preprocess
from app.utilities.typing import NID
from ..event_commands import ALL_EVENT_COMMANDS, EventCommand, BattleSave, Prep, Base, TriggerScript, TriggerScriptWithArgs

EVENT_INSTANCE = "EC"
FORBIDDEN_PYTHON_COMMANDS: List[str] = []
SAVE_COMMANDS: List[EventCommand] = [BattleSave, Prep, Base]
SAVE_COMMAND_NIDS: Set[str] = set([cmd.nid for cmd in SAVE_COMMANDS] + [cmd.nickname for cmd in SAVE_COMMANDS])
EVENT_CALL_COMMANDS: List[EventCommand] = [TriggerScript, TriggerScriptWithArgs]
EVENT_CALL_COMMAND_NIDS: Set[str] = set([cmd.nid for cmd in EVENT_CALL_COMMANDS] + [cmd.nickname for cmd in EVENT_CALL_COMMANDS])

def check_valid_event_function_call(node: ast.stmt):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
        isinstance(node.func.value, ast.Name) and node.func.value.id == EVENT_INSTANCE:
        event_command_nid = node.func.attr
        if not event_command_nid in ALL_EVENT_COMMANDS:
            return False
        if event_command_nid in FORBIDDEN_PYTHON_COMMANDS:
            return False
    return True

def check_safe_event_function_call(node: ast.stmt, parents: List[Type[ast.stmt]]):
    """Expectations: if 'node' is an EventFunction call, e.g. 'speak(*args)'
      and the parents are the ast nodes above it. We assert that the immediate
      parent must be an solitary Expr, and that this cannot be nested in a function.

    Rationale:
      The core concept of this event engine is this: that we can yield
      EventCommand objects, thus allowing us to cede control
      to the actual Event object and execute the yielded EventCommand.
      Once the EventCommand is executed, we then return control
      to the Parser, which can resume the execution of the script,
      until the next EventCommand is hit, which is then yielded, control ceded,
      etc.

      Therefore, the most important rule is that every single event function
      *can* be yielded one-by-one. This fails, for example, for the line,
      `speak(args...) and speak(args2...)`. This line tries to
      execute both speak commands at once, which is not how the EventEngine
      works. Therefore, it is invalid. Likewise, creating a function definition
      with multiple EventCommand and then calling them would also be problematic.

      Therefore, we must be sure to uphold that EventCommand are *always* yieldable, i.e.
      either top-level Exprs, or equivalent (in the bodies of for and while-loops, which can be yielded)
      and not args to a Function call, not values in e.g. a BinOp, and not part of the for loop's iterator
      or while loop's test.
    """
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
      isinstance(node.func.value, ast.Name) and node.func.value.id == EVENT_INSTANCE:
        if not parents[-1] == ast.Expr:
            return False
        elif ast.FunctionDef in parents:
            return False
    return True

def is_save_call(node: ast.stmt):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
        isinstance(node.func.value, ast.Name) and node.func.value.id == EVENT_INSTANCE and \
            node.func.attr in SAVE_COMMAND_NIDS:
        return True
    return False

def is_trigger_script_call(node: ast.stmt):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
        isinstance(node.func.value, ast.Name) and node.func.value.id == EVENT_INSTANCE and \
            node.func.attr in EVENT_CALL_COMMAND_NIDS:
        return True
    return False

def check_valid_trigger_script_call(node: ast.stmt):
    if is_trigger_script_call(node):
        if len(node.args) > 0 and isinstance(node.args[0], ast.Str):
            return True
        return False
    return True

def get_script_from_trigger_script_call(node: ast.Call) -> str:
    try:
        if is_trigger_script_call(node):
            return node.args[0].s
    except:
        raise ValueError("Not a valid TriggerScript call")

ERROR_TEMPLATE = \
"""
    Event "{event_name}", Line {lnum}:
        {line}
    {error_name}: {what}"""

STACK_ERROR_TEMPLATE = \
"""
    From event "{event_name}", Line {lnum}:
        {line}"""

@dataclass
class PreprocessorError():
    event_name: str | List[str]
    line_num: int | List[int]
    line: str | List[str]
    what = "generic preprocessor error"

    def __str__(self) -> str:
        if isinstance(self.event_name, list):
            # all three should be list
            msg = ''
            for i in range(len(self.event_name) - 1):
                msg += STACK_ERROR_TEMPLATE.format(event_name=self.event_name[i], lnum=self.line_num[i], line=self.line[i].strip())
            msg += ERROR_TEMPLATE.format(event_name=self.event_name[-1], lnum=self.line_num[-1], line=self.line[-1].strip(),
                                         error_name=self.__class__.__name__, what=self.what)
            return msg
        else:
            msg = ERROR_TEMPLATE.format(event_name=self.event_name, lnum=self.line_num, line=self.line.strip(),
                                        error_name=self.__class__.__name__, what=self.what)
            return msg

class NestedEventError(PreprocessorError):
    what = "all event function calls must be alone and outside function def"

class InvalidCommandError(PreprocessorError):
    what = "unknown event command"

class NoSaveInLoopError(PreprocessorError):
    what = "cannot use save event commands in for loops"

class MalformedTriggerScriptCall(PreprocessorError):
    what = 'trigger script must have non-variable valid event target'

class CannotUseYieldError(PreprocessorError):
    what = 'cannot use yield in python event scripting'

@dataclass
class EventContext():
    event_name: NID
    source_as_lines: List[str]
    source_as_ast: ast.Module

    @classmethod
    def from_event(cls: Type[EventContext], event_name: str, source: str):
        as_lines = source.split('\n')
        as_ast = ast.parse(ast_preprocess(source))
        return cls(event_name, as_lines, as_ast)

class Preprocessor():
    def __init__(self, event_db: EventCatalog = None) -> None:
        self._catalog: EventCatalog = event_db
        self._parsed_events: Dict[NID, EventContext] = {}

    def get_event_info(self, event_name: str) -> Optional[EventContext]:
        if not event_name in self._parsed_events and self._catalog and event_name in self._catalog.keys():
            self._parsed_events[event_name] = EventContext.from_event(event_name, self._catalog.get_from_nid(event_name).source)
        return self._parsed_events.get(event_name)

    def verify_event(self, event_name: str, event_script: str = None) -> List[PreprocessorError]:
        self._parsed_events.clear() # no reason to load all events simultaneously in memory
        event_info = None
        if not event_script:
            event_info = self.get_event_info(event_name)
        else:
            event_info = EventContext.from_event(event_name, event_script)
            self._parsed_events[event_name] = event_info

        event_command_call_errors = self.verify_event_calls(event_info)
        loop_save_errors = self.verify_no_loop_save(event_info)
        yield_errors = self.verify_no_yields(event_info)
        return event_command_call_errors + loop_save_errors + yield_errors
    
    def verify_no_yields(self, event: EventContext) -> List[CannotUseYieldError]:
        """Since the event engine uses yields as its primary mode of extracting EventCommands,
        yields should not be used in the script."""
        yield_errors: List[CannotUseYieldError] = []
        for cnode in ast.walk(event.source_as_ast):
            if isinstance(cnode, ast.Yield):
                yield_errors.append(CannotUseYieldError(event.event_name, cnode.lineno, event.source_as_lines[cnode.lineno - 1]))
        return yield_errors
        
    def verify_event_calls(self, event: EventContext) -> List[PreprocessorError]:
        """see `check_safe_event_function_call` above for details on what this function verifies.
        It also verifies that all event calls are valid commands, via `check_valid_event_function_call`.
        """
        def recursive_tree_verify(node: ast.stmt, parents: List[Type[ast.stmt]] = None):
            if parents is None:
                curr_parents = []
            else:
                curr_parents = parents[:]
            unsafe_event_function_calls: List[PreprocessorError] = []
            # base case
            if not check_safe_event_function_call(node, curr_parents):
                unsafe_event_function_calls.append(NestedEventError(event.event_name, node.lineno, event.source_as_lines[node.lineno - 1]))
            if not check_valid_event_function_call(node):
                unsafe_event_function_calls.append(InvalidCommandError(event.event_name, node.lineno, event.source_as_lines[node.lineno - 1]))
            curr_parents.append(node.__class__)
            for cnode in ast.iter_child_nodes(node):
                unsafe_event_function_calls += recursive_tree_verify(cnode, curr_parents)
            return unsafe_event_function_calls
        return recursive_tree_verify(event.source_as_ast)
    
    def verify_no_loop_save(self, event: EventContext, from_event_names: List[str] = None, from_event_lines: List[int] = None) -> List[NoSaveInLoopError | MalformedTriggerScriptCall]:
        """Events cannot be resumed in the middle of a for loop. Therefore, any save commands
        cannot be run inside a for loop. Because for loops can call other events, we
        must also verify the other scripts."""
        from_event_names = from_event_names[:] if from_event_names else []
        from_event_lines = from_event_lines[:] if from_event_lines else []
        # if this is the first level of event, we don't care about direct mid-event saves
        # but if this is a nested event, any save is suspect
        is_top_level_event = True if (not from_event_lines and not from_event_names) else False
        current_event = event.event_name

        def generate_error_info(node: ast.stmt) -> Tuple[list, list, list]:
            previous_event_list = [self.get_event_info(event_name).source_as_lines[event_line - 1] for event_name, event_line in zip(from_event_names, from_event_lines)]
            error_info = (from_event_names + [current_event], from_event_lines + [node.lineno], previous_event_list + [event.source_as_lines[node.lineno - 1]])
            return error_info
        
        def recursive_tree_verify(snode: ast.stmt, parents: List[Type[ast.stmt]] = None):
            unsafe_save_calls: List[NoSaveInLoopError] = []
            if parents is None:
                curr_parents = []
            else:
                curr_parents = parents[:]
            for cnode in ast.iter_child_nodes(snode):
                if is_save_call(cnode):                                 # if there's any save call, fail in two conditions
                    if not is_top_level_event or ast.For in curr_parents:   # if we are already in a nested script, or we're in a for loop
                        unsafe_save_calls.append(NoSaveInLoopError(*generate_error_info(cnode)))
                elif is_trigger_script_call(cnode):                     # likewise, if we're triggering another script
                    if not is_top_level_event or ast.For in curr_parents:   # in a nested script, or under a for loop
                        if not check_valid_trigger_script_call(cnode):  # enforce that all trigger scripts go to a specified other event
                            unsafe_save_calls.append(MalformedTriggerScriptCall(*generate_error_info(cnode)))
                        else:                                           # if it does, now we recurse into the other event
                            nested_event_nid = get_script_from_trigger_script_call(cnode)
                            nested_event_info = self.get_event_info(nested_event_nid)
                            if not nested_event_info:
                                unsafe_save_calls.append(MalformedTriggerScriptCall(*generate_error_info(cnode)))
                            else:
                                error_info = generate_error_info(cnode)
                                triggered_script_unsafe_save_calls = self.verify_no_loop_save(nested_event_info, error_info[0], error_info[1])
                                unsafe_save_calls += triggered_script_unsafe_save_calls
                else: # command is neither trigger script nor save; continue walking
                    unsafe_save_calls += recursive_tree_verify(cnode, curr_parents + [snode.__class__])
            return unsafe_save_calls
        return recursive_tree_verify(event.source_as_ast)
    
# python -m app.events.python_eventing.preprocessor
if __name__ == '__main__':
    from pathlib import Path
    SCRIPT_NAME = "example_script.txt"
    script_path = Path(__file__).with_name(SCRIPT_NAME)
    script = script_path.read_text()
    preprocessor = Preprocessor(script, SCRIPT_NAME)
    for error in preprocessor.verify_event(SCRIPT_NAME, script):
        print(error)