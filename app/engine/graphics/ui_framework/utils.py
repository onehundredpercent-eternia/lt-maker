from __future__ import annotations
from app.utilities.enums import Alignments, VAlignment, HAlignment

from typing import Tuple


def convert_align(align: Alignments) -> Tuple[HAlignment, VAlignment]:
    if align == Alignments.TOP_LEFT:
        return (HAlignment.LEFT, VAlignment.TOP)
    if align == Alignments.TOP:
        return (HAlignment.CENTER, VAlignment.TOP)
    if align == Alignments.TOP_RIGHT:
        return (HAlignment.RIGHT, VAlignment.TOP)
    if align == Alignments.LEFT:
        return (HAlignment.LEFT, VAlignment.CENTER)
    if align == Alignments.CENTER:
        return (HAlignment.CENTER, VAlignment.CENTER)
    if align == Alignments.RIGHT:
        return (HAlignment.RIGHT, VAlignment.CENTER)
    if align == Alignments.BOT_LEFT:
        return (HAlignment.LEFT, VAlignment.BOTTOM)
    if align == Alignments.BOT:
        return (HAlignment.CENTER, VAlignment.BOTTOM)
    if align == Alignments.BOT_RIGHT:
        return (HAlignment.RIGHT, VAlignment.BOTTOM)

def calc_align_position(align: Alignments, element_size: Tuple[int, int], frame_size: Tuple[int, int], padding: int = 10):
    halign, valign = convert_align(align)
    # handle horizontal and vertical alignments
    left, top = 0, 0
    width, height = frame_size
    cwidth, cheight = element_size
    if halign is HAlignment.LEFT:
        left = padding
    elif halign is HAlignment.CENTER:
        left = width / 2 - cwidth / 2
    elif halign is HAlignment.RIGHT:
        left = width - (cwidth + padding)
    if valign is VAlignment.TOP:
        top = padding
    elif valign is VAlignment.CENTER:
        top = height / 2 - cheight / 2
    elif valign is VAlignment.BOTTOM:
        top = height - (cheight + padding)
    return left, top