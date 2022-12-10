import re

from app.utilities import utils
from app.utilities.algorithms.interpolation import lerp
from app.constants import WINWIDTH, WINHEIGHT
from app.engine.fonts import FONT
from app.engine.sprites import SPRITES
from app.engine import text_funcs, engine, image_mods, dialog, base_surf
from app.engine import config as cf
from app.engine.graphics.text.text_renderer import (fix_tags, render_text,
                                                    text_width)

class FancyDialogBackground():
    background = base_surf.create_base_surf(WINWIDTH, 80, 'fancy_dialog_bg')
    background = background.convert_alpha()
    transition_in_speed = utils.frames2ms(12)
    transition_out_speed = utils.frames2ms(10)

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
            new_width = int(max(1, self.background.get_width() * self.transition_progress))
            new_height = max(1, self.background.get_height() - 10 + int(10*self.transition_progress))
            bg = engine.transform_scale(self.background, (new_width, new_height))
            bg = image_mods.make_translucent(bg, (1 - self.transition_progress))
            surf.blit(bg, (self.position[0] + self.background.get_width()//2 - new_width//2, self.position[1] + self.height//2 - bg.get_height()//2))
        elif self.state == 'transition_out':
            new_width = max(1, self.background.get_width() - 10 - int(10*self.transition_progress))
            new_height = max(1, self.background.get_height() - 10 - int(10*self.transition_progress))
            bg = engine.transform_scale(self.background, (new_width, new_height))
            bg = image_mods.make_translucent(bg, self.transition_progress)
            surf.blit(bg, (self.position[0], self.position[1] + self.height//2 - bg.get_height()//2))
        elif self.state == 'normal':
            surf.blit(self.background, self.position)

class FancyDialogNametag():
    sprite = SPRITES.get('fancy_nametag')
    sprite = sprite.convert_alpha()
    transition_in_speed = utils.frames2ms(12)
    transition_out_speed = utils.frames2ms(10)
    movement_speed = 32
    default_pos = (WINWIDTH//2 - sprite.get_width(), 94)

    def __init__(self):
        self.state = 'off'  # off, transition_in, on, transition_out
        self.font = FONT['text']
        self.last_update = engine.get_time()
        self.transition_progress = 0
        self.current_position = self.default_pos

    def start(self):
        self.last_update = engine.get_time()
        self.state = 'transition_in'

    def end(self):
        self.last_update = engine.get_time()
        self.state = 'transition_out'

    def update(self, portrait):
        current_time = engine.get_time()
        if self.state == 'off':
            if portrait:
                self.start()
        elif self.state == 'transition_in':
            perc = (current_time - self.last_update) / self.transition_in_speed
            self.transition_progress = utils.clamp(perc, 0, 1)
            if self.transition_progress == 1:
                self.state = 'on'
        elif self.state == 'transition_out':
            perc = (current_time - self.last_update) / self.transition_out_speed
            self.transition_progress = utils.clamp(perc, 0, 1)
            if self.transition_progress == 1:
                self.state = 'off'
                self.current_position = self.default_pos
        elif self.state == 'on':
            if not portrait:
                self.end()

    def draw(self, surf, portrait, name):
        if self.state == 'off':
            return surf

        if portrait:
            position = portrait.position
            x_pos = position[0] + 16
            y_pos = position[1] + 74
            if x_pos < 0:
                x_pos = position[0] + 32
        else:
            x_pos, y_pos = self.default_pos
        # Move sprite
        desired_position = x_pos, y_pos
        if desired_position != self.current_position:
            x_offset = desired_position[0] - self.current_position[0]
            y_offset = desired_position[1] - self.current_position[1]
            x_speed = utils.sign(x_offset) * self.movement_speed
            y_speed = utils.sign(y_offset) * self.movement_speed
            self.current_position = int(self.current_position[0] + x_speed), int(self.current_position[1] + y_speed)
            if abs(x_offset) < self.movement_speed:
                self.current_position = (desired_position[0], self.current_position[1])
            if abs(y_offset) < self.movement_speed:
                self.current_position = (self.current_position[0], desired_position[1])

        name_tag_surf = self.sprite.copy()

        self.font.blit_center(name, name_tag_surf, (name_tag_surf.get_width()//2, name_tag_surf.get_height()//2 - self.font.height//2))
        if self.state == 'transition_in':
            name_tag_surf = image_mods.make_translucent(name_tag_surf, 1 - self.transition_progress)
        elif self.state == 'transition_out':
            name_tag_surf = image_mods.make_translucent(name_tag_surf, self.transition_progress)
        surf.blit(name_tag_surf, self.current_position)
        return surf

class FancyDialogCursor():
    sprite = SPRITES.get('waiting_cursor_red')
    sprite = sprite.convert_alpha()
    pulse_sprite = SPRITES.get('waiting_cursor_pulse')
    cursor_offset = [0]*20 + [1]*2 + [2]*8 + [1]*2

    def __init__(self):
        self.main_image = engine.subsurface(self.sprite, (0, 0, 32, 32))
        self.anims = [engine.subsurface(self.sprite, (i*32, 0, 32, 32)) for i in range(1, self.sprite.get_width()//32)]
        self.anim_counter = 0
        self.waiting = False
        self.last_update = engine.get_time()
        self.wait_start_time = 0

    def start(self):
        self.anim_counter = 4
        self.waiting = False

    def flip(self):
        self.anim_counter = 1
        self.waiting = False

    def wait(self):
        self.waiting = True
        self.wait_start_time = engine.get_time()

    def draw(self, surf):
        if engine.get_time() - self.last_update > 1000:
            self.start()
        self.last_update = engine.get_time()

        # if self.waiting:
        #     current_time = engine.get_time()
        #     y_offset = self.cursor_offset[int(current_time / FRAMERATE) % len(self.cursor_offset)]
        # else:
        y_offset = 0

        if self.waiting:
            current_time = engine.get_time() - self.wait_start_time
            progress = utils.model_wave(current_time, 1500, 1000)
            size = int(lerp(32, 64, progress))
            im = self.pulse_sprite.copy()
            im = engine.transform_scale(im, (size, size))
            x, y = WINWIDTH//2 - size//2, WINHEIGHT - 8 - size//2
            # surf.blit(im, (x, y))
            engine.blit(surf, im, (x, y), None, engine.BLEND_RGB_ADD)

        if self.anim_counter:
            im = self.anims[self.anim_counter - 1]
            pos = WINWIDTH//2 - im.get_width()//2, WINHEIGHT - 24 + y_offset
            surf.blit(im, pos)
            self.anim_counter += 1
            if self.anim_counter >= len(self.anims):
                self.anim_counter = 0
        else:
            pos = WINWIDTH//2 - self.main_image.get_width()//2, WINHEIGHT - 24 + y_offset
            surf.blit(self.main_image, pos)

class FancyDialog(dialog.Dialog):
    solo_flag = True
    draw_cursor_flag = True
    pause_before_wait_time = 150  # 9 frames
    pause_time = 50  # 3 frames
    text_width = WINWIDTH - 40
    text_height = 64
    name_tag = FancyDialogNametag()  # Shared with all dialogs
    cursor = FancyDialogCursor()

    def __init__(self, text, portrait=None, background=None,
                 speaker=None, style_nid=None, speed: float = 1.0,
                 font_color='black', font_type='convo'):
        self.plain_text = text
        self.portrait = portrait
        self.background = background
        self.speaker = speaker
        self.font_type = 'convo'
        self.font_color = 'black'

        # States: 
        # transition_in -- waiting for the dialog box to appear
        # process -- actually adding text to the screen, one character at a time
        # pause -- occasionally pauses for a period
        # pause_before_wait* -- will pause for some time between write and wait states (to account for player mashing A)
        # wait -- Done writing, now waiting for the player to press A
        # done -- No more dialog to show, waiting for the event to clean me up
        # transition_out* -- waiting for the dialog box to disappear
        # * unique to fancy dialog
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
        self.state = 'process'
        if self.portrait:
            self.portrait.talk()
        self.text_lines.append("")

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

    def pause_before_wait(self):
        if self.portrait:
            self.portrait.stop_talking()
        self.cursor.wait()
        self.state = 'pause_before_wait'
        self.last_update = engine.get_time()

    def hurry_up(self):
        if self.state == 'process':
            while self.state == 'process':
                self._next_char(sound=False)
                # Skip regular pauses because we want maximum velocity of speech
                if self.state == 'pause':
                    self.state = 'process'
        elif self.state == 'wait':
            if self.text_index >= len(self.text_commands):
                self.state = 'done'
            else:
                self._next_block()
                self.state = 'process'
                if self.portrait:
                    self.portrait.talk()
            self.cursor.flip()

    def end(self):
        self.state = 'transition_out'

    def update(self):
        current_time = engine.get_time()

        if self.state == 'transition_in':
            if self.background.ready():
                self._next_line()
                self.state = 'process'
        elif self.state == 'transition_out':
            self.background.update()
        elif self.state == 'process':
            if cf.SETTINGS['text_speed'] > 0:
                num_updates = engine.get_delta() / (float(cf.SETTINGS['text_speed']) * self.speed)
                self.total_num_updates += num_updates
                while self.total_num_updates >= 1 and self.state == 'process':
                    self.total_num_updates -= 1
                    self._next_char(sound=self.total_num_updates < 2)
                    if self.state != 'process':
                        self.total_num_updates = 0
            else:
                while self.state == 'process':
                    self._next_char(sound=False)
                    # Skip regular pauses because we want MAXIMUM VELOCITY of characters
                    if self.state == 'pause':
                        self.state = 'process'
                self.play_talk_boop()
        elif self.state == 'pause_before_wait':
            if current_time - self.last_update > self.pause_before_wait_time:
                if self.no_wait:
                    self.state = 'done'
                else:
                    self.state = 'wait'
        elif self.state == 'pause':  # Regular pause for periods
            if current_time - self.last_update > self.pause_time:
                self.state = 'process'

        return True

    def draw_text(self, surf):
        text_surf = engine.create_surface((self.text_width, self.text_height), transparent=True)

        processed_text_lines = fix_tags(self.text_lines)
        for idx, line in enumerate(processed_text_lines):
            x_pos = 0
            y_pos = 16 * idx + (8 * (4 - self.num_lines))

            width = text_width(self.font_type, line)
            render_text(text_surf, [self.font_type], [line], [self.font_color], (x_pos, y_pos))
            x_pos += width

        surf.blit(text_surf, (20, WINHEIGHT - 64 - 12))

    def draw(self, surf: engine.Surface) -> engine.Surface:
        if self.state not in ('transition_in', 'transition_out'):
            # Draw nametag
            if self.portrait and self.speaker:
                self.name_tag.update(self.portrait)
                self.name_tag.draw(surf, self.portrait, self.speaker)
            # Draw text
            self.draw_text(surf)

            if self.draw_cursor_flag:
                self.cursor.draw(surf)

        return surf
