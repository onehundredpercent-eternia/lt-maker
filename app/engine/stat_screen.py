from app.constants import STATWIDTH, WINHEIGHT

from app.data.database import DB
from app.utilities import utils

from app.engine.fonts import FONT
from app.engine.sound import SOUNDTHREAD
from app.engine.sprites import SPRITES
from app.engine.input_manager import INPUT
from app.engine.state import MapState
from app.engine import engine, info_menu, \
    icons, image_mods, item_funcs, menu_options
from app.engine.game_state import game
from app.engine.fluid_scroll import FluidScroll

def handle_info():
    if game.cursor.get_hover():
        SOUNDTHREAD.play_sfx('Select 1')
        game.state.change('stat_screen')
    else:
        SOUNDTHREAD.play_sfx('Select 3')
        game.boundary.toggle_all_enemy_attacks()

def build_groove(surf, topleft, width, fill):
    bg = SPRITES.get('groove_back')
    start = engine.subsurface(bg, (0, 0, 2, 5))
    mid = engine.subsurface(bg, (2, 0, 1, 5))
    end = engine.subsurface(bg, (3, 0, 2, 5))
    fg = SPRITES.get('groove_fill')

    # Build back groove
    surf.blit(start, topleft)
    for idx in range(width - 2):
        mid_pos = (topleft[0] + 2 + idx, topleft[1])
        surf.blit(mid, mid_pos)
    surf.blit(end, (topleft[0] + width, topleft[1]))

    # Build fill groove
    number_needed = int(fill * (width - 1))  # Width of groove minus section for start and end
    for groove in range(number_needed):
        surf.blit(fg, (topleft[0] + 1 + groove, topleft[1] + 1))

class StatScreenState(MapState):
    name = 'stat_screen'

    def start(self):
        self.fluid = FluidScroll(200, 1)

        SOUNDTHREAD.play_sfx('Info In')
        game.stat_screen.toggle_info(True)
        game.stat_screen.info_graph.set_transition_in()

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.handle_mouse()
        if game.stat_screen.info_flag:
            if event == 'INFO' or event == 'BACK':
                SOUNDTHREAD.play_sfx('Info Out')
                game.stat_screen.info_graph.set_transition_out()
                game.state.back()

            if 'RIGHT' in directions:
                SOUNDTHREAD.play_sfx('Select 6')
                game.stat_screen.info_graph.move_right()
            elif 'LEFT' in directions:
                SOUNDTHREAD.play_sfx('Select 6')
                game.stat_screen.info_graph.move_left()
            elif 'UP' in directions:
                SOUNDTHREAD.play_sfx('Select 6')
                game.stat_screen.info_graph.move_up()
            elif 'DOWN' in directions:
                SOUNDTHREAD.play_sfx('Select 6')
                game.stat_screen.info_graph.move_down()

    def handle_mouse(self):
        mouse_position = INPUT.get_mouse_position()
        if not mouse_position:
            return
        if game.stat_screen.info_flag:
            game.stat_screen.info_graph.handle_mouse(mouse_position)

    def finish(self):
        game.stat_screen.toggle_info(False)

class StatScreen():
    def __init__(self):
        self.bg = SPRITES.get('stat_screen_background')
        self.unit = None
        self._next_unit = None

        self.info_graph = info_menu.InfoGraph()
        self.info_flag = False
        self.info_graph.set_current_state('personal_data')
        self.reset_surfs()

        self.transition = None
        self.transition_counter = 0

    def reset_surfs(self):
        self.info_graph.clear()
        self.portrait_surf = None
        self.personal_data_surf = None

    def toggle_info(self, val=False):
        self.info_flag = val

    def update(self):
        hover = game.cursor.get_hover()
        if hover:
            if hover != self.unit:
                self._next_unit = hover
                self.transition = 'out'

        if self.transition == 'out':
            self.transition_counter += 1
            self.transparency = self.transition_counter / 5
            if self.transparency >= 1:
                self.transition = 'in'
                self.transparency = 1
                self.unit = self._next_unit
                self._next_unit = None
                self.reset_surfs()

        elif self.transition == 'in':
            self.transition_counter -= 1
            self.transparency = self.transition_counter / 5
            if self.transparency <= 0:
                self.transition = None
                self.transparency = 0

    def draw(self, surf):
        self.update()
        if self.bg:
            surf.blit(self.bg, (0, 0))
        if self.unit:
            self.draw_portrait(surf)
            self.draw_slide(surf)
        if self.info_graph.current_bb:
            self.info_graph.draw(surf)
        return surf

    def draw_portrait(self, surf):
        if not self.portrait_surf:
            self.portrait_surf = self.create_portrait()

        # Stick it on the surface
        if self.transparency:
            im = image_mods.make_translucent(self.portrait_surf, self.transparency)
            surf.blit(im, (0, 0))
        else:
            surf.blit(self.portrait_surf, (0, 0))

    def create_portrait(self):
        surf = engine.create_surface((STATWIDTH, WINHEIGHT), transparent=True)
        surf.blit(SPRITES.get('info_unit'), (54, 82))

        im = icons.get_portrait(self.unit)
        if im:
            width = im.get_width()
            if width < 112:
                x_pos = (width - 80)//2
                portrait_surf = engine.subsurface(im, (x_pos, 0, 80, 72))
                portrait_surf = engine.flip_horiz(portrait_surf)
                surf.blit(portrait_surf, (16, 2))
            else:
                x_pos = (width - 112)//2
                portrait_surf = engine.subsurface(im, (x_pos, 0, 112, 72))
                portrait_surf = engine.flip_horiz(portrait_surf)
                surf.blit(portrait_surf, (0, 2))

        class_obj = DB.classes.get(self.unit.klass)
        if self.unit.generic:
            FONT['text-white'].blit(class_obj.name, surf, (8, 80))
            self.info_graph.register((8, 80, 72, 16), class_obj.desc, 'all', first=True)
        else:
            FONT['text-white'].blit(self.unit.name, surf, (8, 80))
            self.info_graph.register((8, 80, 72, 16), self.unit.desc, 'all', first=True)
        FONT['text-blue'].blit_right(str(self.unit.level), surf, (86, 80))
        self.info_graph.register((50, 80, 30, 16), 'Level_desc', 'all')
        FONT['text-blue'].blit_right(str(self.unit.exp), surf, (110, 80))
        self.info_graph.register((86, 80, 30, 16), 'Exp_desc', 'all')
        FONT['text-blue'].blit_right(str(self.unit.get_hp()), surf, (86, 96))
        self.info_graph.register((50, 96, 72, 16), 'HP_desc', 'all')
        max_hp = self.unit.get_max_hp()
        FONT['text-blue'].blit_right(str(max_hp), surf, (110, 96))
        affinity = DB.affinities.get(self.unit.affinity)
        if affinity:
            icons.draw_item(surf, affinity, (4, 16))
            self.info_graph.register((4, 24, 16, 16), affinity.desc, 'all')
        return surf

    def draw_slide(self, surf):
        if not self.personal_data_surf:
            self.personal_data_surf = self.create_slide()

        # Stick it on the surface
        if self.transparency:
            im = image_mods.make_translucent(self.personal_data_surf, self.transparency)
            surf.blit(im, (0, 0))
        else:
            surf.blit(self.personal_data_surf, (0, 0))

    def create_slide(self):
        menu_size = STATWIDTH, WINHEIGHT
        surf = engine.create_surface(menu_size, transparent=True)

        self.draw_stats(surf, 116)
        self.draw_equipment(surf, 152)

        return surf

    def draw_stats(self, surf, top):
        class_obj = DB.classes.get(self.unit.klass)
        max_stats = class_obj.max_stats

        stats = [stat.nid for stat in DB.stats if stat.position == 'left']
        # Make sure we only display up to 6 on each

        for idx, stat_nid in enumerate(stats):
            left = 37 * (idx // 2)
            y_pos = top + 16 * (idx % 2)
            # highest_stat = DB.stats.get(stat_nid).maximum
            # max_stat = max_stats.get(stat_nid, 30)
            # if max_stat > 0:
            #     total_length = int(max_stat / highest_stat * 24)
            #     frac = utils.clamp(self.unit.stats.get(stat_nid) / max_stat, 0, 1)
            #     build_groove(surf, (left + 19, y_pos + 8), total_length, frac)
            icons.draw_stat(surf, stat_nid, self.unit, (36 + left, y_pos), compact=True)
            # Name
            name = DB.stats.get(stat_nid).name
            FONT['text-yellow'].blit(name, surf, (1 + left, y_pos))
            self.info_graph.register((1 + left, y_pos, 40, 16), '%s_desc' % stat_nid, 'all')

        return surf

    def draw_equipment(self, surf, top):
        # Equipment
        weapon = self.unit.get_weapon()
        accessory = self.unit.get_accessory()

        # Blit items
        for idx, item in enumerate(self.unit.nonaccessories):
            y_pos = idx * 16 + top
            if item.multi_item and any(subitem is weapon for subitem in item.subitems):
                surf.blit(SPRITES.get('equipment_highlight'), (2, y_pos + 8))
                for subitem in item.subitems:
                    if subitem is weapon:
                        item_option = menu_options.ItemOption(idx, subitem)
                        break
                else:  # Shouldn't happen
                    item_option = menu_options.ItemOption(idx, item)
            else:
                if item is weapon:
                    surf.blit(SPRITES.get('equipment_highlight'), (2, y_pos + 8))
                item_option = menu_options.ItemOption(idx, item)
            item_option.draw(surf, 2, y_pos)
            self.info_graph.register((2, y_pos, 108, 16), item_option.get_help_box(), 'all')

        # Blit accessories
        for idx, item in enumerate(self.unit.accessories):
            aidx = item_funcs.get_num_items(self.unit) + idx
            y_pos = aidx * 16 + top
            if item.multi_item and any(subitem is accessory for subitem in item.subitems):
                surf.blit(SPRITES.get('equipment_highlight'), (2, y_pos + 8))
                for subitem in item.subitems:
                    if subitem is accessory:
                        item_option = menu_options.ItemOption(aidx, subitem)
                        break
                else:  # Shouldn't happen
                    item_option = menu_options.ItemOption(aidx, item)
            else:
                if item is accessory:
                    surf.blit(SPRITES.get('equipment_highlight'), (2, y_pos + 8))
                item_option = menu_options.ItemOption(aidx, item)
            item_option.draw(surf, 2, y_pos)
            first = (idx == 0 and not self.unit.nonaccessories)
            self.info_graph.register((2, y_pos, 108, 16), item_option.get_help_box(), 'all', first=first)

        return surf
