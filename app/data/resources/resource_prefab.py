from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from typing_extensions import override

class WithResources(ABC):
    @abstractmethod
    def set_full_path(self, path: str) -> None:
        ...

    @abstractmethod
    def used_resources(self) -> List[Optional[Path]]:
        ...

class NoResources(WithResources):
    @override
    def set_full_path(self, path: str) -> None:
        pass

    @override
    def used_resources(self) -> List[Optional[Path]]:
        return []
