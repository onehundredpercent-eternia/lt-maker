from __future__ import annotations
import ast
import re
from typing import List
import astpretty

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
      and not args to a Function call, not values in a BinOp, and not part of the for loop's iterator
      or while loop's test.
  """
  if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
    isinstance(node.func.value, ast.Name) and node.func.value.id == 'event':
    if not parents[-1] == ast.Expr:
      return False
    elif ast.FunctionDef in parents:
      return False
  return True

AST_LIST_STMT_FIELDS = ['body', 'values', 'args', 'orelse']
AST_STMT_FIELDS = ['value', 'test', 'iter', 'left', 'right']

def verify_event_calls(node: ast.stmt, parents: List[ast.stmt] = None):
  if parents is None:
    curr_parents = []
  else:
    curr_parents = parents[:]
  unsafe_event_function_calls: List[int] = []
  # base case
  if not check_safe_event_function_call(node, curr_parents):
    unsafe_event_function_calls.append(node.lineno)
  curr_parents.append(node.__class__)

  def check_recursive_property_list(property_name, unsafe_event_function_calls):
    # this is not relevant but will throw errors, so skip it
    if isinstance(node, ast.FunctionDef) and property_name == 'args':
      return
    if hasattr(node, property_name):
      for expr in getattr(node, property_name):
        unsafe_event_function_calls += verify_event_calls(expr, curr_parents)
  for list_stmt_prop in AST_LIST_STMT_FIELDS:
    check_recursive_property_list(list_stmt_prop, unsafe_event_function_calls)

  def check_recursive_property(property_name, unsafe_event_function_calls):
    if hasattr(node, property_name):
      unsafe_event_function_calls += verify_event_calls(getattr(node, property_name), curr_parents)
  for stmt_prop in AST_STMT_FIELDS:
    check_recursive_property(stmt_prop, unsafe_event_function_calls)

  return unsafe_event_function_calls

scr = \
"""
class SomeClass(OtherClass):
  def some_fun(self):
    event.d()
    event.e()

event.a() is 5
event.a(event.b())
"""

aslines = scr.split('\n')

p = ast.parse(scr)
print(astpretty.pprint(p))
unsafe_event_function_calls_lines = verify_event_calls(p)
print(unsafe_event_function_calls_lines)
for i in unsafe_event_function_calls_lines:
  print("failed compilation", aslines[i - 1])