from __future__ import annotations

from app.engine import action, background, menus
from app.engine.game_state import game
from app.engine.sound import get_sound_thread
from app.engine.state import MapState, State
from app.engine.selection_helper import SelectionHelper
from app.engine.fluid_scroll import FluidScroll
from app.engine.sprites import SPRITES
from app.data.resources.resources import RESOURCES


class CityMenuState(State):
    name = 'city_menu'
    in_level = False
    show_map = False

    def create_background(self):
        panorama = RESOURCES.panoramas.get('city_menu_background')
        if not panorama:
            panorama = RESOURCES.panoramas.get('default_background')
        if panorama:
            self.bg = background.PanoramaBackground(panorama)
        else:
            self.bg = None

    def start(self):
        self.city = game.memory.get('selected_city')
        self.menu = menus.CityMenu(self.city)
        self.fluid = FluidScroll()
        self.create_background()
        game.state.change('transition_in')
        return 'repeat'

    def begin(self):
        self.fluid.reset_on_change_state()

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            if self.menu.move_down(first_push):
                get_sound_thread().play_sfx('Select 6')
        elif 'UP' in directions:
            if self.menu.move_up(first_push):
                get_sound_thread().play_sfx('Select 6')
        elif 'RIGHT' in directions:
            self.menu.move_right(first_push)
            get_sound_thread().play_sfx('Select 6')
        elif 'LEFT' in directions:
            self.menu.move_left(first_push)
            get_sound_thread().play_sfx('Select 6')

        if event == 'BACK':
            get_sound_thread().play_sfx('Select 4')
            game.state.back()
        elif event == 'INFO':
            self.menu.toggle_info()
            get_sound_thread().play_sfx('Info In' if self.menu.info_flag else 'Info Out')
        elif event == 'SELECT':
            self._select()

    def _select(self):
        tab = self.menu.current_tab
        opt = self.menu.get_current()
        if opt is None:
            get_sound_thread().play_sfx('Error')
            return
        if tab == 'Work':
            self._toggle_work(opt)
        else:
            self._purchase(tab, opt)

    def _toggle_work(self, building):
        worked = self.city.worked_buildings.copy()
        if building.uid in worked:
            worked.remove(building.uid)
        elif len(worked) < self.city.worker_cap:
            worked.append(building.uid)
        else:
            get_sound_thread().play_sfx('Error')
            return
        action.do(action.SetWorkedBuildings(self.city, worked))
        get_sound_thread().play_sfx('Select 1')

    def _purchase(self, tab, opt):
        import app.engine.city_funcs as city_funcs
        team = game.teams.get(self.city.team)
        if tab == 'Draft':
            gold_cost, prod_cost = opt['gold_cost'], opt['production_cost']
            entry = city_funcs.make_unit_entry(opt['klass'], opt['level'], self.city.team, prod_cost, gold_cost)
        else:  # Build
            cost = opt.cost
            gold_cost = cost.gold_cost(self.city) if cost else 0
            prod_cost = cost.production_cost(self.city) if cost else 0
            entry = city_funcs.make_building_entry(opt.nid, prod_cost, gold_cost)

        if team and team.gold >= gold_cost:
            if gold_cost:
                action.do(action.ChangeTeamGold(team, -gold_cost))
            action.do(action.AddToProductionQueue(self.city, entry))
            get_sound_thread().play_sfx('Select 1')
            self.menu.build_options()
        else:
            get_sound_thread().play_sfx('Error')

    def update(self):
        self.menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        else:
            surf.blit(SPRITES.get('bg_black'), (0, 0))
        self.menu.draw(surf)
        return surf


class PlaceBuildingState(MapState):
    name = 'place_building'

    def start(self):
        self.pending = game.memory.get('pending_building_placements', [])
        self.city = None
        self.building = None
        self.selection = None
        self.valid = set()
        if not self._load_current():
            game.state.back()

    def _load_current(self) -> bool:
        """Advance to the next placeable pending building; returns False if none remain."""
        import app.engine.city_funcs as city_funcs
        while self.pending:
            self.city, self.building = self.pending[0]
            tiles = city_funcs.get_valid_placement_tiles(self.city, self.building)
            if tiles:
                self.valid = set(tiles)
                self.selection = SelectionHelper(self.valid)
                game.cursor.show()
                game.cursor.set_pos(self.selection.get_closest(self.city.position))
                return True
            # No valid tile anymore (a sibling placement filled the last one) - drop it
            self.pending.pop(0)
        return False

    def begin(self):
        self.fluid.reset_on_change_state()

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        if directions:
            new_pos = None
            if 'DOWN' in directions:
                new_pos = self.selection.get_down(game.cursor.position)
            elif 'UP' in directions:
                new_pos = self.selection.get_up(game.cursor.position)
            elif 'LEFT' in directions:
                new_pos = self.selection.get_left(game.cursor.position)
            elif 'RIGHT' in directions:
                new_pos = self.selection.get_right(game.cursor.position)
            if new_pos and new_pos != game.cursor.position:
                game.cursor.set_pos(new_pos)
                get_sound_thread().play_sfx('Select 6')

        if event == 'SELECT':
            pos = game.cursor.position
            if pos in self.valid:
                self.building.position = pos
                action.do(action.AddBuilding(self.city, self.building))
                get_sound_thread().play_sfx('Select 1')
                self.pending.pop(0)
                if not self._load_current():
                    game.state.back()
            else:
                get_sound_thread().play_sfx('Error')

        elif event == 'BACK':
            # Defer this building: re-queue it (already paid) so it prompts again next turn
            import app.engine.city_funcs as city_funcs
            entry = city_funcs.make_building_entry(self.building.nid, 0, 0)
            action.do(action.AddToProductionQueue(self.city, entry))
            get_sound_thread().play_sfx('Select 4')
            self.pending.pop(0)
            if not self._load_current():
                game.state.back()

    def draw(self, surf):
        surf = super().draw(surf)
        return surf
