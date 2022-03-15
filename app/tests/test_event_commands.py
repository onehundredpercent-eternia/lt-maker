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
        # Missing keyword
        command1, bad_idx = event_commands.parse_text_to_command("speak")
        self.assertTrue(command1 is None)
        # Test with tab in front
        command2, bad_idx = event_commands.parse_text_to_command("    speak;Eirika;I am evil;;60")
        self.assertTrue(isinstance(command2, event_commands.Speak))
        # Test with nickname
        command3, bad_idx = event_commands.parse_text_to_command("s;Eirika;I am evil")
        self.assertTrue(isinstance(command3, event_commands.Speak))
        # Test comments
        command4, bad_idx = event_commands.parse_text_to_command("#Hello")
        self.assertTrue(isinstance(command4, event_commands.Comment))
        command5, bad_idx = event_commands.parse_text_to_command("comment;Hello")
        self.assertTrue(isinstance(command5, event_commands.Comment))
        command6, bad_idx = event_commands.parse_text_to_command("flgjklskl;sumerian;lorem ipsum")
        self.assertTrue(isinstance(command6, event_commands.Comment))
        command7, bad_idx = event_commands.parse_text_to_command(None)
        self.assertTrue(command7 is None)
        command8, bad_idx = event_commands.parse_text_to_command("")
        self.assertTrue(command8 is None)

    def test_parse_text_to_command_strict(self):
        # Test with keyword arguments
        command1, bad_idx = event_commands.parse_text_to_command("set_current_hp;Unit=Seth;HP=13", strict=True)
        self.assertTrue(isinstance(command1, event_commands.SetCurrentHP))
        self.assertTrue(command1.parameters.get('Unit') == "Seth")
        self.assertTrue(command1.parameters.get('HP') == "13")
        self.assertTrue(len(command1.chosen_flags) == 0)
        self.assertTrue(bad_idx is None)
        # Test with flags and nickname
        command2, bad_idx = event_commands.parse_text_to_command("r;Seth;no_block", strict=True)
        self.assertTrue(isinstance(command2, event_commands.RemovePortrait))
        self.assertTrue(command2.parameters.get('Unit') == "Seth")
        self.assertTrue(command2.chosen_flags == {"no_block"})
        # Test with universal flags
        command3, bad_idx = event_commands.parse_text_to_command("set_current_hp;Seth;13;no_warn", strict=True)
        self.assertTrue(command3.chosen_flags == {"no_warn"})
        # Test with display values (use of parentheses)
        command4, bad_idx = event_commands.parse_text_to_command("set_current_hp;Seth (Seth);13", strict=True)
        self.assertTrue(command4.parameters.get('Unit') == "Seth")
        self.assertTrue(command4.parameters.get('HP') == "13")
        # Test with evaluables
        command5, bad_idx = event_commands.parse_text_to_command("if;Seth (Seth)", strict=True)
        self.assertTrue(command5.parameters.get('Expression') == "Seth (Seth)")
        # Test with positional arguments before keywords
        command6, bad_idx = event_commands.parse_text_to_command("set_current_hp;Seth;HP=13", strict=True)
        self.assertTrue(command6.parameters.get('Unit') == "Seth")
        self.assertTrue(command6.parameters.get('HP') == "13")
        # Test with invalid keyword argument
        command7, bad_idx = event_commands.parse_text_to_command("set_current_hp;Unit=Seth;13", strict=True)
        self.assertTrue(command7 is None)
        self.assertTrue(bad_idx == 1)
        # Test with using keyword types wrongly
        command8, bad_idx = event_commands.parse_text_to_command("set_current_hp;Unit=Seth;PositiveInteger=13", strict=True)
        self.assertTrue(command8 is None)
        self.assertTrue(bad_idx == 1)
        # Purposefully does not do validation of keyword arguments here,
        # so that other functions can use the full command when THEY do validation
        # Plus, validation often reuqires that the validator know what level is referred to
        # This ruins the atomic self-containedness of theis
        # parse_text_to_command is really a structural check, not a semantic check
        command9, bad_idx = event_commands.parse_text_to_command("set_current_hp;Unit=Seth;HP=lorem ipsum", strict=True)
        self.assertTrue(isinstance(command9, event_commands.SetCurrentHP))
        # Test with too many arguments
        command10, bad_idx = event_commands.parse_text_to_command("set_current_hp;Seth;13;Lorem Ipsum", strict=True)
        self.assertTrue(command10 is None)
        self.assertTrue(bad_idx == 2)
        # Test with non-existent keyword argument
        command11, bad_idx = event_commands.parse_text_to_command("set_current_hp;Seth;13;Lorem=Ipsum", strict=True)
        self.assertTrue(command11 is None)
        self.assertTrue(bad_idx == 2)
        # Test with missing keyword arguments
        command12, bad_idx = event_commands.parse_text_to_command("set_current_hp;Seth", strict=True)
        self.assertTrue(command12 is None)

    def test_parse(self):
        input_parameters = {"x": 1, "y": 2}
        x = event_commands.EventCommand(input_parameters, {"algebra"})
        parameters, flags = event_commands.parse(x)
        self.assertEqual(parameters, input_parameters)
        self.assertEqual(flags, {"algebra"})

    def test_convert_parse(self):
        input_parameters = {"x": 1, "y": 2}
        x = event_commands.EventCommand(input_parameters, {"algebra"})
        parameters, flags = event_commands.convert_parse(x)
        self.assertEqual(parameters, input_parameters)
        self.assertEqual(flags, {"algebra"})
        # Test with existing command and make sure it returns back parameters + flags
        command_parameters = {"Unit": "Seth", "HP": "13"}
        command1 = event_commands.SetCurrentHP(command_parameters, {"no_warn"})
        parameters, flags = event_commands.convert_parse(command1)
        self.assertEqual(parameters, command_parameters)
        self.assertEqual(flags, {"no_warn"})
        # Test with existing command and see if it runs convert using validators
        command_parameters = {"Speaker": "Seth", "TextSpeed": "5.5"}
        command2 = event_commands.SpeakStyle(command_parameters)
        parameters, flags = event_commands.convert_parse(command2)
        self.assertEqual(parameters, {"Speaker": "Seth", "TextSpeed": 5.5})
        self.assertTrue(len(flags) == 0)

    def test_save_and_restore(self):
        # Test save returns what we expect
        parameters = {"Unit": "Seth", "HP": "13"}
        command = event_commands.SetCurrentHP(parameters)
        dat = command.save()
        self.assertTrue(len(dat) == 2)
        self.assertEqual(dat[0] == command.nid)
        # Test restore correctly restores an event command
        command = event_commands.restore_command(dat)
        self.assertTrue(isinstance(command, event_commands.SetCurrentHP))
        self.assertEqual(command.parameters, parameters)

    def test_save_and_restore_comment(self):
        command = event_commands.Comment("Hello")
        dat = command.save()
        self.assertEqual(dat[0] == command.nid)
        command = event_commands.restore_command(dat)
        self.assertEqual(command.display_values, "Hello")

    def test_get_keyword_types(self):
        # Test that when keyword types exist, it returns that
        command = event_commands.SetCurrentHP()
        self.assertEqual(command.get_keyword_types(), command.keyword_types)
        # Test that when keyword types does not exist, it returns regular command
        command = event_commands.If()
        self.assertEqual(command.get_keyword_types(), command.keywords + command.optional_keywords)
        command = event_commands.AddPortrait()
        self.assertEqual(command.get_keyword_types(), command.keywords + command.optional_keywords)

    def test_get_validator_from_keyword(self):
        command = event_commands.Music()
        # Test validator from keywords
        self.assertEqual(command.get_validator_from_keyword("Music"), "Music")
        # Test validator from optional keywords
        self.assertEqual(command.get_validator_from_keyword("FadeIn"), "Time")

    def test_get_index_from_keyword(self):
        command, _ = event_commands.parse_text_to_command("add_portrait;ScreenPosition=Left;Slide=Left;Portrait=Eirika")
        self.assertTrue(isinstance(command, event_commands.AddPortrait))
        # Test keyword argument
        self.assertEqual(command.get_index_from_keyword("ScreenPosition"), 0)
        # Test positional argument
        self.assertEqual(command.get_index_from_keyword("Slide"), 1)
        self.assertEqual(command.get_index_from_keyword("Portrait"), 2)
