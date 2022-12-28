from abc import abstractmethod
from app.editor.data_editor import SingleDatabaseEditor
from app.utilities import Protocol

class DatabaseEditor(Protocol):
    @classmethod
    def edit(cls, *args, **kwargs) -> SingleDatabaseEditor: pass # type: ignore