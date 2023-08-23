from __future__ import annotations

import logging
from typing import List, Tuple

from app.engine.text_evaluator import TextEvaluator
from app.events import event_commands
from app.utilities.typing import NID


def create_generator_from_source(source: str):


class EventParser():
    def __init__(self, nid: NID, source: str):
        self.nid = nid
        self.gener

    def fetch_next_command(self) -> event_commands.EventCommand:
        if self.command_pointer >= len(self.commands):
            return None
        command = self.commands[self.command_pointer]
        self.logger.debug("Processing Event Line: %s", str(command))

        # conditional and loop handling
        if command.nid in ('if',):
            truth = self._get_truth(command)
            if truth:
                self.command_pointer += 1
            else:
                self.command_pointer = self._jump_conditional(self.command_pointer)
            return self.fetch_next_command()
        elif command.nid in ('elif', 'else'):
            # if we naturally navigate to elif/else,
            # implies we finished an if and should skip to the end
            # (because an if fails, we jump directly into the else)
            self.command_pointer = self._find_end(self.command_pointer)
            return self.fetch_next_command()
        elif command.nid == 'end':
            self.command_pointer += 1
            return self.fetch_next_command()
        elif command.nid in ('for'):
            if not self.iterator_stack or self.command_pointer != self.iterator_stack[-1].line:
                self.iterator_stack.append(self._build_iterator(self.command_pointer, command))
            else:
                self.iterator_stack[-1].iterator.next()
            if self.iterator_stack[-1].iterator.empty():
                self.iterator_stack.pop()
                self.command_pointer = self._find_end(self.command_pointer)
            else:
                self.command_pointer += 1
            return self.fetch_next_command()
        elif command.nid in ('endf'): # jump to iterator
            self.command_pointer = self.iterator_stack[-1].line
            return self.fetch_next_command()

        # ignore comments
        if isinstance(command, event_commands.Comment):
            self.command_pointer += 1
            return self.fetch_next_command()

        # normal command
        self.command_pointer += 1
        # evaluate and process command
        parameters, flags = event_commands.convert_parse(command, self._evaluate_all)
        # Handle the weird cases where we don't want to handle evaluation
        if command.nid == 'choice':
            unevaled_parameters, _ = event_commands.convert_parse(command, None)
            parameters['Choices'] = unevaled_parameters['Choices']
        elif command.nid == 'table':
            unevaled_parameters, _ = event_commands.convert_parse(command, None)
            parameters['TableData'] = unevaled_parameters['TableData']
        elif command.nid == 'textbox':
            unevaled_parameters, _ = event_commands.convert_parse(command, None)
            parameters['Text'] = unevaled_parameters['Text']
        processed_command = command.__class__(parameters, flags, command.display_values)
        return processed_command

    def finished(self):
        return self.command_pointer >= len(self.commands)

    def _object_to_str(self, obj) -> str:
        if hasattr(obj, 'uid'):
            return str(obj.uid)
        elif hasattr(obj, 'nid'):
            return str(obj.nid)
        else:
            return str(obj)

    def save(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['commands'] = self.commands
        s_dict['iterators'] = [info.save() for info in self.iterator_stack]
        s_dict['command_pointer'] = self.command_pointer
        return s_dict

    @classmethod
    def restore(cls, s_dict, text_evaluator: TextEvaluator):
        commands = s_dict['commands']
        nid = s_dict['nid']
        self = cls(nid, commands, text_evaluator)
        self.command_pointer = s_dict['command_pointer']
        self.iterator_stack = [IteratorInfo.restore(info_dict) for info_dict in s_dict['iterators']]
        return self
