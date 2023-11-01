import logging
import unittest

from app.events.python_eventing.swscomp.comp_utils import EventCommandData

class CompilerUtilsUnitTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def testEventCommandDataToString(self):
        ec = EventCommandData("speak", ['eirika_var', '"I am speaking in a string"'], {'no_block'})
        expected = 'speak(eirika_var,"I am speaking in a string").set_flags("no_block")'
        self.assertEqual(ec.to_event_command_str(), expected)