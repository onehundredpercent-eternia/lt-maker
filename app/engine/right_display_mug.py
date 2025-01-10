
from app.engine import engine
import pygame

from app.engine.game_state import GameState

class RightDisplay():
    game: GameState
    def __init__(self, game: GameState):
        self.game = game

    def draw(self, surf: engine.Surface) -> engine.Surface:
        # Draw a circle at position (100, 100) with radius 50 and color red (255, 0, 0)
        pygame.draw.circle(surf, (255, 0, 0), (100, 100), 50)
        return surf