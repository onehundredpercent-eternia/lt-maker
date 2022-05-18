from __future__ import annotations
from dataclasses import dataclass

import os
from typing import Dict, List, Optional, Set, Tuple
from app.data.resources.combat_anims import EffectAnimation, Pose
from app.data.resources.combat_commands import get_command, CombatAnimationCommand
from app.utilities.str_utils import is_int
from pathlib import Path
import re
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import QSize


def handle_command(line, context: GbaSpellScriptContext) -> List[CombatAnimationCommand]:
    # spell command, in the format [C]XXYYID
    # where XX is the first arg, YY the second, and ID the actual command
    # OR in the format [C]ID, where XX and YY are implicitly 00.
    reg_search = re.search('(C[0-9]*)', line)
    if reg_search:
        command_text = reg_search.group(1)
    else:
        return []
    if len(command_text) == 3:  # shorthand command
        argx = '00'
        argy = '00'
        command_id = command_text[1:]
    else:  # full command
        argx = command_text[1:3]
        argy = command_text[3:5]
        command_id = command_text[5:]

    argx = int(argx, 16)
    argy = int(argy, 16)

    if command_id == '00':  # NOP
        # possible interrupt loops?
        # possibly consumes a frame?
        return []
    elif command_id == '14':  # screen shake
        pass
    elif command_id == '1A':  # "required before hit or 1f"
        # i'm not sure if we even need this
        pass
    elif command_id == '1F':  # register spell hit
        # should be straightforward
        pass
    elif command_id == '29':  # opacity/brightness change, uses XX
        context.bg_brightness = argx
        context.bg_opacity = argy
        opacity_command = get_command('opacity')
        opacity_command.value = (1.0 - (float(argy) / 32),)
        brightness_command = get_command('brightness')
        brightness_command.value = (0.5 + (float(argx) / 32),)
        return [opacity_command, brightness_command]
    elif command_id == '40':  # pan to defender
        pass
    elif command_id == '48':  # sound effect
        # we actually have no way of actually determining the sound since it's internal GBA mapped.
        # therefore, we'll just add a dummy sound command and let the user figure it out.
        pass
    elif command_id == '51':  # white flash
        pass
    elif command_id == '53':  # stretch screen based on YY
        context.vertical_stretch_mode = bool(argy)


class GbaSpellScriptContext():
    vertical_stretch_mode: bool = False
    missed: bool = False
    bg_brightness: int = 0xFF
    bg_opacity: int = 0xFF

    # state for frame commands
    o_frame_name: Optional[str] = None
    b_frame_name: Optional[str] = None


def crop_and_stretch_flattened_bg_frames(pixmap: QPixmap) -> QPixmap:
    cropped = pixmap.copy(0, 0, 240, 64)
    return cropped.scaled(240, 126)

# https://discord.com/channels/144670830150811649/206588291053649921/584940826115702806


def parse_gba_spell_script(current: EffectAnimation, fn: str):
    fname = Path(fn) / 'Spell.txt'

    # format: (fname, vertical_stretch_mode)
    required_frame_names: List[Tuple[str, bool]] = []
    context = GbaSpellScriptContext()
    attack_pose = Pose('Attack')
    miss_pose = Pose('Miss')
    with open(fname) as spell_file:
        spell_script = spell_file.readlines()
        spell_script = [line for line in spell_script if line]
        for idx, line in enumerate(spell_script):
            if line[0] == '#':  # comment
                continue
            elif line[0] == 'C':  # spell command
                cmds = handle_command(line, context)
                attack_pose.timeline += cmds
                if not context.missed:
                    miss_pose.timeline += cmds
                continue
            elif line[0] == 'O':  # possibly above/below frame
                # notes to self: bg frames have palettes in the top right, and are double stretched horizontally. not sure why, ask
                _, frame_png = line.strip().split(' ', 1)
                required_frame_names.append(
                    (frame_png, context.vertical_stretch_mode))
                frame_name = os.path.splitext(frame_png)[0]
                context.o_frame_name = frame_name
            elif line[0] == 'B':  # foreground frame - we'll be using this, mostly
                # notes to self: fg frames do not have palettes in the top right, and are possibly compressed vertically. but not always
                _, frame_png = line.strip().split(' ', 1)
                frame_name = os.path.splitext(frame_png)
                required_frame_names.append(
                    (frame_png, context.vertical_stretch_mode))
                frame_name = os.path.splitext(frame_png)[0]
                context.b_frame_name = frame_name
            # frames to hold the prior two frames for.
            elif is_int(line.strip()):
                if context.o_frame_name and context.b_frame_name:
                    frame_command = get_command('dual_frame')
                    frame_duration = int(line.strip())
                    frame_command.value = (
                        frame_duration, context.o_frame_name, context.b_frame_name)
                    attack_pose.timeline.append(frame_command)
                    if not context.missed:
                        miss_pose.timeline.append(frame_command)
                context.o_frame_name = None
                context.b_frame_name = None
            elif line[0] in ('~', '/'):  # "miss terminator" and "end of anim"
                # insert "abort for miss"
                # maybe NOP the end of anim?
                pass

    # dump frames
    from app.editor.utilities import get_bbox
    all_frames: Dict[str, QPixmap] = {}
    for frame_name, vertical_stretch in required_frame_names:
        ffname = Path(fn) / frame_name
        pixmap = QPixmap(str(ffname))
        if vertical_stretch:
            pixmap = crop_and_stretch_flattened_bg_frames(pixmap)
        x, y, width, height = get_bbox(pixmap.toImage())
        cropped_pixmap = pixmap.copy(x, y, width, height)
        all_frames[frame_name] = cropped_pixmap

    rects = [(name, p.width(), p.height()) for name, p in all_frames.items()]
    pack_result = rect_pack(rects)
    full_pixmap = QPixmap(QSize(*pack_result.size))
    painter = QPainter()
    painter.begin(full_pixmap)
    for name, pos in pack_result.top_lefts.items():
        x, y = pos
        pixmap = all_frames[name]
        painter.drawPixmap(x, y, pixmap)
    painter.end()
    return full_pixmap


@dataclass
class RectPackResult():
    size: Tuple[int, int]
    top_lefts: Dict[str, Tuple[int, int]]


def rect_pack(rects: List[Tuple[str, int, int]]) -> RectPackResult:
    # super naive solution
    MAX_WIDTH = 240 * 4
    top_lefts: Dict[str, Tuple[int, int]] = {}
    left = 0
    top = 0
    mheight = 0
    for rect_name, rwidth, rheight in rects:
        if left + rwidth > MAX_WIDTH:
            left = 0
            top += mheight
            mheight = 0
        top_lefts[rect_name] = (left, top)
        left += rwidth
        mheight = max(mheight, rheight)
    return RectPackResult((MAX_WIDTH, top + mheight), top_lefts)


# python -m app.editor.combat_animation_editor.spell_imports
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QWidget, QLabel
    app = QApplication(sys.argv)
    dname = 'app/editor/combat_animation_editor/testing_ground/[Dark] FE7if Ereshkigal {SHYUTERz}'
    c = EffectAnimation('thoron')
    animation = parse_gba_spell_script(c, dname)
    window = QWidget()
    l = QLabel(window)
    l.setPixmap(animation)
    animation.save("output.png", "PNG")
    # window.show()
    # app.exec_()
