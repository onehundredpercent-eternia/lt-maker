

from typing import Optional, Tuple

from app.constants import WINHEIGHT, WINWIDTH
from app.data.database.database import DB
from app.engine import combat_calcs, engine, item_funcs, text_funcs
from app.engine.game_menus.icon_options import BasicItemOption, ItemOptionModes
from app.engine.graphics.text.text_renderer import render_text
from app.engine.info_menu.info_graph import InfoGraph
from app.engine.objects.unit import UnitObject
from app.sprites import SPRITES
from app.utilities.enums import HAlignment


class EquipmentScreen():
    def __init__(self, parent_info_graph: InfoGraph, left_top: Tuple[int, int]) -> None:
        self.info_graph = parent_info_graph
        self.left_top = left_top

        self._equipment_surf: Optional[engine.Surface] = None
        self.unit: Optional[UnitObject] = None

    def reset(self):
        self._equipment_surf = None
        self._unit = None

    def initialized(self):
        if not self._equipment_surf and not self._unit:
            return False
        return True

    def set_unit(self, unit: UnitObject):
        self.reset()
        self.unit = unit

    def create_equipment_surf(self):
        EQUIPMENT_STATE = 'equipment'
        def create_item_option(idx, item):
            return BasicItemOption.from_item(idx, item, width=120, mode=ItemOptionModes.FULL_USES)

        if not self.unit:
            return

        surf = engine.create_surface((WINWIDTH - 96, WINHEIGHT), transparent=True)

        weapon = self.unit.get_weapon()
        accessory = self.unit.get_accessory()
        left, top = self.left_top

        # Blit items
        for idx, item in enumerate(self.unit.nonaccessories):
            if item.multi_item and any(subitem is weapon for subitem in item.subitems):
                surf.blit(SPRITES.get('equipment_highlight'), (8, idx * 16 + 24 + 8))
                for subitem in item.subitems:
                    if subitem is weapon:
                        item_option = create_item_option(idx, subitem)
                        break
                else:  # Shouldn't happen
                    item_option = create_item_option(idx, item)
            else:
                if item is weapon:
                    surf.blit(SPRITES.get('equipment_highlight'), (8, idx * 16 + 24 + 8))
                item_option = create_item_option(idx, item)
            item_option.draw(surf, 8, idx * 16 + 24)
            self.info_graph.register((left + 8, top + idx * 16 + 24, 120, 16), item_option.get_help_box(), EQUIPMENT_STATE, first=(idx == 0))

        # Blit accessories
        for idx, item in enumerate(self.unit.accessories):
            aidx = item_funcs.get_num_items(self.unit) + idx
            y_pos = aidx * 16 + 24
            if item.multi_item and any(subitem is accessory for subitem in item.subitems):
                surf.blit(SPRITES.get('equipment_highlight'), (8, y_pos + 8))
                for subitem in item.subitems:
                    if subitem is accessory:
                        item_option = create_item_option(aidx, subitem)
                        break
                else:  # Shouldn't happen
                    item_option = create_item_option(aidx, item)
            else:
                if item is accessory:
                    surf.blit(SPRITES.get('equipment_highlight'), (8, y_pos + 8))
                item_option = create_item_option(aidx, item)
            item_option.draw(surf, 8, y_pos)
            first = (idx == 0 and not self.unit.nonaccessories)
            self.info_graph.register((left + 8, top + y_pos, 120, 16), item_option.get_help_box(), EQUIPMENT_STATE, first=first)

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

    def draw(self, surf):
        if not self._equipment_surf and self.unit:
            self._equipment_surf = self.create_equipment_surf()
        if self._equipment_surf:
            surf.blit(self._equipment_surf, self.left_top)
