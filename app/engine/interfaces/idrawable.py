from abc import ABC, abstractmethod

from app.engine import engine


class IDrawable(ABC):
    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self, surf: engine.Surface) -> engine.Surface:
        pass
