from __future__ import annotations
from logging import getLogger
import re
from typing import TYPE_CHECKING, Generator
from unittest import mock
import ast

if TYPE_CHECKING:
    from app.engine.game_state import GameState

COMMAND_REGEX = re.compile(r'\$(.*?)\(.*')

def ast_preprocess(script: str):
    # turns all `$command(args)` -> `EC.command(args)`
    as_lines = script.split('\n')
    for idx, line in enumerate(as_lines):
        match = COMMAND_REGEX.match(line.strip())
        if match:
            matched = match.groups() # length 2 because of the COMMAND_REGEX
            line = line.replace('$%s(' % matched[0], 'EC.%s(' % matched[0])
            as_lines[idx] = line
    return '\n'.join(as_lines)

def insert_yields_and_command_pointer(script: str):
    # turns `$command(args)` -> `yield DO_NOT_EXECUTE_SENTINEL if _PTR >= 1 else $(line_num), EC.command(args)`
    as_lines = script.split('\n')
    for idx, line in enumerate(as_lines):
        match = COMMAND_REGEX.match(line.strip())
        if match:
            matched = match.groups()
            line = line.replace('$%s(' % matched[0], 'yield DO_NOT_EXECUTE_SENTINEL if (_PTR >= %d and RESUME_CHECK.check_set_caught_up(%d)) else %d, EC.%s(' % (idx, idx, idx, matched[0]))
            as_lines[idx] = line
    return '\n'.join(as_lines)

def _get_yield_value(node: ast.Yield):
    return node.value.elts[0].orelse.n

def insert_command_pointer_conditional_skips(script_with_yields: str):
    parsed = ast.parse(script_with_yields)

    def fetch_pointers_under_conditional(cond_node: ast.If | ast.While):
        starting_nodes = cond_node.body
        def recursive_fetch_yields(node: ast.stmt):
            pointers_found = []
            for cnode in ast.iter_child_nodes(node):
                if isinstance(cnode, ast.Yield):
                    pointers_found.append(_get_yield_value(cnode))
                else:
                    pointers_found += recursive_fetch_yields(cnode)
            return pointers_found
        return [line_pointer for cnode in starting_nodes for line_pointer in recursive_fetch_yields(cnode)]

    as_lines = script_with_yields.split('\n')
    # inefficient algorithm with no memoization - i don't expect this to be a huge bottleneck
    for cnode in ast.walk(parsed):
        if isinstance(cnode, ast.If) or isinstance(cnode, ast.While):
            pointers_in_conditional = fetch_pointers_under_conditional(cnode)
            line = as_lines[cnode.lineno - 1]
            if isinstance(cnode, ast.If):
                # line starts with if or elif
                line = line.replace('if', 'if _PTR in [%s] or' % ', '.join([str(i) for i in pointers_in_conditional]), 1)
                as_lines[cnode.lineno - 1] = line
            else:
                line = line.replace('while', 'while (_PTR in [%s] and RESUME_CHECK.catching_up) or' % ', '.join([str(i) for i in pointers_in_conditional]), 1)
                as_lines[cnode.lineno - 1] = line

    return '\n'.join(as_lines)

def wrap_generator(script: str, generator_func_name: str, resume_command_pointer = -1):
    # wraps the entire script in a generator
    as_lines = script.split("\n")
    as_lines = ["\t%s" % line for line in as_lines]
    as_lines = ["_PTR = %d" % resume_command_pointer, "def %s():" % generator_func_name] + as_lines
    if resume_command_pointer:
        as_lines = ['RESUME_CHECK = ResumeCheck(%d)' % resume_command_pointer] + as_lines
    return '\n'.join(as_lines)

HEADER_IMPORT = """
import app.events.python_eventing.python_event_command_wrappers as EC
from app.events.python_eventing.utils import DO_NOT_EXECUTE_SENTINEL, ResumeCheck
"""
def insert_header(script: str):
    """Insert necessary imports for the environment"""
    script = HEADER_IMPORT + '\n' + script
    return script

class Compiler():
    @staticmethod
    def compile(script: str, game: GameState, command_pointer: int = 0) -> Generator:
        script = insert_yields_and_command_pointer(script)
        script = insert_command_pointer_conditional_skips(script)
        script = wrap_generator(script, "g", command_pointer)
        script = insert_header(script)
        exec_context = {'game': game}
        exec_context.update(game.query_engine.func_dict)
        exec(script, exec_context)
        return exec_context['g']()

# python -m app.events.python_eventing.compilation
if __name__ == '__main__':
    from pathlib import Path
    from unittest.mock import MagicMock
    from app.engine.query_engine import GameQueryEngine
    import astpretty
    script_path = Path(__file__).with_name('example_script_no_errors.txt')
    script = script_path.read_text()

    dummy_game = MagicMock()
    dummy_game.query_engine = GameQueryEngine(getLogger(), dummy_game)
    dummy_game.game_vars = {'TimesRescued': 10}
    dummy_game.level_vars = {}
    dunit = MagicMock()
    dunit.name = 'MU_NAME'
    dummy_game.get_unit = lambda x: dunit

    generator = Compiler.compile(script, dummy_game)
    while True:
        print(next(generator))
    yielded = insert_yields_and_command_pointer(script)
    p = ast.parse(yielded)
    astpretty.pprint(p)
    print(yielded)
    print(insert_command_pointer_conditional_skips(yielded))