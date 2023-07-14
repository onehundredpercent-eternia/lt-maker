import unittest
from typing import Any, Callable, List
from unittest.mock import MagicMock, patch

from app.data.database.item_components import ItemComponent
from app.data.database.skill_components import SkillComponent
from app.engine.component_system import source_generator
from app.engine.item_components.base_components import Spell, Weapon
from app.engine.skill_components.base_components import CanUseWeaponType, CannotUseWeaponType


class ItemSkillComponentTests(unittest.TestCase):
    def setUp(self):
        source_generator.generate_component_system_source()

    def tearDown(self):
        pass

    def test_item_components(self):
        # Test that all item components have
        # unique nids
        item_components = ItemComponent.__subclasses__()
        nids = {component.nid for component in item_components}
        for component in item_components:
            nid = component.nid
            self.assertIn(nid, nids)
            nids.remove(nid)

    def test_skill_components(self):
        # Test that all skill components have
        # unique nids
        skill_components = SkillComponent.__subclasses__()
        nids = {component.nid for component in skill_components}
        for component in skill_components:
            nid = component.nid
            self.assertIn(nid, nids)
            nids.remove(nid)

    def _test_skill_hook_with_components(self, components: List[SkillComponent], call_hook: Callable[[], Any], expected_result: Any):
        mock_skill = MagicMock()
        mock_skill.components = components
        mock_unit = MagicMock()
        mock_unit.skills = [mock_skill]
        self.assertEqual(expected_result, call_hook(mock_unit))

    def test_skill_hooks_have_correct_resolution_logic(self):
        from app.engine import skill_system
        self._test_skill_hook_with_components([CanUseWeaponType("Sword"), CanUseWeaponType("Lance")], lambda unit: skill_system.usable_wtypes(unit), set(["Sword", "Lance"]))

    def _test_item_hook_with_components(self, components: List[ItemComponent], call_hook: Callable[[], Any], expected_result: Any):
        with patch('app.engine.item_system.get_all_components', return_value = components):
            self.assertEqual(expected_result, call_hook())

    def test_item_hooks_have_correct_resolution_logic(self):
        from app.engine import item_system
        unit = MagicMock()
        item = MagicMock()
        # is_weapon
        self._test_item_hook_with_components([Weapon()], lambda: item_system.is_weapon(unit, item), True)
        self._test_item_hook_with_components([Spell()], lambda: item_system.is_weapon(unit, item), False)
        self._test_item_hook_with_components([Spell(), Weapon()], lambda: item_system.is_weapon(unit, item), False)
        self._test_item_hook_with_components([], lambda: item_system.is_weapon(unit, item), False)

if __name__ == '__main__':
    unittest.main()
