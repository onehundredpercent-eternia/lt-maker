import unittest

from app.events import event_commands

class EventCommandUnitTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_subclasses(self):
        # Make sure there are some commands
        commands = event_commands.get_commands()
        self.assertTrue(len(commands) > 0)
        # Make sure that speak exists as a command
        self.assertTrue(any(command.nid == 'speak' for command in commands))

    def test_determine_command_type(self):
        command1 = event_commands.determine_command_type("speak")
        self.assertTrue(isinstance(command1, event_commands.Speak))
        # Test with tab in front
        command2 = event_commands.determine_command_type("    speak;Eirika;I am evil;;60")
        self.assertTrue(isinstance(command2, event_commands.Speak))

    def test_determine_command_type_nickname(self):
        command = event_commands.determine_command_type("s;Eirika;I am evil;;60")
        self.assertTrue(isinstance(command, event_commands.Speak))

    def test_determine_command_type_comment(self):
        command1 = event_commands.determine_command_type("#Hello")
        self.assertTrue(isinstance(command1, event_commands.Comment))
        command2 = event_commands.determine_command_type("comment;Hello")
        self.assertTrue(isinstance(command2, event_commands.Comment))

    def test_determine_command_type_fails(self):
        command = event_commands.determine_command_type("flgjklskl;sumerian;lorem ipsum")
        self.assertTrue(isinstance(command, event_commands.Comment))

    def test_parse_text_to_command_typing(self):
        command1, bad_idx = event_commands.determine_command_type("speak")
        self.assertTrue(isinstance(command1, event_commands.Speak))
        # Test with tab in front
        command2, bad_idx = event_commands.determine_command_type("    speak;Eirika;I am evil;;60")
        self.assertTrue(isinstance(command2, event_commands.Speak))
        # Test with nickname
        command3, bad_idx = event_commands.determine_command_type("s;Eirika;I am evil;;60")
        self.assertTrue(isinstance(command3, event_commands.Speak))
        # Test comments
        command4, bad_idx = event_commands.determine_command_type("#Hello")
        self.assertTrue(isinstance(command4, event_commands.Comment))
        command5, bad_idx = event_commands.determine_command_type("comment;Hello")
        self.assertTrue(isinstance(command5, event_commands.Comment))
        command6, bad_idx = event_commands.determine_command_type("flgjklskl;sumerian;lorem ipsum")
        self.assertTrue(isinstance(command6, event_commands.Comment))
        command7, bad_idx = event_commands.determine_command_type(None)
        self.assertTrue(command7 is None)
        command8, bad_idx = event_commands.determine_command_type("")
        self.assertTrue(command8 is None)

    def test_parse_text_to_command_strict(self):
        # Test with keyword arguments
        # Test with flags
        # Test with universal flags
        # Test with display values (use of parentheses)
        # Test with evaluables
        # Test with positional arguments before keywords
        # Test with invalid keyword argument
        # Test with bad idx returning something interesting
        # Test with too many arguments

    def test_parse(self):
        # Test with existing command and make sure it returns back parameters + flags

    def test_convert_parse(self):
        # Test with existing command and make sure it returns back parameters + flags
        # Test with existing command and see if it runs convert using validators

    def test_save_and_restore(self):
        # Test save returns what we expect
        # Test restore correctly restores an event command

    def test_get_keyword_types(self):
        # Test that when keyword types exist, it returns that
        # Test that when keyword types does not exist, it returns regular command

    def test_get_validator_from_keyword(self):
        # Test validator from keywords
        # Test validator from optional keywords

    def test_get_index_from_keyword(self):
        # Test keyword argument
        # Test positional argument
