from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QTabWidget, QWidget

from app.data.database.database import Database
from app.data.database.items import ItemCatalog
from app.editor.editor_types import DatabaseEditor
from app.editor.item_editor.new_item_tab import NewItemDatabase
from app.editor.lib.state_editor.editor_state_manager import EditorStateManager
from app.editor.new_data_editor import DatabaseEditorDialog

if TYPE_CHECKING:
    from app.editor.main_editor import MainEditor


class EditorLauncher():
    def __init__(self, db: Database, parent=None) -> None:
        self._db = db
        self.parent: Optional[QWidget] = parent
        self.running_instances: Dict[Type, List[QDialog]] = {}
        self.initial_values: Dict[Type, Any] = {}

    def _launch(self, etype: str, editor, ):
        if not etype in Database.save_data_types:
            raise ValueError("%s not recognized as dbtype" % etype)
        def ok():
            pass
        def apply():
            self.initial_values[etype] = getattr(self._db, etype).copy()
        def cancel():
            running_instances = self.running_instances[etype]
            for instance in running_instances:
                instance.close()
            initial_values = self.initial_values[etype]
            setattr(self._db, etype, initial_values)
        window = DatabaseEditorDialog(self.parent, editor, ok, apply, cancel, '%s Editor' % etype.capitalize())
        if etype in self.running_instances:
            self.running_instances[etype].append(window)
        else:
            self.running_instances[etype] = [window]
            print(getattr(self._db, etype))
            self.initial_values[etype] = getattr(self._db, etype).copy()
        window.show()

    def item_editor(self, main_editor: Optional[MainEditor]=None, state_manager: Optional[EditorStateManager] = None):
        self._launch('items', NewItemDatabase(main_editor, self._db, state_manager))
