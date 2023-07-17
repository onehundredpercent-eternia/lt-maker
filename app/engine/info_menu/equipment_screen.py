

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from app.constants import WINHEIGHT, WINWIDTH
from app.data.database.database import DB
from app.engine import combat_calcs, engine, item_funcs, text_funcs
from app.engine.game_menus.icon_options import BasicItemOption, ItemOptionModes
from app.engine.game_menus.menu_components.generic_menu.cursor_hand import \
    CursorHand
from app.engine.graphics.text.text_renderer import render_text
from app.engine.gui import ScrollBar
from app.engine.info_menu.info_graph import InfoGraph
from app.engine.objects.item import ItemObject
from app.engine.objects.unit import UnitObject
from app.sprites import SPRITES
from app.utilities.enums import HAlignment

INVENTORY_TOP = 32
MAX_ITEMS_DISPLAYED = 5

EQUIPMENT_STATE = 'equipment'
EQUIPMENT_BB_ID = 'inventory'
def get_bb_id(idx: int):
    return EQUIPMENT_BB_ID + str(idx)


@dataclass
class MultiItemMenuInfo():
    start_idx: int
    size: int

class EquipmentScreen():
    def __init__(self, parent_info_graph: InfoGraph, left_top: Tuple[int, int]) -> None:
        self.info_graph = parent_info_graph
        self.left_top = left_top
        self.unit: Optional[UnitObject] = None
        self.displayed_items: List[ItemObject] = []
        self.displayed_accessories: List[ItemObject] = []

        self.scroll_bar = ScrollBar()
        self.cursor = CursorHand()

        # state
        self._control_enabled: bool = False
        self._inventory_scroll: int = 0
        self._cursor_pos: int = 0
        self._expanded_multiitems: Dict[int, MultiItemMenuInfo] = {}

        self._equipment_surf: Optional[engine.Surface] = None

    def enable_control(self):
        self._control_enabled = True

    def disable_control(self):
        self._control_enabled = False
        self.info_graph.select_box(EQUIPMENT_STATE, get_bb_id(self._cursor_pos - self._inventory_scroll))

    def reset(self):
        self._equipment_surf = None
        self.unit = None
        self._expanded_multiitems = {}
        self._cursor_pos = 0
        self._inventory_scroll = 0

    def initialized(self):
        if self.unit:
            return True
        return False

    @property
    def unit_items(self) -> List[Optional[ItemObject]]:
        items = self.displayed_items[:]
        if self.displayed_accessories:
            while len(items) + len(self.displayed_accessories) < MAX_ITEMS_DISPLAYED:
                items.append(None)
        items += self.displayed_accessories
        return items

    def expand_multi_item(self, index):
        item = self.unit_items[index]
        if not item:
            return
        index = -1
        which_list = None
        if item in self.displayed_items:
            index = self.displayed_items.index(item)
            which_list = self.displayed_items
        elif item in self.displayed_accessories:
            index = self.displayed_accessories.index(item)
            which_list = self.displayed_accessories
        if index == -1:
            return
        if item.multi_item:
            if item.uid in self._expanded_multiitems: # already expanded, do nothing
                return
            else:
                self._expanded_multiitems[item.uid] = MultiItemMenuInfo(index, len(item.subitems))
                for subitem in reversed(item.subitems):
                    idx = index + 1
                    which_list.insert(idx, subitem)
        self._inventory_scroll = min(self._inventory_scroll, len(self.unit_items) - MAX_ITEMS_DISPLAYED)
        self._equipment_surf = None

    def shrink_multi_item(self, index):
        item = self.unit_items[index]
        if not item:
            return
        index = -1
        which_list = None
        if item in self.displayed_items:
            index = self.displayed_items.index(item)
            which_list = self.displayed_items
        elif item in self.displayed_accessories:
            index = self.displayed_accessories.index(item)
            which_list = self.displayed_accessories
        if index == -1:
            return
        if item.multi_item:
            if item.uid in self._expanded_multiitems: # shrink
                multi_item_info = self._expanded_multiitems[item.uid]
                l_idx = multi_item_info.start_idx + 1
                r_idx = l_idx + multi_item_info.size
                while True: # recursively shrink any multi-item children that are expanded
                    expanded_children = False
                    for i in range(l_idx, r_idx):
                        if self.unit_items[i] and self.unit_items[i].uid in self._expanded_multiitems:
                            expanded_children = True
                            self.shrink_multi_item(i)
                    if not expanded_children:
                        break
                del which_list[l_idx:r_idx]
                del self._expanded_multiitems[item.uid]
            else: # not expanded, do nothing
                return
        self._inventory_scroll = min(self._inventory_scroll, len(self.unit_items) - MAX_ITEMS_DISPLAYED)
        self._equipment_surf = None

    def set_unit(self, unit: UnitObject):
        self.reset()
        self.unit = unit
        self.displayed_items = self.unit.nonaccessories
        self.displayed_accessories = self.unit.accessories
        # automatically expand multi items if they are equipped
        weapon = self.unit.get_weapon()
        idx_of_equipped_subweapon = -1
        for idx, item in enumerate(self.unit_items):
            if item.multi_item and any((subitem is weapon)for subitem in item.subitems):
                idx_of_equipped_subweapon = idx
                break
        if idx_of_equipped_subweapon != -1:
            self.expand_multi_item(idx_of_equipped_subweapon)
        # do the same for accessory
        accessory = self.unit.get_accessory()
        idx_of_equipped_subaccessory = -1
        for idx, item in enumerate(self.unit_items):
            if item.multi_item and any((subitem is accessory) for subitem in item.subitems):
                idx_of_equipped_subaccessory = idx
                break
        if idx_of_equipped_subaccessory != -1:
            self.expand_multi_item(idx_of_equipped_subaccessory)

    def select(self):
        item_at_cursor = self.unit_items[self._cursor_pos]
        if item_at_cursor.uid in self._expanded_multiitems: # expanded, shrink instead
            self.shrink_multi_item(self._cursor_pos)
        else: # try shrink
            self.expand_multi_item(self._cursor_pos)

    def handle_scroll(self):
        while self._cursor_pos - self._inventory_scroll >= MAX_ITEMS_DISPLAYED:
            self._inventory_scroll += 1
            self._equipment_surf = None
        while self._cursor_pos < self._inventory_scroll:
            self._inventory_scroll -= 1
            self._equipment_surf = None

    def move_up(self):
        self._cursor_pos = (self._cursor_pos - 1) % len(self.unit_items)
        self.handle_scroll()

    def move_down(self):
        self._cursor_pos = (self._cursor_pos + 1) % len(self.unit_items)
        self.handle_scroll()

    def move_left(self):
        item_at_pos = self.unit_items[self._cursor_pos]
        if item_at_pos.parent_item: # we are inside a multi-item - let's jump to parent
            index_of_parent = self.unit_items.index(item_at_pos.parent_item)
            self._cursor_pos = index_of_parent
            self.handle_scroll()
        else: # we are inside a normal item, just scroll up
            self.move_up()

    def move_right(self):
        item_at_pos = self.unit_items[self._cursor_pos]
        if item_at_pos.parent_item: # we are inside a multi-item - let's jump to next item that isn't this multi item
            parent_multi_item_info = self._expanded_multiitems[item_at_pos.parent_item.uid]
            next_idx = parent_multi_item_info.start_idx + 1 + parent_multi_item_info.size
            next_idx = min(next_idx, len(self.unit_items) - 1)
            self._cursor_pos = next_idx
            self.handle_scroll()
        else: # normal item; scroll down
            self.move_down

    def create_equipment_surf(self):
        def create_item_option(idx, item):
            return BasicItemOption.from_item(idx, item, width=120, mode=ItemOptionModes.FULL_USES)
        if not self.unit:
            return
        # unregister all existing boxes. if an inventory item was currently selected, remember its position
        for i in range(MAX_ITEMS_DISPLAYED):
            bbid = get_bb_id(i)
            self.info_graph.unregister(EQUIPMENT_STATE, bbid)

        surf = engine.create_surface((WINWIDTH - 96, WINHEIGHT), transparent=True)

        weapon = self.unit.get_weapon()
        accessory = self.unit.get_accessory()
        left, top = self.left_top

        # Blit items
        for idx, item in enumerate(self.unit_items[self._inventory_scroll:self._inventory_scroll + MAX_ITEMS_DISPLAYED]):
            if not item:
                continue
            if item.multi_item and any((subitem is weapon) or (subitem is accessory) for subitem in item.subitems):
                surf.blit(SPRITES.get('equipment_highlight'), (8, idx * 16 + INVENTORY_TOP))
                item_option = create_item_option(idx, item)
            else:
                if item is weapon or item is accessory:
                    surf.blit(SPRITES.get('equipment_highlight'), (8, idx * 16 + INVENTORY_TOP))
                item_option = create_item_option(idx, item)
            item_option.draw(surf, 8, idx * 16 + 24)
            self.info_graph.register((left + 8, top + idx * 16 + 24, 120, 16), item_option.get_help_box(), EQUIPMENT_STATE, first=(idx == 0), bb_id=get_bb_id(idx))

        # Battle stats
        battle_surf = SPRITES.get('battle_info')
        btop, bleft = 104, 12
        surf.blit(battle_surf, (bleft, btop))
        # Populate battle info
        surf.blit(SPRITES.get('equipment_logo'), (14, btop + 4))
        render_text(surf, ['text'], [text_funcs.translate('Rng')], ['yellow'], (78, btop))
        self.info_graph.register((left + 78, btop, 56, 16), 'Rng_desc', 'equipment')
        render_text(surf, ['text'], [text_funcs.translate('Atk')], ['yellow'], (22, btop + 16))
        self.info_graph.register((left + 14, btop + 16, 64, 16), 'Atk_desc', 'equipment')
        render_text(surf, ['text'], [text_funcs.translate('Hit')], ['yellow'], (22, btop + 32))
        self.info_graph.register((left + 14, btop + 32, 64, 16), 'Hit_desc', 'equipment')
        if DB.constants.value('crit'):
            render_text(surf, ['text'], [text_funcs.translate('Crit')], ['yellow'], (78, btop + 16))
            self.info_graph.register((left + 78, btop + 16, 56, 16), 'Crit_desc', 'equipment')
        else:
            render_text(surf, ['text'], [text_funcs.translate('AS')], ['yellow'], (78, btop + 16))
            self.info_graph.register((left + 78, btop + 16, 56, 16), 'AS_desc', 'equipment')
        render_text(surf, ['text'], [text_funcs.translate('Avoid')], ['yellow'], (78, btop + 32))
        self.info_graph.register((left + 78, btop + 32, 56, 16), 'Avoid_desc', 'equipment')

        if weapon:
            rng = item_funcs.get_range_string(self.unit, weapon)
            dam = str(combat_calcs.damage(self.unit, weapon))
            acc = str(combat_calcs.accuracy(self.unit, weapon))
            crt = combat_calcs.crit_accuracy(self.unit, weapon)
            if crt is None:
                crt = '--'
            else:
                crt = str(crt)
        else:
            rng, dam, acc, crt = '--', '--', '--', '--'

        avo = str(combat_calcs.avoid(self.unit, weapon))
        attack_speed = str(combat_calcs.attack_speed(self.unit, weapon))
        render_text(surf, ['text'], [rng], ['blue'], (127, btop), HAlignment.RIGHT)
        render_text(surf, ['text'], [dam], ['blue'], (71, btop + 16), HAlignment.RIGHT)
        render_text(surf, ['text'], [acc], ['blue'], (71, btop + 32), HAlignment.RIGHT)
        if DB.constants.value('crit'):
            render_text(surf, ['text'], [crt], ['blue'], (127, btop + 16), HAlignment.RIGHT)
        else:
            render_text(surf, ['text'], [attack_speed], ['blue'], (127, btop + 16), HAlignment.RIGHT)
        render_text(surf, ['text'], [avo], ['blue'], (127, btop + 32), HAlignment.RIGHT)

        return surf

    def update(self):
        self.cursor.update()

    def draw(self, surf):
        if not self._equipment_surf and self.unit:
            self._equipment_surf = self.create_equipment_surf()
        if self._equipment_surf:
            surf.blit(self._equipment_surf, self.left_top)

        if len(self.unit_items) > MAX_ITEMS_DISPLAYED:
            left, top = self.left_top
            left += 140
            top += 23
            self.scroll_bar.draw(surf, (left, top), self._inventory_scroll,
                                 MAX_ITEMS_DISPLAYED, len(self.unit_items))

        if self._control_enabled:
            left, top = self.left_top
            left -= 6
            top += (self._cursor_pos - self._inventory_scroll) * 16 + INVENTORY_TOP - 5
            # draw cursor and arrows
            self.cursor.draw(surf, (left, top))
