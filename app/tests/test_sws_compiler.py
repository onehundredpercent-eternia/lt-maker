import logging
import unittest
from app.events.python_eventing.swscomp.comp_utils import EventCommandData, ParseMode
from app.events.python_eventing.swscomp.swscompv1 import SWSCompilerV1

class SWSCompilationTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    # def test_str_to_event(self):
    #     script = "$speak,"
    #     print(SWSCompilerV1.parse_str_to_event(script))

    def test_swscompilerv1(self):
        script = """
$speak eirika "Hello", no_block
for i in range(5):
    $speak "Seth" "Goodbye", yes_block
    $speak "Franz" "This is a"\\
           "multi-line command",\\
           maybe_block
    $half_finished_comman
    $finished_command ('not_done_with_arg',
"""


        expected_commands = [
            EventCommandData('speak', ['eirika', '"Hello"'], ['no_block'], ParseMode.FLAGS),
            EventCommandData('speak', ['"Seth"', '"Goodbye"'], ['yes_block'], ParseMode.FLAGS),
            EventCommandData('speak', ['"Franz"', '"This is a"', '"multi-line command"'], ['maybe_block'], ParseMode.FLAGS),
            EventCommandData('half_finished_comman', [], [], ParseMode.COMMAND),
            EventCommandData('finished_command', ["('not_done_with_arg',"], [], ParseMode.ARGS),
        ]
        # we should maintain whitespace (for indentation)
        # and newline count (for error logging)
        expected_source = """
__COMMAND_SENTINEL
for i in range(5):
    __COMMAND_SENTINEL
    __COMMAND_SENTINEL


    __COMMAND_SENTINEL
    __COMMAND_SENTINEL
"""

        res = SWSCompilerV1(script).compile_sws()
        self.assertEqual(res.source, expected_source)
        self.assertEqual(len(res.commands), len(expected_commands))
        for i in range(len(res.commands)):
            r = res.commands[i]
            exp = expected_commands[i]
            self.assertEqual(r.args, exp.args)
            self.assertEqual(r.command, exp.command)
            self.assertEqual(r.flags, exp.flags)