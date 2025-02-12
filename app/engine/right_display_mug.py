
from app.engine import engine
import pygame
import time
from typing import List, Tuple
from app.constants import TILEX, TILEY, WINHEIGHT, WINWIDTH
from app.engine.game_state import GameState
from app.engine.fonts import FONT
from app.engine.graphics.text.text_renderer import render_text, text_width
from app.engine.sprites import SPRITES
from app.constants import WINHEIGHT, WINWIDTH
from app.data.database.database import DB
from app.engine.graphics.ingame_ui.build_groove import build_groove
from app.data.resources.resources import RESOURCES
from app.engine.info_menu.info_graph import InfoGraph, info_states
from app.engine.info_menu.info_menu_portrait import InfoMenuPortrait
from app.engine.info_menu.info_menu_state import InfoMenuState
from app.engine import (background, combat_calcs, engine, equations, gui,
                        help_menu, icons, image_mods, item_funcs, item_system,
                        skill_system, text_funcs, unit_funcs)
from app.engine.text_evaluator import TextEvaluator
from app.utilities import utils
from app.utilities.enums import HAlignment

class RightDisplay():
    game: GameState
    mmb_states = ('free', 'prep_formation', 'prep_formation_select', 'info_menu', 'move')
    clock = pygame.time.Clock()
    def __init__(self, game: GameState):
        self.game = game
        self.unit_info_disp = None
        self.remove_unit_info = True
        self.prev_unit_info_top = False
        self.unit_info_offset = 0
        self.portrait_surf = None
        self.current_portrait = None
        self.bg = None
        
        self.info_graph = InfoGraph()
        self.info_flag = False
        
        self.sidebar_images = ['Ad1', 'Ad2', 'Ad3']
        self.current_image_index = 0
        self.last_switch_time = time.time()  # Track time of last switch
        self.switch_interval = 0.8  # Switch every 5 seconds
        
        
        # For transitions between states
        self.rescuer = None  # Keeps track of the rescuer if we are looking at the traveler
        self.next_unit = None
        self.next_state = None
        self.scroll_offset_x = 0
        self.scroll_offset_y = 0
        self.transition = None
        self.transition_counter = 0
        self.transparency = 0
        self.hover = None
        
        self.unit: self.unitObject = game.memory.get('current_unit')
        
    def remove_unit_display(self):
        self.remove_unit_info = True
        
    def reset_surfs(self, keep_last_info_graph_aabb=False):
        self.info_graph.clear(keep_last_aabb=keep_last_info_graph_aabb)
        self.portrait_surf = None
        self.current_portrait = None
        self.unit = None
        
    def update(self):
        self.current_tile_pos = self.game.cursor.position
        self.reset_surfs()
        
    def update_sidebar_image(self):
        """Update the current image if the interval has passed."""
        current_time = time.time()
        if current_time - self.last_switch_time >= self.switch_interval:
            # Switch to the next image
            self.current_image_index = (self.current_image_index + 1) % len(self.sidebar_images)
            self.last_switch_time = current_time
    
    def draw(self, surf: engine.Surface) -> engine.Surface:
        # if self.game.state.current() in self.mmb_states:
        #     surf.blit(SPRITES.get('Custom_Sidebar'), (0, 0))
        # else:
        #     # info menu shouldn't be transparent
        #     surf.blit(SPRITES.get('Empty_Sidebar'), (0, 0))
            
        self.update_sidebar_image()
        
        # Get the current image key
        current_image_key = self.sidebar_images[self.current_image_index]
        surf.blit(SPRITES.get(current_image_key), (0, 0))
        
        self.update()    
        
        # self.unit info handling
        if self.remove_unit_info:
            self.hover = self.game.cursor.get_hover()
            if self.game.state.current() in self.mmb_states:
                if self.hover and self.game.state.current() in ['free', 'prep_formation', 'prep_formation_select']:
                    if self.unit != self.hover:
                        self.reset_surfs()
                    self.unit = self.hover
                    self.draw_portrait(surf)
                elif self.game.state.current() in ['move'] and self.unit and self.game.memory.get('current_unit'):
                    self.unit = self.game.state.current_state().get_unit()
                    self.draw_portrait(surf)
                elif self.game.state.current() in ['info_menu']:
                    self.unit = self.game.state.current_state().get_unit()
                        
                    self.draw_portrait(surf)
                        
            else:
                self.reset_surfs()
        else:
            self.unit_info_offset -= 20
            self.unit_info_offset = max(0, self.unit_info_offset)
        
        return surf
    
    

    def draw_portrait(self, surf):
        # Only create if we don't have one in memory
        if not self.portrait_surf:
            self.portrait_surf = self.create_portrait_section()
        portrait_surf = self.portrait_surf.copy()

        surf.blit(portrait_surf, (0, self.scroll_offset_y))

    def create_portrait_section(self):
        font = FONT['info-white']
        nfont = FONT['number_small']
        dimensions = (80, 160)
        width, height = dimensions
        surf = engine.create_surface((80, WINHEIGHT), transparent=True)
        top, left = 4, 12
        
        if not self.unit.portrait_nid and self.unit.faction:
            icons.draw_faction(surf, DB.factions.get(self.unit.faction), (left + 11, top))
        elif self.unit.portrait_nid:
            portrait_nid = self.unit.portrait_nid
            icons.draw_chibi(surf, portrait_nid, (left + 11, top))

        if self.unit.generic:
            short_name = DB.classes.get(self.unit.klass).name
            name = short_name
        else:
            name = self.unit.name
        pos = (left + width//2 - font.width(name)//2 - 14, top + 34)
        FONT['text'].blit(name, surf, pos)
        
       # Weapon Icon

        itNum = 0
        for item in self.unit.items:
            icon = icons.get_icon(item) 
            if icon:
                if item is self.unit.get_weapon():
                    surf.blit(SPRITES.get('info_equipment_highlight'), (left + (itNum) * 16 - 11, top + 92))
                pos = (left + (itNum) * 16 - 11, top + 83)
                surf.blit(icon, pos)
                if item.droppable:
                    surf.blit(SPRITES.get('droppable'), (left + (itNum) * 16 - 11, top + 84))
                
                itNum += 1

        # Level text
        surf.blit(SPRITES.get('lv_sprite'), (left - 3, top + 52))
        surf.blit(SPRITES.get('exp_sprite'), (left + 33, top + 52))
        lvl = self.unit.level
        exper = self.unit.exp
        nfont.blit_right(str(lvl), surf, (left + 32, top + 48))
        nfont.blit_right(str(exper), surf, (left + 58, top + 48))

        # Health text
        surf.blit(SPRITES.get('unit_info_hp'), (left - 3, top + 61))
        surf.blit(SPRITES.get('unit_info_slash'), (left + 34, top + 62))
        current_hp = self.unit.get_hp()
        max_hp = equations.parser.hitpoints(self.unit)
        nfont.blit_right(str(current_hp), surf, (left + 32, top + 57))
        nfont.blit_right(str(max_hp), surf, (left + 58, top + 57))
        
        # Mana text
        surf.blit(SPRITES.get('unit_info_sp'), (left - 3, top + 70))
        surf.blit(SPRITES.get('unit_info_slash'), (left + 34, top + 71))
        current_mana = self.unit.get_mana()
        max_mana = equations.parser.mana(self.unit)
        nfont.blit_right(str(current_mana), surf, (left + 32, top + 66))
        nfont.blit_right(str(max_mana), surf, (left + 58, top + 66))

        # Combat stats
        STAT_FONT = FONT['small-white']
        
        if self.unit.get_weapon():
            dam = str(combat_calcs.damage(self.unit, self.unit.get_weapon()))
            acc = str(combat_calcs.accuracy(self.unit, self.unit.get_weapon()))
            crt = combat_calcs.crit_accuracy(self.unit, self.unit.get_weapon())
            if crt is None:
                crt = '--'
            else:
                crt = str(crt)
        else:
            dam, acc, crt = '--', '--', '--'
        
        STAT_FONT.blit(str("ATK"), surf, (left - 8, top + 96))
        nfont.blit_right(str(dam), surf, (left + 24, top + 99))
        STAT_FONT.blit(str("AS"), surf, (left - 8, top + 107))
        nfont.blit_right(str(combat_calcs.attack_speed(self.unit, self.unit.get_weapon())), surf, (left + 24, top + 110))
        STAT_FONT.blit(str("DEF"), surf, (left - 8, top + 119))
        nfont.blit_right(str(self.unit.get_stat('DEF')), surf, (left + 24, top + 122))
        STAT_FONT.blit(str("RES"), surf, (left - 8, top + 131))
        nfont.blit_right(str(self.unit.get_stat('RES')), surf, (left + 24, top + 134))
        
        # Combat stats right
        STAT_FONT.blit(str("HIT"), surf, (left + 30, top + 96))
        nfont.blit_right(str(acc), surf, (left + 64, top + 99))
        STAT_FONT.blit(str("AVO"), surf, (left + 30, top + 107))
        nfont.blit_right(str(combat_calcs.avoid(self.unit, self.unit.get_weapon())), surf, (left + 64, top + 110))
        STAT_FONT.blit(str("CRT"), surf, (left + 30, top + 119))
        nfont.blit_right(str(crt), surf, (left + 64, top + 122))
        STAT_FONT.blit(str("DDG"), surf, (left + 30, top + 131))
        nfont.blit_right(str(combat_calcs.crit_avoid(self.unit, self.unit.get_weapon())), surf, (left + 64, top + 134))

        
        
        # Weapon Types
        
        # wexp_to_draw: List[Tuple[str, int]] = []
        # for weapon, wexp in self.unit.wexp.items():
        #     if wexp > 0 and weapon in self.unit_funcs.usable_wtypes(self.unit):
        #         wexp_to_draw.append((weapon, wexp))
                
        # if not wexp_to_draw:
        #     return surf
        
        # counter = 0
        # for x in range(0, 4):
        #         weapon, value = wexp_to_draw[counter]
        #         weapon_rank = DB.weapon_ranks.get_rank_from_wexp(value)
        #         next_weapon_rank = DB.weapon_ranks.get_next_rank_from_wexp(value)
        #         if not weapon_rank:
        #             perc = 0
        #         elif not next_weapon_rank:
        #             perc = 1
        #         else:
        #             perc = (value - weapon_rank.requirement) / (next_weapon_rank.requirement - weapon_rank.requirement)
        #         offset = 3 + x * 24

        #         icons.draw_weapon(surf, weapon, (offset, 4 + 131))

        #         # Build groove
        #         build_groove(surf, (offset, 18 + 131), 16, perc)
        #         # Add text
        #         pos = (offset + 18, 4 + 131)
        #         render_text(surf, ['text'], [weapon_rank.nid], ['blue'], pos, HAlignment.CENTER)
        #         counter += 1
        #         if counter >= len(wexp_to_draw):
        #             break
        
        return surf