from __future__ import annotations
import re
from app.events.python_eventing.swscomp.comp_utils import COMMAND_SENTINEL, EventCommandData, ParseMode, ScriptWithSentinel

EOF = "EOF"

CLOSE_BRACES = {
    '{': '}',
    '[': ']',
    '(': ')'
}

class SWSCompilerV1():
    def __init__(self, event_script: str) -> None:
        self.source = event_script.replace('\u2029', ' ')

    @staticmethod
    def parse_str_to_event(line: str) -> EventCommandData:
        # should be of format:
        # $speak eirika "Hello" "This is a second line" (1, 2, 3), flag_1 flag_2
        # should correctly separate the above by spaces, respecting quotes and parens, and partitions the last pieces into flags

        mode = ParseMode.COMMAND
        tokens = []
        flags = []
        c_idx = 0
        c_tok = ''

        # remove $
        line = line[1:]
        # remove escaped newlines
        line = line.replace('\\\n', '')

        def advance():
            nonlocal c_idx
            c_idx = min(c_idx + 1, len(line))

        def fin_tok():
            nonlocal c_tok
            nonlocal mode
            if mode == ParseMode.FLAGS:
                flags.append(c_tok)
            else:
                tokens.append(c_tok)
            c_tok = ''

        def cadd(c: str):
            nonlocal c_tok
            c_tok += c

        def cchar() -> str:
            if c_idx < len(line):
                return line[c_idx]
            return EOF

        def peek():
            if c_idx + 1 < len(line):
                return line[c_idx + 1]
            return EOF

        while c_idx < len(line):
            c = cchar()
            if c in ("'", '"'):
                cadd(c)
                advance()
                while cchar() != c and cchar() != EOF:
                    nc = cchar()
                    cadd(nc)
                    advance()
                cadd(c)
            elif c in '([{':
                level = 1
                cc = CLOSE_BRACES[c]
                cadd(c)
                in_str = False
                while level != 0 and peek() != EOF:
                    advance()
                    nc = cchar()
                    cadd(nc)
                    if nc in ("'", '"'):
                        in_str = not in_str
                    if not in_str:
                        if nc == cc: # found close
                            level -= 1
                        elif nc == c: # found another open
                            level += 1
            elif c == ' ':
                if c_tok:
                    fin_tok()
                    if mode == ParseMode.COMMAND:
                        mode = ParseMode.ARGS
            elif c == ',':
                fin_tok()
                mode = ParseMode.FLAGS
            else:
                cadd(c)
            advance()
        fin_tok()
        if not tokens:
            tokens = ['']
        return EventCommandData(tokens[0], tokens[1:], flags, mode)

    def compile_sws(self) -> ScriptWithSentinel:
        # takes in a python event script
        # removes all event commands, and replaces them with COMMAND_SENTINEL
        # stores the parsed event commands as data

        # regex explanation: split on newlines not following
        # a backslash (escaped newline), and not following start-of-line
        as_lines = re.split(r'(?<=[^\\])\n|(?<=^)\n', self.source)
        found_commands = []
        for idx, line in enumerate(as_lines):
            if line.strip().startswith('$'):
                lpad = line.index("$")
                # insert command sentinel
                # replace newlines so the line count doesn't go out of whack
                as_lines[idx] = ' ' * lpad + COMMAND_SENTINEL + '\n' * line.count('\\\n')
                found_commands.append(SWSCompilerV1.parse_str_to_event(line.strip()))
        return ScriptWithSentinel('\n'.join(as_lines), found_commands)