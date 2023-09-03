from __future__ import annotations
import re

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
