import logging
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from app.events import event_commands
from app.events.python_eventing.python_event_parser import PythonEventParser
from app.tests.mocks.mock_game import get_mock_game


class PythonEventParserUnitTests(unittest.TestCase):
    def setUp(self):
        self.mock_game = get_mock_game()
        mock_unit = MagicMock()
        mock_unit.name = "Erika" # deliberate spelling
        get_unit = lambda name: mock_unit
        self.mock_game.get_unit = get_unit
        self.mock_game.level_vars = {"TimesRescued": 10}
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_event_parser(self):
        script_path = Path(__file__).parent / 'data' / 'python_parser' / 'test_event.pyevent'
        script_source = script_path.read_text()
        parser = PythonEventParser('test', script_source)

        # normal command
        mu_speak = parser.fetch_next_command()
        self.assertTrue(isinstance(mu_speak, event_commands.Speak))
        self.assertEqual(mu_speak.parameters['Speaker'], 'MU')
        self.assertEqual(mu_speak.parameters['Text'], 'I am a custom named character.')

        # eval
        seth_speak = parser.fetch_next_command()
        self.assertTrue(isinstance(seth_speak, event_commands.Speak))
        self.assertEqual(seth_speak.parameters['Speaker'], 'Seth')
        self.assertEqual(seth_speak.parameters['Text'], 'Princess Erika!')

        # variable
        rescue_speak = parser.fetch_next_command()
        self.assertTrue(isinstance(rescue_speak, event_commands.Speak))
        self.assertEqual(rescue_speak.parameters['Speaker'], 'MU')
        self.assertEqual(rescue_speak.parameters['Text'], "You've rescued me 10 times.")

        # if/else/processing
        iftrue_speak = parser.fetch_next_command()
        self.assertTrue(isinstance(iftrue_speak, event_commands.Speak))
        self.assertEqual(iftrue_speak.parameters['Speaker'], 'MU')
        self.assertEqual(iftrue_speak.parameters['Text'], "A bit ridiculous, isn't it?")

        # for
        eirika_for = parser.fetch_next_command()
        seth_for = parser.fetch_next_command()
        self.assertTrue(isinstance(eirika_for, event_commands.Speak))
        self.assertEqual(eirika_for.parameters['Speaker'], 'Eirika')
        self.assertEqual(eirika_for.parameters['Text'], "My name is Eirika.")
        self.assertTrue(isinstance(seth_for, event_commands.Speak))
        self.assertEqual(seth_for.parameters['Speaker'], 'Seth')
        self.assertEqual(seth_for.parameters['Text'], "My name is Seth.")

    def test_save_restore_parser_state(self):
        script_path = Path(__file__).parent / 'data' / 'python_parser' / 'test_event.pyevent'
        script_source = script_path.read_text()
        parser = PythonEventParser('test', script_source)

        parser.fetch_next_command()
        parser.fetch_next_command()
        parser.fetch_next_command()
        parser.fetch_next_command()
        # parser just returned "speak;MU;A bit ridiculous, isn't it?"

        new_parser = PythonEventParser.restore(parser.save())
        self.assertEqual(new_parser.nid, 'test')
        next_command = new_parser.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Speak))
        self.assertEqual(next_command.parameters['Speaker'], 'Eirika')
        self.assertEqual(next_command.parameters['Text'], "My name is Eirika.")