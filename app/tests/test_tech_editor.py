import json
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import logging
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication, QWidget

import app.engine.tech_component_access as TCA
from app.data.database.database import DB, Database
from app.data.database.techs import TechPrefab
from app.data.resources.resources import RESOURCES
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
from app.utilities.data import Data

_app = None


def setUpModule():
    global _app
    from app.editor.editor_locale import init_locale
    init_locale()   # installs the global _() the editor widgets use
    _app = QApplication.instance() or QApplication(sys.argv)


class StubComponentParent(QWidget):
    """component_database row widgets reach back into their owning properties widget:
    the X button calls remove_component, and a resized options block asks the component
    list to re-lay out."""

    def __init__(self):
        super().__init__()
        self.component_list = QWidget()

    def remove_component(self, widget):
        pass


def make_tech(nid, requires=None, components=None):
    return TechPrefab(nid, nid, renown_cost=100, requires=requires,
                      components=Data(components or []))


class PrereqCycleTests(unittest.TestCase):
    """A prereq loop makes can_unlock permanently unsatisfiable, so the editor warns."""

    def cycle(self, edges, start):
        from app.editor.tech_editor.new_tech_tab import find_prereq_cycle
        techs = Data([make_tech(nid, requires=reqs) for nid, reqs in edges.items()])
        return find_prereq_cycle(techs, start)

    def test_two_cycle_is_found(self):
        self.assertEqual(['A', 'B', 'A'], self.cycle({'A': ['B'], 'B': ['A']}, 'A'))

    def test_self_reference_is_found(self):
        self.assertEqual(['A', 'A'], self.cycle({'A': ['A']}, 'A'))

    def test_longer_cycle_is_found(self):
        self.assertEqual(['A', 'B', 'C', 'A'],
                         self.cycle({'A': ['B'], 'B': ['C'], 'C': ['A']}, 'A'))

    def test_a_chain_is_not_a_cycle(self):
        self.assertIsNone(self.cycle({'A': ['B'], 'B': ['C'], 'C': []}, 'A'))

    def test_a_diamond_is_not_a_cycle(self):
        # A requires B and C; both require D. D is visited twice but never on one path.
        self.assertIsNone(
            self.cycle({'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': []}, 'A'))

    def test_a_missing_prerequisite_is_not_a_cycle(self):
        self.assertIsNone(self.cycle({'A': ['DoesNotExist']}, 'A'))


class TechComponentWidgetTests(unittest.TestCase):
    """Every tech component must render an editor row. A component whose expose type has
    no delegate/subcomponent editor registered silently falls back to a bare checkbox (or
    raises), so build one of each and check we got a real editor."""

    @classmethod
    def setUpClass(cls):
        DB.load('default.ltproj', CURRENT_SERIALIZATION_VERSION)
        RESOURCES.load('default.ltproj', CURRENT_SERIALIZATION_VERSION)
        from app.engine import sprites as engine_sprites
        engine_sprites.load_images()

    def setUp(self):
        self.parent = StubComponentParent()

    def test_every_component_builds_a_display_widget(self):
        from app.data.database.components import ComponentType
        from app.editor import component_database
        from app.editor.component_database import BoolItemComponent
        for component_class in TCA.get_tech_components():
            with self.subTest(component=component_class.nid):
                component = TCA.get_component(component_class.nid)
                widget = component_database.get_display_widget(component, self.parent)
                self.assertIsInstance(widget, BoolItemComponent)
                if component.expose == ComponentType.NewMultipleOptions:
                    # An options block builds one sub-editor per field; get_editor_widget
                    # raises for a field type with no registered editor, so reaching here
                    # with the right count proves every option is authorable
                    self.assertEqual(len(component.options),
                                     widget.editors_widget.layout().count())
                elif component.expose is not None:
                    self.assertTrue(hasattr(widget, 'editor'), component_class.nid)

    def test_list_of_buildings_gets_a_building_delegate(self):
        from app.editor import component_database
        from app.editor.component_editor_delegates import BuildingDelegate
        widget = component_database.get_display_widget(
            TCA.get_component('build_unlock'), self.parent)
        self.assertIsInstance(widget.editor.view.itemDelegate(), BuildingDelegate)


class NewTechDatabaseTests(unittest.TestCase):
    """The tab itself, against a scratch copy of a real project.

    Drives the global DB singleton rather than a private Database(): the properties
    widgets read the global DB directly (as every other *_properties widget does), so a
    private instance would leave the Requires dropdown reading a different catalog.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = os.path.join(tempfile.mkdtemp(prefix='lt_tech_editor_'), 'proj.ltproj')
        shutil.copytree('default.ltproj', cls.tmp)
        RESOURCES.load(cls.tmp, CURRENT_SERIALIZATION_VERSION)
        from app.engine import sprites as engine_sprites
        engine_sprites.load_images()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.dirname(cls.tmp), ignore_errors=True)

    def setUp(self):
        logging.disable(logging.CRITICAL)
        from app.editor.tech_editor.new_tech_tab import NewTechDatabase
        DB.load(self.tmp, CURRENT_SERIALIZATION_VERSION)
        self.db = DB
        self.db.techs.clear()
        for tech in (make_tech('Roots'),
                     make_tech('Branch', requires=['Roots'],
                               components=[TCA.restore_component(('city_pop_bonus', 5))]),
                     make_tech('Leaf', requires=['Branch'])):
            self.db.techs.append(tech)
        self.tab = NewTechDatabase(None, self.db)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_tab_lists_every_tech(self):
        self.assertEqual(['Roots', 'Branch', 'Leaf'], self.db.techs.keys())

    def test_selecting_a_tech_populates_the_form(self):
        self.tab.on_select('Branch')
        props = self.tab.right_frame
        self.assertEqual('Branch', props.nid_box.edit.text())
        self.assertEqual(100, props.renown_cost_box.edit.value())
        self.assertEqual(['Roots'], props.requires_box.edit.currentText())
        self.assertEqual(1, props.component_list.count())

    def test_requires_box_never_offers_the_tech_itself(self):
        self.tab.on_select('Branch')
        offered = [self.tab.right_frame.requires_box.edit.itemText(i)
                   for i in range(self.tab.right_frame.requires_box.edit.count())]
        self.assertNotIn('Branch', offered)

    def test_selecting_does_not_wipe_requires(self):
        # clear()/addItems() on the MultiSelectComboBox fires `updated`; if set_current
        # read the box back too early it would blank the tech's real prerequisites
        self.tab.on_select('Branch')
        self.assertEqual(['Roots'], self.db.techs.get('Branch').requires)

    def test_create_new_makes_an_empty_tech(self):
        self.assertTrue(self.tab.create_new('Sapling'))
        tech = self.db.techs.get('Sapling')
        self.assertEqual(0, len(tech.components))
        self.assertEqual([], tech.requires)

    def test_create_new_refuses_a_duplicate_nid(self):
        with patch('app.editor.new_editor_tab.QMessageBox.warning'):
            self.assertFalse(self.tab.create_new('Roots'))

    def test_duplicate_copies_components_without_aliasing(self):
        self.assertTrue(self.tab.duplicate('Branch', 'Branch2'))
        original = self.db.techs.get('Branch').components.get('city_pop_bonus')
        copy = self.db.techs.get('Branch2').components.get('city_pop_bonus')
        self.assertEqual(5, copy.value)
        copy.value = 99
        self.assertEqual(5, original.value)

    def test_rename_rewrites_other_techs_prerequisites(self):
        self.assertTrue(self.tab.rename('Roots', 'Taproot'))
        self.assertEqual(['Taproot'], self.db.techs.get('Branch').requires)
        self.assertEqual(['Branch'], self.db.techs.get('Leaf').requires)

    def test_renaming_a_class_rewrites_draft_unlock(self):
        from app.editor.class_editor import class_model
        tech = make_tech('Cavalry', components=[TCA.restore_component(('draft_unlock', ['Cavalier']))])
        self.db.techs.append(tech)
        class_model.on_nid_changed('Cavalier', 'Knight')
        self.assertEqual(['Knight'], tech.components.get('draft_unlock').value)

    def test_renaming_a_building_rewrites_build_unlock(self):
        import types

        from app.editor.building_editor.new_building_tab import NewBuildingDatabase
        tech = make_tech('Learning', components=[TCA.restore_component(('build_unlock', ['Library']))])
        self.db.techs.append(tech)
        NewBuildingDatabase._on_nid_changed(types.SimpleNamespace(_db=self.db), 'Library', 'Academy')
        self.assertEqual(['Academy'], tech.components.get('build_unlock').value)

    def test_renaming_a_skill_rewrites_grant_skill(self):
        import types

        from app.editor.skill_editor.new_skill_tab import NewSkillDatabase
        tech = make_tech('Toughness', components=[
            TCA.restore_component(('grant_skill', {'skills': ['Canto']}))])
        self.db.techs.append(tech)
        NewSkillDatabase._on_nid_changed(types.SimpleNamespace(_db=self.db), 'Canto', 'CantoPlus')
        self.assertEqual(['CantoPlus'], tech.components.get('grant_skill').skills)

    def test_a_tag_with_no_icon_file_labels_its_toolbutton(self):
        # QIcon built from a path is never null, even when the file is missing, so an
        # existence check that leans on QIcon.isNull leaves the button blank.
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QToolButton
        buttons = self.tab.right_frame.toolbar.findChildren(QToolButton)
        labelled = [b for b in buttons if b.toolButtonStyle() == Qt.ToolButtonTextOnly]
        # None of the Tech tags has a component_<tag>.png drawn for it yet
        self.assertTrue(labelled)
        for button in labelled:
            self.assertTrue(button.text())

    def test_delete_offers_a_swap_and_applies_it(self):
        with patch('app.editor.tech_editor.new_tech_tab.DeletionDialog.get_swap',
                   return_value=(self.db.techs.get('Leaf'), True)) as get_swap:
            self.assertTrue(self.tab.delete_from_db('Roots'))
        get_swap.assert_called_once()
        self.assertIsNone(self.db.techs.get('Roots'))
        self.assertEqual(['Leaf'], self.db.techs.get('Branch').requires)

    def test_delete_can_be_cancelled(self):
        with patch('app.editor.tech_editor.new_tech_tab.DeletionDialog.get_swap',
                   return_value=(None, False)):
            self.assertFalse(self.tab.delete_from_db('Roots'))
        self.assertIsNotNone(self.db.techs.get('Roots'))

    def test_delete_of_an_unreferenced_tech_asks_nothing(self):
        with patch('app.editor.tech_editor.new_tech_tab.DeletionDialog.get_swap') as get_swap:
            self.assertTrue(self.tab.delete_from_db('Leaf'))
        get_swap.assert_not_called()
        self.assertIsNone(self.db.techs.get('Leaf'))

    def test_cycle_warning_appears_and_clears(self):
        self.tab.on_select('Roots')
        props = self.tab.right_frame
        self.assertTrue(props.warning_label.isHidden())
        self.db.techs.get('Roots').requires = ['Leaf']   # Roots -> Leaf -> Branch -> Roots
        props.check_requires()
        self.assertFalse(props.warning_label.isHidden())
        self.db.techs.get('Roots').requires = []
        props.check_requires()
        self.assertTrue(props.warning_label.isHidden())

    def test_saving_writes_the_component_shape_and_reloads_identically(self):
        self.db.serialize(self.tmp)
        with open(os.path.join(self.tmp, 'game_data', 'techs.json')) as f:
            raw = json.load(f)
        self.assertEqual(['Roots', 'Branch', 'Leaf'], [d['nid'] for d in raw])
        self.assertNotIn('effects', raw[0])
        self.assertEqual([['city_pop_bonus', 5]], raw[1]['components'])

        reloaded = Database()
        reloaded.load(self.tmp, CURRENT_SERIALIZATION_VERSION)
        self.assertEqual(['Roots', 'Branch', 'Leaf'], reloaded.techs.keys())
        self.assertEqual(5, reloaded.techs.get('Branch').components.get('city_pop_bonus').value)
        self.assertEqual(['Roots'], reloaded.techs.get('Branch').requires)


if __name__ == '__main__':
    unittest.main()
