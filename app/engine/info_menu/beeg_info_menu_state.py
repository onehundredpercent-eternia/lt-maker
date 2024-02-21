from app.engine.graphics.text.text_renderer import render_text, text_width

from app.constants import WINWIDTH, WINHEIGHT
from app.utilities import utils

from app.data.database.database import DB
from app.data.resources.resources import RESOURCES

from app.engine.sprites import SPRITES
from app.engine.state import State
from app.engine import engine, help_menu, gui, \
    icons, image_mods, item_funcs, equations, \
    combat_calcs, skill_system
from app.engine.game_menus import menu_options
from app.engine.game_state import game
from app.engine.info_menu.info_menu_portrait import InfoMenuPortrait
from app.utilities.enums import Alignments

from app.engine.info_menu import info_graph, info_menu_state
from app.engine.graphics.ingame_ui.build_groove import build_groove

class BeegInfoMenuState(info_menu_state.InfoMenuState, State):
    name = 'beeg_info_menu'
    in_level = False
    show_map = False

    portrait_section_height = 80

    def build_arrows(self):
        self.left_arrow = gui.ScrollArrow('left', (3, self.portrait_section_height + 44))
        self.right_arrow = gui.ScrollArrow('right', (WINWIDTH - 8 - 3, self.portrait_section_height + 44), 0.5)

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        else:
            # info menu shouldn't be transparent
            surf.blit(SPRITES.get('bg_black'), (0, 0))

        self.draw_portrait(surf)
        self.draw_slide(surf)

        if self.info_graph.current_bb:
            self.info_graph.draw(surf)

        if not self.transition:
            self.mouse_indicator.draw(surf)

        return surf

    def draw_portrait(self, surf):
        # Only create if we don't have one in memory
        if not self.portrait_surf:
            self.portrait_surf = self.create_portrait_section()
        portrait_surf = self.portrait_surf.copy()

        # If no portrait for this unit, either create one or default to class card using icons.get_portrait
        if not self.current_portrait:
            portrait = RESOURCES.portraits.get(self.unit.portrait_nid)
            if portrait:
                self.current_portrait = InfoMenuPortrait(portrait, DB.constants.value('info_menu_blink'))
            else:
                im, offset = icons.get_portrait(self.unit)
        # We do have a portrait, so update...
        if self.current_portrait:
            self.current_portrait.update()
            im = self.current_portrait.create_image()
            offset = self.current_portrait.portrait.info_offset
        # Draw portrait onto the portrait surf
        if im:
            rect = (0, offset//2, im.get_width(), 76)
            portrait_surf = engine.subsurface(im, rect)
            surf.blit(portrait_surf, (100 + max((96 - im.get_width())//2, 0), 4))

        # Stick it on the surface
        if self.transparency:
            im = image_mods.make_translucent(portrait_surf, self.transparency)
            surf.blit(im, (0, self.scroll_offset_y))
        else:
            surf.blit(portrait_surf, (0, self.scroll_offset_y))

        # Blit the unit's active/focus map sprite
        if not self.transparency:
            active_sprite = self.unit.sprite.create_image('active')
            x_pos = 4 + 81 - active_sprite.get_width()//2
            y_pos = self.portrait_section_height - 61
            surf.blit(active_sprite, (x_pos, y_pos + self.scroll_offset_y))

    def create_portrait_section(self):
        surf = engine.create_surface((WINWIDTH, 80), transparent=True)
        surf.blit(SPRITES.get('info_unit'), (10, 44))

        x_offset = 4
        render_text(surf, ['text'], [self.unit.name], ['white'], (x_offset + 44, 0), Alignments.CENTER)
        self.info_graph.register((x_offset + 24, 0, 52, 24), self.unit.desc, 'all')
        class_obj = DB.classes.get(self.unit.klass)
        render_text(surf, ['text'], [class_obj.name], ['white'], (x_offset + 8, 24))
        self.info_graph.register((x_offset + 8, 24, 72, 16), class_obj.desc, 'all')
        render_text(surf, ['text'], [str(self.unit.level)], ['blue'], (x_offset + 38, 42), Alignments.RIGHT)
        self.info_graph.register((x_offset + 8, 42, 30, 16), 'Level_desc', 'all')
        render_text(surf, ['text'], [str(self.unit.exp)], ['blue'], (x_offset + 63, 42), Alignments.RIGHT)
        self.info_graph.register((x_offset + 38, 42, 30, 16), 'Exp_desc', 'all')
        render_text(surf, ['text'], [str(self.unit.get_hp())], ['blue'], (x_offset + 39, 58), Alignments.RIGHT)
        self.info_graph.register((x_offset + 8, 58, 72, 16), 'HP_desc', 'all')
        max_hp = equations.parser.hitpoints(self.unit)
        render_text(surf, ['text'], [str(max_hp)], ['blue'], (x_offset + 63, 58), Alignments.RIGHT)
        # Blit the white status platform
        surf.blit(SPRITES.get('status_platform'), (x_offset + 66, 53))
        # Blit affinity
        affinity = DB.affinities.get(self.unit.affinity)
        if affinity:
            icons.draw_item(surf, affinity, (x_offset + 78, 0))
            self.info_graph.register((x_offset + 76, 0, 16, 16), affinity.desc, 'all')

        # Battle stats
        battle_surf = SPRITES.get('battle_info')
        left, top = WINWIDTH - 122, 8
        surf.blit(battle_surf, (left, top))
        # Populate battle info
        surf.blit(SPRITES.get('equipment_logo'), (left + 2, top + 4))
        render_text(surf, ['text'], ['Rng'], ['yellow'], (left + 60, top + 1))
        self.info_graph.register((left + 60, top + 1, 64, 16), 'Rng_desc', 'all')
        render_text(surf, ['text'], ['Atk'], ['yellow'], (left + 4, top + 17))
        self.info_graph.register((left + 4, top + 17, 64, 16), 'Atk_desc', 'all')
        render_text(surf, ['text'], ['AS'], ['yellow'], (left + 60, top + 17))
        self.info_graph.register((left + 60, top + 17, 64, 16), 'AS_desc', 'all')
        render_text(surf, ['text'], ['Hit'], ['yellow'], (left + 4, top + 33))
        self.info_graph.register((left + 4, top + 33, 64, 16), 'Hit_desc', 'all')
        render_text(surf, ['text'], ['Avoid'], ['yellow'], (left + 60, top + 33))
        self.info_graph.register((left + 60, top + 33, 64, 16), 'Avoid_desc', 'all')
        if DB.constants.value('crit'):
            render_text(surf, ['text'], ['Crit'], ['yellow'], (left + 4, top + 49))
            self.info_graph.register((left + 4, top + 49, 64, 16), 'Crit_desc', 'all')
            render_text(surf, ['text'], ['Dodg'], ['yellow'], (left + 60, top + 49))
            self.info_graph.register((left + 60, top + 49, 64, 16), 'Dodg_desc', 'all')

        weapon = self.unit.get_weapon()
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
        ddg = str(combat_calcs.crit_avoid(self.unit, weapon))
        render_text(surf, ['text'], [rng], ['blue'], (left + 116, top + 1), Alignments.RIGHT)
        render_text(surf, ['text'], [dam], ['blue'], (left + 56, top + 17), Alignments.RIGHT)
        render_text(surf, ['text'], [attack_speed], ['blue'], (left + 116, top + 17), Alignments.RIGHT)
        render_text(surf, ['text'], [acc], ['blue'], (left + 56, top + 33), Alignments.RIGHT)
        render_text(surf, ['text'], [avo], ['blue'], (left + 116, top + 33), Alignments.RIGHT)
        if DB.constants.value('crit'):
            render_text(surf, ['text'], [crt], ['blue'], (left + 56, top + 49), Alignments.RIGHT)
            render_text(surf, ['text'], [ddg], ['blue'], (left + 116, top + 49), Alignments.RIGHT)

        return surf

    def draw_slide(self, surf):
        top_surf = engine.create_surface((WINWIDTH, WINHEIGHT), transparent=True)
        main_surf = engine.copy_surface(top_surf)

        if len(info_graph.info_states) > 1:
            self.draw_top_arrows(top_surf)

        if self.state == 'combat':
            if self.growth_flag:
                if not self.growths_surf:
                    self.growths_surf = self.create_personal_data_surf(growths=True)
                self.draw_growths_surf(main_surf)
            else:
                if not self.personal_data_surf:
                    self.personal_data_surf = self.create_personal_data_surf()
                self.draw_personal_data_surf(main_surf)
            if not self.class_skill_surf:
                self.class_skill_surf = self.create_class_skill_surf()
            self.draw_class_skill_surf(main_surf)
            if DB.constants.value('fatigue') and self.unit.team == 'player' and \
                    game.game_vars.get('_fatigue'):
                if not self.fatigue_surf:
                    self.fatigue_surf = self.create_fatigue_surf()
                self.draw_fatigue_surf(main_surf)
            if not self.equipment_surf:
                self.equipment_surf = self.create_equipment_surf()
            self.draw_equipment_surf(main_surf)
            if not self.skill_surf:
                self.skill_surf = self.create_skill_surf()
            self.draw_skill_surf(main_surf)

        elif self.state == 'extra':
            if not self.support_surf:
                self.support_surf = self.create_support_surf()
            self.draw_support_surf(main_surf)
            if not self.notes_surf:
                self.notes_surf = self.create_notes_surf()
            self.draw_notes_surf(main_surf)

        # Now put it in the right place
        offset_x = max(4, 4 - self.scroll_offset_x)
        main_surf = engine.subsurface(main_surf, (offset_x, 0, main_surf.get_width() - offset_x, WINHEIGHT))
        surf.blit(main_surf, (max(4, 4 + self.scroll_offset_x), self.scroll_offset_y))
        if self.transparency:
            top_surf = image_mods.make_translucent(top_surf, self.transparency)
        surf.blit(top_surf, (0, self.scroll_offset_y))

    def create_personal_data_surf(self, growths=False):
        if growths:
            state = 'growths'
        else:
            state = 'combat'

        menu_size = WINWIDTH//2 - 16, WINHEIGHT - self.portrait_section_height
        surf = engine.create_surface(menu_size, transparent=True)

        class_obj = DB.classes.get(self.unit.klass)
        max_stats = class_obj.max_stats

        left_stats = [stat.nid for stat in DB.stats if stat.position == 'left']
        right_stats = left_stats[10:]  # Only first ten get to be on the left
        right_stats += [stat.nid for stat in DB.stats if stat.position == 'right']
        # Make sure we only display up to 10 on each
        left_stats = left_stats[:10]

        stat_offset = 64
        for idx, stat_nid in enumerate(left_stats):
            curr_stat = DB.stats.get(stat_nid)
            # Value
            x_idx = idx // 3
            y_idx = idx % 3
            if growths:
                icons.draw_growth(surf, stat_nid, self.unit, (47 + stat_offset * x_idx, 16 * y_idx))
            else:
                highest_stat = curr_stat.maximum
                max_stat = max_stats.get(stat_nid, 30)
                if max_stat > 0:
                    total_length = int(max_stat / highest_stat * 42)
                    frac = utils.clamp(self.unit.stats.get(stat_nid) / max_stat, 0, 1)
                    build_groove(surf, (27 + stat_offset * x_idx, 16 * y_idx + 8), total_length, frac)
                icons.draw_stat(surf, stat_nid, self.unit, (47 + stat_offset * x_idx, 16 * y_idx))
            # Name
            name = DB.stats.get(stat_nid).name
            render_text(surf, ['text'], [name], ['yellow'], (8 + stat_offset * x_idx, 16 * y_idx))
            base_value = self.unit.stats.get(stat_nid, 0)
            subtle_stat_bonus = self.unit.subtle_stat_bonus(stat_nid)
            base_value += subtle_stat_bonus
            contribution = self.unit.stat_contribution(stat_nid)
            contribution['Base Value'] = base_value
            desc_text = curr_stat.desc
            help_box = help_menu.StatDialog(desc_text or ('%s_desc' % stat_nid), contribution)
            self.info_graph.register((WINWIDTH//2 + 4 + 8 + stat_offset * x_idx, self.portrait_section_height + 16 * y_idx, 64, 16), help_box, state, first=(idx == 0))

        return surf

    def draw_personal_data_surf(self, surf):
        surf.blit(self.personal_data_surf, (WINWIDTH//2 + 4, self.portrait_section_height))

    def draw_growths_surf(self, surf):
        surf.blit(self.growths_surf, (WINWIDTH//2 + 4, self.portrait_section_height))

    def create_equipment_surf(self):
        surf = engine.create_surface((WINWIDTH//2 - 16, WINHEIGHT - self.portrait_section_height), transparent=True)

        weapon = self.unit.get_weapon()
        accessory = self.unit.get_accessory()

        # Blit items
        for idx, item in enumerate(self.unit.nonaccessories):
            if item.multi_item and any(subitem is weapon for subitem in item.subitems):
                surf.blit(SPRITES.get('equipment_highlight'), (8, idx * 16 + 4))
                for subitem in item.subitems:
                    if subitem is weapon:
                        item_option = menu_options.FullItemOption(idx, subitem)
                        break
                else:  # Shouldn't happen
                    item_option = menu_options.FullItemOption(idx, item)
            else:
                if item is weapon:
                    surf.blit(SPRITES.get('equipment_highlight'), (8, idx * 16 + 4))
                item_option = menu_options.FullItemOption(idx, item)
            item_option.draw(surf, 8, idx * 16)
            self.info_graph.register((4 + 8, idx * 16 + self.portrait_section_height, 120, 16), item_option.get_help_box(), 'combat', first=(idx == 0))

        # Blit accessories
        for idx, item in enumerate(self.unit.accessories):
            aidx = item_funcs.get_num_items(self.unit) + idx
            y_pos = aidx * 16
            if item.multi_item and any(subitem is accessory for subitem in item.subitems):
                surf.blit(SPRITES.get('equipment_highlight'), (8, y_pos + 8))
                for subitem in item.subitems:
                    if subitem is accessory:
                        item_option = menu_options.FullItemOption(aidx, subitem)
                        break
                else:  # Shouldn't happen
                    item_option = menu_options.FullItemOption(aidx, item)
            else:
                if item is accessory:
                    surf.blit(SPRITES.get('equipment_highlight'), (8, y_pos + 8))
                item_option = menu_options.FullItemOption(aidx, item)
            item_option.draw(surf, 8, y_pos)
            first = (idx == 0 and not self.unit.nonaccessories)
            self.info_graph.register((4 + 8, y_pos + self.portrait_section_height, 120, 16), item_option.get_help_box(), 'combat', first=first)

        return surf

    def draw_equipment_surf(self, surf):
        surf.blit(self.equipment_surf, (4, self.portrait_section_height))

    def create_skill_surf(self):
        surf = engine.create_surface((WINWIDTH//2, 24), transparent=True)
        skills = [skill for skill in self.unit.skills if not (skill.class_skill or skill_system.hidden(skill, self.unit))]
        # stacked skills appear multiple times, but should be drawn only once
        skill_counter = {}
        unique_skills = []
        for skill in skills:
            if skill.nid not in skill_counter:
                skill_counter[skill.nid] = 1
                unique_skills.append(skill)
            else:
                skill_counter[skill.nid] += 1
        for idx, skill in enumerate(unique_skills[:6]):
            left_pos = idx * 24
            icons.draw_skill(surf, skill, (left_pos + 8, 4), compact=False, grey=skill_system.is_grey(skill, self.unit))
            if skill_counter[skill.nid] > 1:
                render_text(surf, ['small'], [str(skill_counter[skill.nid])], ['white'], (left_pos + 20 - 4 * len(str(skill_counter[skill.nid])), 6))
            if skill.data.get('total_charge'):
                charge = ' %d / %d' % (skill.data['charge'], skill.data['total_charge'])
            else:
                charge = ''
            self.info_graph.register((WINWIDTH//2 + 4 + left_pos + 8, WINHEIGHT - 24, 16, 16), help_menu.HelpDialog(skill.desc, name=skill.name + charge), 'combat')

        return surf

    def draw_skill_surf(self, surf):
        surf.blit(self.skill_surf, (WINWIDTH//2 + 4, WINHEIGHT - 32))

    def create_class_skill_surf(self):
        surf = engine.create_surface((WINWIDTH//2, 24), transparent=True)
        class_skills = [skill for skill in self.unit.skills if skill.class_skill and not skill_system.hidden(skill, self.unit)][:6]

        for idx, skill in enumerate(class_skills):
            left_pos = idx * 24
            icons.draw_skill(surf, skill, (left_pos + 8, 4), grey=skill_system.is_grey(skill, self.unit))
            if skill.data.get('total_charge'):
                charge = ' (%d/%d)' % (skill.data['charge'], skill.data['total_charge'])
            else:
                charge = ''
            self.info_graph.register((4 + WINWIDTH//2 + left_pos + 8, WINHEIGHT - 52, 16, 16), help_menu.HelpDialog(skill.desc, name=skill.name + charge), 'combat')

        return surf

    def draw_class_skill_surf(self, surf):
        surf.blit(self.class_skill_surf, (WINWIDTH//2 + 4, WINHEIGHT - 56))

    def create_support_surf(self):
        surf = engine.create_surface((WINWIDTH//2, WINHEIGHT - self.portrait_section_height), transparent=True)
        width = WINWIDTH // 4

        if game.game_vars.get('_supports'):
            pairs = game.supports.get_pairs(self.unit.nid)
            pairs = [pair for pair in pairs if pair.unlocked_ranks]
        else:
            pairs = []

        pairs = pairs[:6] # max six supports displayed

        top = 4
        for idx, pair in enumerate(pairs):
            x, y = (idx) % 2, idx // 2
            other_unit = None
            if pair.unit1 == self.unit.nid:
                other_unit = game.get_unit(pair.unit2)
            elif pair.unit2 == self.unit.nid:
                other_unit = game.get_unit(pair.unit1)
            if not other_unit:
                continue
            affinity = DB.affinities.get(other_unit.affinity)
            if affinity:
                icons.draw_item(surf, affinity, (x * width + 8, y * 16 + top))
                self.info_graph.register((0 + x * width + 8, self.portrait_section_height + y * 16 + top, WINWIDTH//2, 16), affinity.desc, 'extra')
            render_text(surf, ['narrow'], [other_unit.name], [], (x * width + 22, y * 16 + top))
            highest_rank = pair.unlocked_ranks[-1]
            render_text(surf, ['text'], [highest_rank], ['yellow'], (x * width + surf.get_width()/2 - 2, y * 16 + top), Alignments.RIGHT)
        return surf

    def draw_support_surf(self, surf):
        surf.blit(self.support_surf, (4, self.portrait_section_height))

    def create_notes_surf(self):
        # Menu background
        menu_surf = engine.create_surface((WINWIDTH//2, WINHEIGHT - self.portrait_section_height), transparent=True)

        my_notes = self.unit.notes

        if my_notes:
            total_height = 4
            help_offset = 0
            for idx, note in enumerate(my_notes):
                category = note[0]
                entries = note[1].split(',')
                render_text(menu_surf, ['text'], [category], ['blue'], (10, total_height))
                for entry in entries:
                    category_length = text_width('text', category)
                    left_pos = 64 if category_length <= 64 else (category_length + 8)
                    render_text(menu_surf, ['text'], [entry], [], (left_pos, total_height))
                    total_height += 16
                self.info_graph.register((WINWIDTH//2, 16 * help_offset + 4 + self.portrait_section_height, 64, 16), '%s_desc' % category, 'extra', first=(idx == 0))
                help_offset += len(entries)

        return menu_surf

    def draw_notes_surf(self, surf):
        surf.blit(self.notes_surf, (WINWIDTH//2 + 4, self.portrait_section_height))
