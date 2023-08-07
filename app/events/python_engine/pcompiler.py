from __future__ import annotations
import ast
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple
from ..event_commands import ALL_EVENT_COMMANDS


def check_safe_event_function_call(node: ast.stmt, parents: List[type]):
  """Expectations: if 'node' is an EventFunction call, e.g. 'event.speak(*args)'
      and the parents are the ast nodes above it. We assert that the immediate
      parent must be an solitary Expr, and that this cannot be nested in a function.

    Rationale:
      The core concept of this event engine is this: that we can yield
      on every call to the EventEngine, thus allowing us to cede control
      to the engine's state machine and execute the EventFunction.
      Once the EventFunction is executed, we then return control
      to the EventEngine, which can resume the execution of the script,
      until the next EventFunction is hit, which is then yielded, control ceded,
      etc.

      Therefore, the most important rule is that every single event function
      *can* be yielded one-by-one. This fails, for example, for the line,
      `event.speak(args...) and event.speak(args2...)`. This line tries to
      execute both speak commands at once, which is not how the EventEngine
      works. Therefore, it is invalid. Likewise, creating a function definition
      with multiple EventFunctions and then calling them would also be problematic.

      Therefore, we must be sure to uphold that EventFunctions are *always* yieldable, i.e.
      either top-level Exprs, or equivalent (in the bodies of for and while-loops, which can be yielded)
      and not args to a Function call, not values in e.g. a BinOp, and not part of the for loop's iterator
      or while loop's test.
  """
  if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
    isinstance(node.func.value, ast.Name) and node.func.value.id == 'event':
    if not parents[-1] == ast.Expr:
      return False
    elif ast.FunctionDef in parents:
      return False
  return True

FORBIDDEN_PYTHON_COMMANDS: List[str] = []

def check_valid_event_function_call(node: ast.stmt):
  if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
    isinstance(node.func.value, ast.Name) and node.func.value.id == 'event':
    event_command_nid = node.func.attr
    if not event_command_nid in ALL_EVENT_COMMANDS:
        return False
    if event_command_nid in FORBIDDEN_PYTHON_COMMANDS:
        return False
    return True

AST_LIST_STMT_FIELDS = ['body', 'values', 'args', 'orelse']
AST_STMT_FIELDS = ['value', 'test', 'iter', 'left', 'right']

# aslines = scr.split('\n')

# import astpretty
# p = ast.parse(scr)
# print(astpretty.pprint(p))
# unsafe_event_function_calls_lines = verify_event_calls(p)
# print(unsafe_event_function_calls_lines)
# for i in unsafe_event_function_calls_lines:
#   print("failed compilation", aslines[i - 1])

class ErrorType(Enum):
    NESTED_ERROR = "NestedEventError"
    INVALID_COMMAND_ERROR = "InvalidEventCommandError"

@dataclass
class PreprocessorError():
    what: str

    @classmethod
    def nested_event_call(cls, event_name: str, lnum: int, line: str):
        what = \
"""Event "{event_name}", Line {lnum}:
{line}
NestedEventError: all event funcs must be top level and outside function def""".format(event_name=event_name, lnum=lnum, line=line)
        return cls(what)

class Preprocessor():
    def __init__(self, script: str, event_name: str) -> None:
        self._event_name = event_name
        self._source = script
        self._as_lines = script.split("\n")
        self._as_ast = ast.parse(script)

    def preprocess(self):
        pass

    def identify_unsafe_event_functions(self) -> List[PreprocessorError]:
        unsafe_event_function_lines = Preprocessor.verify_event_calls(self._as_ast)
        return [PreprocessorError.nested_event_call(self._event_name, i, self._as_lines[i]) for i in unsafe_event_function_lines]

    def identify_invalid_event_functions(self) -> List[PreprocessorError]:
        pass

    @staticmethod
    def verify_event_calls(node: ast.stmt, parents: List[ast.stmt] = None) -> List[Tuple[ErrorType, int]]:
        if parents is None:
            curr_parents = []
        else:
            curr_parents = parents[:]
        unsafe_event_function_calls: List[Tuple[ErrorType, int]] = []
        # base case
        if not check_safe_event_function_call(node, curr_parents):
            unsafe_event_function_calls.append((ErrorType.NESTED_ERROR, node.lineno))
        if not check_valid_event_function_call(node):
            unsafe_event_function_calls.append((ErrorType.INVALID_COMMAND_ERROR, node.lineno))
        curr_parents.append(node.__class__)

        def check_recursive_property_list(property_name, unsafe_event_function_calls):
            # this is not relevant but will throw errors, so skip it
            if isinstance(node, ast.FunctionDef) and property_name == 'args':
                return
            if hasattr(node, property_name):
                for expr in getattr(node, property_name):
                    unsafe_event_function_calls += Preprocessor.verify_event_calls(expr, curr_parents)

        for list_stmt_prop in AST_LIST_STMT_FIELDS:
            check_recursive_property_list(list_stmt_prop, unsafe_event_function_calls)

        def check_recursive_property(property_name, unsafe_event_function_calls):
            if hasattr(node, property_name):
                unsafe_event_function_calls += Preprocessor.verify_event_calls(getattr(node, property_name), curr_parents)
        for stmt_prop in AST_STMT_FIELDS:
            check_recursive_property(stmt_prop, unsafe_event_function_calls)

        return unsafe_event_function_calls

# python -m app.events.python_engine.pcompiler
if __name__ == '__main__':
    from pathlib import Path
    script_path = Path(__file__).with_name('example_script.txt')
    script = script_path.read_text()
    print(script)
    import astpretty
    p = ast.parse(script)
    print(astpretty.pprint(p))