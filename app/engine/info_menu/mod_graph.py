from __future__ import annotations

from typing import Callable, List, Tuple

from dataclasses import dataclass

from app.engine import help_menu, menus

@dataclass
class ModifiableSlot:
    aabb: Tuple[int, int, int, int] = None  # left, top, width, height
    menu: menus.ChoiceMenu = None
    on_select: Callable = None
    help_box: help_menu.HelpDialog = None
    first: bool = False

class ModGraph:
    def __init__(self):
        self.registry: List[ModifiableSlot] = []
        self.current_slot: ModifiableSlot = None
        self.cursor = menus.Cursor()
        self.has_focus = False

    def clear(self):
        self.registry.clear()
        self.current_slot = None

    def register(self, aabb: Tuple[int, int, int, int], menu: menus.ChoiceMenu, 
                 on_select: Callable, help_box: help_menu.HelpDialog | str, first: bool = False):
        if isinstance(help_box, str):
            help_box = help_menu.HelpDialog(help_box)

        self.registry.append(BoundingBox(aabb, menu, on_select, help_box, first))

    def _move(self, valid_slots: List[ModifiableSlot], horiz: bool = False) -> bool:
        """Move the current slot to the closest slot in the given direction

        Args:
            valid_slots (List[ModifiableSlot]): List of slots to compare against
            horiz (bool): Whether to move horizontally or vertically

        Returns:
            bool: Whether the current_slot was moved"""

        if not valid_slots:
            return False
        if not self.current_slot:
            return False
        closest_slot = info_graph.find_closest(self.current_slot, valid_slots, horiz)
        if closest_slot == self.current_slot:
            return False
        self.current_slot = closest_slot
        return True

    def move_left(self) -> bool:
        valid_slots = [slot for slot in self.registry if slot.aabb[0] < self.current_slot.aabb[0]]
        return self._move(valid_slots, horiz=True)

    def move_right(self) -> bool:
        valid_slots = [slot for slot in self.registry if slot.aabb[0] > self.current_slot.aabb[0]]
        return self._move(valid_slots, horiz=True)

    def move_up(self) -> bool:
        valid_slots = [slot for slot in self.registry if slot.aabb[1] < self.current_slot.aabb[1]]
        return self._move(valid_slots)

    def move_down(self) -> bool:
        valid_slots = [slot for slot in self.registry if slot.aabb[1] > self.current_slot.aabb[1]]
        return self._move(valid_slots)

    def handle_mouse(self, mouse_position: Tuple[int, int]):
        x, y = mouse_position
        for slot in self.registry:
            if slot.aabb[0] <= x < slot.aabb[0] + slot.aabb[2] \
                    and slot.aabb[1] <= y < slot.aabb[1] + slot.aabb[3]:
                self.current_slot = slot

    def draw(self, surf, with_info: bool = False):
        # Draw the slight translucent yellow effect over modifiable slots
        for slot in self.registry:
            s = engine.create_surface((slot.aabb[2], slot.aabb[3]), transparent=True)
            period = 1000  # ms
            max_opacity = 128  # 50%
            transparency = math.sin((engine.get_time() % period) / period * 2 * math.pi) * max_opacity
            color = (255, 255, 0)
            engine.fill(s, (*color, transparency))

        # Draw the current slot
        if self.current_slot:
            cursor_pos = (self.current_slot.aabb[0] - 4, self.current_slot.aabb[1])
            if self.has_focus:  # Only show as animating if the graph is the focus
                self.cursor.update()
            self.cursor.draw(surf, *cursor_pos)

            if with_info:
                help_box_pos = (self.current_slot.aabb[0] - 32, self.current_slot.aabb[1] + 13)
                self.current_slot.help_box.draw(surf, pos, False)
    