import re

from app.utilities import utils
from app.constants import WINWIDTH, WINHEIGHT
from app.engine.fonts import FONT
from app.engine.sprites import SPRITES
from app.engine import text_funcs, engine, image_mods, dialog
from app.engine import config as cf

class MementoDialogBackground():
    background = SPRITES.get('memento_dialog_background')
    transition_in_speed = 1660  # 10 frames
    transition_out_speed = 1660  # 10 frames

    def __init__(self):
        # off, transition_in, normal, transition_out
        self.state = 'off'
        self.transition_progress = 0
        self.last_update = engine.get_time()
        self.height = self.background.get_height()
        self.position = (0, WINHEIGHT - self.height)

    def update(self) -> bool:
        # Returns true if in normal state
        current_time = engine.get_time()

        if self.state == 'transition_in':
            perc = (current_time - self.last_update) / self.transition_in_speed
            self.transition_progress = utils.clamp(perc, 0, 1)
            if self.transition_progress == 1:
                self.state = 'normal'

        elif self.state == 'transition_out':
            perc = (current_time - self.last_update) / self.transition_out_speed
            self.transition_progress = utils.clamp(perc, 0, 1)
            if self.transition_progress == 1:
                self.state = 'off'

        return self.state == 'normal'

    def start(self):
        self.state = 'transition_in'
        self.transition_progress = 0
        self.last_update = engine.get_time()

    def end(self):
        self.state = 'transition_out'
        self.transition_progress = 0
        self.last_update = engine.get_time()

    def ready(self):
        return self.state == 'normal'

    def draw(self, surf):
        if self.state == 'transition_in':
            new_width = max(1, self.background.get_width() - 10 + int(10*self.transition_progress))
            new_height = max(1, self.background.get_height() - 10 + int(10*self.transition_progress))
            bg = engine.transform_scale(self.background, (new_width, new_height))
            bg = image_mods.make_translucent(bg, (1 - self.transition_progress))
            surf.blit(bg, (self.position[0], self.position[1] + self.height//2 - bg.get_height()//2))
        elif self.state == 'transition_out':
            new_width = max(1, self.background.get_width() - 10 - int(10*self.transition_progress))
            new_height = max(1, self.background.get_height() - 10 - int(10*self.transition_progress))
            bg = engine.transform_scale(self.background, (new_width, new_height))
            bg = image_mods.make_translucent(bg, self.transition_progress)
            surf.blit(bg, (self.position[0], self.position[1] + self.height//2 - bg.get_height()//2))
        else:
            surf.blit(self.background, self.position)

class MementoDialog(dialog.Dialog):
    solo_flag = True
    cursor = SPRITES.get('waiting_cursor')
    name_tag = SPRITES.get('memento_nametag')
    draw_cursor_flag = False
    pause_before_wait_time = 150  # 9 frames
    pause_time = 150  # 9 frames
    text_width = WINWIDTH - 40
    text_height = 64

    def __init__(self, text, background, portrait=None):
        self.plain_text = text
        self.background = background
        self.portrait = portrait
        self.speaker = self.portrait.name
        self.font_type = 'convo'
        self.font_color = 'black'
        self.font = FONT[self.font_type + '-' + self.font_color]

        # States: 
        # transition_in -- waiting for the dialog box to appear
        # write -- actually adding text to the screen, one character at a time
        # pause -- occasionally pauses for a period
        # pause_before_wait -- will pause for some time between write and wait states (to account for player mashing A)
        # wait -- Done writing, now waiting for the player to press A
        # done -- No more dialog to show, waiting for the event to clean me up
        # transition_out -- waiting for the dialog box to disappear
        self.state = 'transition_in'

        self.no_wait: bool = False  # Whether to wait for the player to press
        self.text_commands = self.format_text(text)
        self.text_blocks = self.get_text_blocks()
        self.current_block = 0

        # Size & Position
        self.num_lines = self.determine_num_lines(self.current_block)

        # For drawing
        self.text_index = 0
        self.text_lines = []
        self.total_num_updates = 0

        # For state transitions
        self.last_update = engine.get_time()

        # For sound
        self.last_sound_update = 0

    def get_text_blocks(self) -> list:
        blocks = []
        current_block = []
        for command in self.text_commands:
            if command in ('{w}', '{wait}', '{clear}'):
                blocks.append(current_block)
                current_block = []
            else:
                current_block.append(command)
        return blocks

    def line_wrap(self, line: str) -> list:
        max_line_width = self.text_width
        return text_funcs.line_wrap(self.font, line, max_line_width)

    def determine_num_lines(self, current_block: int) -> int:
        # Figure out how many lines we need to display this
        block: list = self.text_blocks[current_block]
        lines = []
        current_line = ''
        for command in block:
            if command in ('{br}', '{break}'):
                new_lines = self.line_wrap(current_line)
                lines += new_lines
                current_line = ''
            elif command.startswith('{'):
                pass
            else:
                current_line += command
        new_lines = self.line_wrap(current_line)
        lines += new_lines
        num_lines = len(lines)
        return num_lines

    def _next_line(self):
        self.text_lines.append([])

    def _add_letter(self, letter):
        self.text_lines[-1].append(letter)

    def _next_char(self, sound=True):  # Add the next character to the text_lines list
        if self.text_index >= len(self.text_commands):
            self.pause_before_wait()
            return
        command = self.text_commands[self.text_index]
        if command == '{br}' or command == '{break}':
            self._next_line()
        elif command == '{w}' or command == '{wait}':
            self.pause_before_wait()
        elif command == '{clear}':
            self._next_block()
        elif command == ' ':  # Check to see if we should move to next line
            current_line = ''.join(self.text_lines[-1])
            # Remove any commands from line
            current_line = re.sub(r'\{[^}]*\}', '', current_line)
            next_word = self._get_next_word(self.text_index)
            if self.font.width(current_line + ' ' + next_word) > self.text_width:
                self._next_line()
            else:
                self._add_letter(' ')
        elif command in self.aesthetic_commands:
            self._add_letter(command)
        elif command in ('.', ',', ';', '!', '?'):
            self._add_letter(command)
            self.pause()
        else:
            self._add_letter(command)
        self.text_index += 1

    def _get_next_word(self, text_index):
        word = ''
        for letter in self.text_commands[self.text_index + 1:]:
            if letter == ' ':
                break
            elif len(letter) > 1:  # Command
                if letter in self.aesthetic_commands:
                    continue
                else:
                    break
            else:
                word += letter
        return word

    def _next_block(self):
        self.text_lines.clear()
        self._next_line()
        self.current_block += 1
        self.num_lines = self.determine_num_lines(self.current_block)

    def is_complete(self):
        """
        Should no longer be drawn
        """
        return self.state == 'transition_out'

    def is_done(self):
        """
        Can move onto processing other commands
        """
        return self.state == 'done'

    def is_done_or_wait(self):
        return self.state in ('done', 'wait')

    def pause(self):
        self.state = 'pause'
        self.last_update = engine.get_time()

    def pause_before_wait(self):
        self.state = 'pause_before_wait'
        self.last_update = engine.get_time()

    def hurry_up(self):
        if self.state == 'write':
            while self.state == 'write':
                self._next_char()
                # Skip regular pauses
                if self.state == 'pause':
                    self.state = 'write'
        elif self.state == 'wait':
            if self.text_index >= len(self.text_commands):
                self.state = 'done'
            else:
                self._next_block()
                self.state = 'write'

    def update(self):
        current_time = engine.get_time()

        if self.state == 'transition_in':
            if self.background.ready():
                self._next_line()
                self.state = 'write'
        elif self.state == 'transition_out':
            self.background.update()
        elif self.state == 'write':
            if cf.SETTINGS['text_speed'] > 0:
                num_updates = engine.get_delta() / float(cf.SETTINGS['text_speed'])
                self.total_num_updates += num_updates
                while self.total_num_updates >= 1 and self.state == 'write':
                    self.total_num_updates -= 1
                    self._next_char()
                    if self.state != 'write':
                        self.total_num_updates = 0
            else:
                while self.state == 'write':
                    self._next_char()
                    # Skip regular pauses
                    if self.state == 'pause':
                        self.state = 'write'
        elif self.state == 'pause_before_wait':
            if current_time - self.last_update > self.pause_before_wait_time:
                if self.no_wait:
                    self.state = 'done'
                else:
                    self.state = 'wait'
        elif self.state == 'pause':  # Regular pause for periods
            if current_time - self.last_update > self.pause_time:
                self.state = 'write'

    def draw_text(self, surf):
        text_surf = engine.create_surface((self.text_width, self.text_height), transparent=True)

        current_color = self.font_color

        for idx, line in enumerate(self.text_lines):
            x_pos = 0
            y_pos = 16 * idx + (8 * (4 - self.num_lines))

            line_chunks, current_color = self.chunkify(line, current_color)
            for chunk in line_chunks:
                text, color = chunk
                font = FONT[self.font_type + '-' + color]
                width = font.width(text)
                font.blit(text, text_surf, (x_pos, y_pos))
                x_pos += width

        surf.blit(text_surf, (20, WINHEIGHT - 64 - 12))

    def draw_nametag(self, surf, name):
        if self.portrait:
            position = self.portrait.position
            x_pos = position[0] - 4
            y_pos = position[1] + 118
            if x_pos < 0:
                x_pos = position[0] + 16
        else:
            x_pos, y_pos = (8, 8)
        name_tag_surf = self.name_tag.copy()
        FONT['text-white'].blit_center(name, name_tag_surf, (name_tag_surf.get_width()//2, name_tag_surf.get_height()//2 - self.font.height//2))
        surf.blit(name_tag_surf, (x_pos, y_pos))
        return surf

    def draw(self, surf):
        if self.state not in ('transition_in', 'transition_out'):
            # Draw nametag
            if self.portrait:
                self.draw_nametag(surf, self.speaker)
            # Draw text
            self.draw_text(surf)

            if self.state == 'wait' and self.draw_cursor_flag:
                cursor_pos = WINWIDTH//2 - self.cursor.get_width()//2, WINHEIGHT - 24
                surf.blit(self.cursor, cursor_pos)

        return surf
