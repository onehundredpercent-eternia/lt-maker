from __future__ import annotations

from PyQt5.QtWidgets import QMessageBox

from app.editor.component_editor_properties import NewComponentProperties
from app.utilities.typing import NID
from app.editor.new_editor_tab import NewEditorTab

class ComponentObjectEditor(NewEditorTab):
    catalog_type = None
    properties_type: NewComponentProperties = None
    allow_import_from_xml = True
    allow_import_from_csv = True
    allow_copy_and_paste = True

    def attempt_change_nid(self, old_nid: NID, new_nid: NID) -> bool:
        if not new_nid:
            return False
        if old_nid == new_nid:
            return True
        if self.data.get(new_nid):
            QMessageBox.warning(self, 'Warning', 'ID %s already in use' % new_nid)
            return False
        self.data.change_key(old_nid, new_nid)
        self.tree_list.update_nid(old_nid, new_nid)
        self.tree_list.on_filter_changed(self.tree_list.search_box.text())
        return True

    def delete_from_db(self, nid):
        if len(self.data) == 1:
            return False
        self.data.remove_key(nid)
        return True
