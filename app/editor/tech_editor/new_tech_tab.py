from __future__ import annotations

from typing import List, Optional, Set

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QLabel, QPushButton, QSpinBox

import app.engine.tech_component_access as TCA
from app.data.database.database import DB
from app.data.database.techs import TechCatalog, TechPrefab
from app.editor import timer
from app.editor.component_editor_delegates import EvalStringDelegate
from app.editor.component_editor_properties import NewComponentProperties
from app.editor.custom_widgets import TechBox
from app.editor.data_editor import SingleDatabaseEditor
from app.editor.new_editor_tab import NewEditorTab
from app.editor.tech_editor import tech_model
from app.extensions.custom_gui import DeletionDialog, DeletionTab, PropertyBox
from app.extensions.list_widgets import AppendSingleListWidget
from app.extensions.multi_select_combo_box import MultiSelectComboBox
from app.utilities.typing import NID


def find_prereq_cycle(techs, start_nid: NID) -> Optional[List[NID]]:
    """The `requires` chain reachable from `start_nid` that loops back on itself, or None.

    A cycle makes `can_unlock` permanently unsatisfiable -- every tech in the loop waits
    on another that is itself waiting -- so it is worth flagging while it is being typed,
    whether or not the techs are ever displayed as a tree.
    """
    path: List[NID] = []
    on_path: Set[NID] = set()

    def visit(nid: NID) -> Optional[List[NID]]:
        if nid in on_path:
            return path[path.index(nid):] + [nid]
        tech = techs.get(nid)
        if not tech:
            return None
        path.append(nid)
        on_path.add(nid)
        for req in tech.requires:
            found = visit(req)
            if found:
                return found
        path.pop()
        on_path.discard(nid)
        return None

    return visit(start_nid)


class NewTechProperties(NewComponentProperties[TechPrefab]):
    title = "Tech"
    get_components = staticmethod(TCA.get_tech_components)
    get_templates = staticmethod(TCA.get_templates)
    get_tags = staticmethod(TCA.get_tech_tags)

    def add_additional_widgets(self, main_section):
        self.renown_cost_box = PropertyBox(_("Renown Cost"), QSpinBox, self)
        self.renown_cost_box.edit.setRange(0, 999999)
        self.renown_cost_box.edit.valueChanged.connect(self.renown_cost_changed)
        main_section.addWidget(self.renown_cost_box, 1, 0)

        self.requires_box = PropertyBox(_("Requires"), MultiSelectComboBox, self)
        self.requires_box.edit.setPlaceholderText(_("No prerequisites..."))
        self.requires_box.edit.updated.connect(self.requires_changed)
        main_section.addWidget(self.requires_box, 1, 1, 1, 2)

        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: red")
        self.warning_label.hide()
        main_section.addWidget(self.warning_label, 2, 0, 1, 3)

        self.conditions_box = AppendSingleListWidget(
            [], _("Unlock Conditions"), EvalStringDelegate, self)
        self.conditions_box.model.default_value = 'True'
        self.conditions_box.view.setMaximumHeight(75)
        main_section.addWidget(self.conditions_box, 3, 0, 1, 3)

    def renown_cost_changed(self, val):
        self.current.renown_cost = val

    def requires_changed(self):
        self.current.requires = self.requires_box.edit.currentText()
        self.check_requires()

    def check_requires(self):
        """Warn about a prerequisite the tech can never satisfy: itself, or a loop."""
        if not self.current:
            return
        if self.current.nid in self.current.requires:
            self.show_warning(_("A tech cannot require itself."))
            return
        cycle = find_prereq_cycle(DB.techs, self.current.nid)
        if cycle:
            self.show_warning(_("Prerequisite loop: %s") % " -> ".join(cycle))
            return
        self.warning_label.hide()

    def show_warning(self, text: str):
        self.warning_label.setText(text)
        self.warning_label.show()

    def set_current(self, current):
        if not current:
            self.setEnabled(False)
            return
        self.setEnabled(True)
        self.current = current
        self.cached_nid = current.nid
        self.nid_box.edit.setText(current.nid)
        self.name_box.edit.setText(current.name)
        self.desc_box.edit.setText(current.desc)
        self.renown_cost_box.edit.setValue(current.renown_cost)

        # Copy first: clear()/addItems() fire `updated`, which would write the box's
        # (momentarily empty) selection straight back onto current.requires
        requires = current.requires[:]
        self.requires_box.edit.clear()
        self.requires_box.edit.addItems([nid for nid in DB.techs.keys() if nid != current.nid])
        self.requires_box.edit.setCurrentTexts(requires)
        self.current.requires = requires

        self.conditions_box.set_current(current.conditions)
        self.check_requires()

        self.icon_edit.change_icon(current.icon_nid, current.icon_index)
        self.component_list.clear()
        for component in current.components.values():
            self.add_component_widget(component)


class NewTechDatabase(NewEditorTab):
    catalog_type = TechCatalog
    properties_type = NewTechProperties
    allow_copy_and_paste = True

    @classmethod
    def edit(cls, parent=None):
        timer.get_timer().stop_for_editor()  # Don't need these while running game
        window = SingleDatabaseEditor(NewTechDatabase, parent)
        window.exec_()
        timer.get_timer().start_for_editor()

    @property
    def data(self):
        return self._db.techs

    def get_icon(self, tech_nid) -> Optional[QIcon]:
        pix = tech_model.get_pixmap(self.data.get(tech_nid))
        if pix:
            return QIcon(pix.scaled(32, 32))
        return None

    def _on_delete(self, nid: NID) -> bool:
        """Returns whether the user wants to proceed with deletion"""
        tech = self.data.get(nid)
        affected_techs = [t for t in self.data if nid in t.requires]

        if affected_techs:
            from app.editor.tech_editor.tech_model import TechModel
            msg = "Deleting Tech <b>%s</b> would affect these techs" % nid
            deletion_tab = DeletionTab(affected_techs, TechModel, msg, "Techs")
            swap, ok = DeletionDialog.get_swap([deletion_tab], TechBox(self, exclude=tech), self)
            if ok:
                self._on_nid_changed(nid, swap.nid)
            else:
                return False
        return True

    def _on_nid_changed(self, old_nid: NID, new_nid: NID) -> None:
        for tech in self.data:
            tech.requires = [new_nid if req == old_nid else req for req in tech.requires]


# Testing
# Run "python -m app.editor.tech_editor.new_tech_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.data.resources.resources import RESOURCES
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
    DB.load('default.ltproj', CURRENT_SERIALIZATION_VERSION)
    RESOURCES.load('default.ltproj', CURRENT_SERIALIZATION_VERSION)
    window = NewTechDatabase(None, DB)
    window.show()
    app.exec_()
