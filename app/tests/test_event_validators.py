import logging
import unittest
from unittest.mock import MagicMock
from app.events import event_validators

from app.events.event_commands import ALL_EVENT_COMMANDS

class EventValidatorTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_all_types_have_validators(self):
        for command_type in ALL_EVENT_COMMANDS.values():
            if command_type.keyword_types:
                found_types = set(command_type.keyword_types)
            else:
                found_types = set(command_type.keywords)
                found_types |= set(command_type.optional_keywords)
            for t in found_types:
                self.assertTrue(event_validators.get(t) != None, "Type '%s' in CommandType '%s' has no associated Validator" % (t, command_type.nid))