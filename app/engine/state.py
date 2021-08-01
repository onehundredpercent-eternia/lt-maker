from app.constants import TILEHEIGHT, TILEWIDTH, WINHEIGHT, WINWIDTH, MAPWIDTH, STATWIDTH
from app.engine.fluid_scroll import FluidScroll
from app.engine.game_state import game
from app.engine import engine

class State():
    name = None
    in_level = True
    show_map = True
    transparent = False

    started = False
    processed = False

    def __init__(self, name=None):
        self.name = name

    def start(self):
        """
        Called when state is first loaded
        """
        pass

    def begin(self):
        """
        Called whenever state begins being top of state stack
        """
        pass

    def take_input(self, event):
        pass

    def update(self):
        pass

    def draw(self, surf):
        return surf

    def end(self):
        pass

    def finish(self):
        pass

class MapState(State):
    def __init__(self, name=None):
        if name:
            self.name = name
        self.fluid = FluidScroll()

    def update(self):
        pass

    def draw(self, surf, culled_rect=None):
        game.camera.update()
        game.highlight.update()

        full_surf = engine.create_surface((WINWIDTH, WINHEIGHT))
        camera_cull = int(game.camera.get_x() * TILEWIDTH), int(game.camera.get_y() * TILEHEIGHT), MAPWIDTH, WINHEIGHT
        surf = game.map_view.draw(camera_cull, culled_rect)
        full_surf.blit(surf, (STATWIDTH, 0))
        return full_surf
