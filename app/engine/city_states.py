from __future__ import annotations

from app.engine import action, background, city_funcs, menus
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
        opt = self.menu.get_current()
        if opt is None:
            get_sound_thread().play_sfx('Error')
            return
        if self.menu.current_tab == 'Draft':
            self._draft(opt)
        elif self.menu.current_tab == 'Build':
            self._build(opt)
        else:
            self._upgrade(opt)

    def _draft(self, spec):
        """Buy a unit outright: pay, then spawn it next to the city."""
        costs = city_funcs.get_unit_cost(spec)
        if not city_funcs.can_purchase(self.city) or not city_funcs.can_afford(self.city, *costs):
            get_sound_thread().play_sfx('Error')
            return
        city_funcs.pay_costs(self.city, *costs)
        city_funcs.mark_purchase(self.city)
        city_funcs.draft_unit(self.city, spec)
        get_sound_thread().play_sfx('Select 1')
        self.menu.build_options()

    def _build(self, building):
        """Buy a building outright: pay, then leave the menu to place it on the map."""
        costs = city_funcs.get_building_cost(building, self.city)
        if not city_funcs.can_purchase(self.city) or not city_funcs.can_afford(self.city, *costs):
            get_sound_thread().play_sfx('Error')
            return
        city_funcs.pay_costs(self.city, *costs)
        city_funcs.mark_purchase(self.city)
        get_sound_thread().play_sfx('Select 1')
        game.memory['pending_building'] = (self.city, building, costs)
        game.memory['next_state'] = 'place_building'
        game.state.change('transition_to_with_pop')

    def _upgrade(self, upgrade):
        """Buy an upgrade outright: pay, then swap the building where it stands."""
        costs = city_funcs.get_building_cost(upgrade.new, self.city)
        if not city_funcs.can_purchase(self.city) or not city_funcs.can_afford(self.city, *costs) \
                or not city_funcs.upgrade_fits(self.city, upgrade):
            get_sound_thread().play_sfx('Error')
            return
        city_funcs.pay_costs(self.city, *costs)
        city_funcs.mark_purchase(self.city)
        city_funcs.upgrade_building(self.city, upgrade)
        get_sound_thread().play_sfx('Select 1')
        self.menu.build_options()

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
    """Places the single building the player just bought in the city menu. Entered from
    (and returns to) the city menu, so the purchase reads as one uninterrupted action.
    Backing out refunds the building's full cost."""
    name = 'place_building'

    def start(self):
        self.city, self.building, self.costs = game.memory['pending_building']
        tiles = city_funcs.get_valid_placement_tiles(self.city, self.building)
        if not tiles:
            self._back(refund=True)
            return
        self.valid = set(tiles)
        self.selection = SelectionHelper(self.valid)
        game.cursor.show()
        game.cursor.set_pos(self.selection.get_closest(self.city.position))
        game.state.change('transition_in')
        return 'repeat'

    def begin(self):
        self.fluid.reset_on_change_state()

    def _back(self, refund: bool):
        """Return to the city menu, optionally handing the purchase price back."""
        if refund:
            gold_cost, food_cost, production_cost = self.costs
            city_funcs.pay_costs(self.city, -gold_cost, -food_cost, -production_cost)
            city_funcs.mark_purchase(self.city, False)
        game.memory['pending_building'] = None
        game.memory['next_state'] = 'city_menu'
        game.state.change('transition_to_with_pop')

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
                self._back(refund=False)
            else:
                get_sound_thread().play_sfx('Error')

        elif event == 'BACK':
            get_sound_thread().play_sfx('Select 4')
            self._back(refund=True)

    def draw(self, surf):
        surf = super().draw(surf)
        return surf
