from __future__ import annotations
import logging
from app.data.database.overworld_node import OverworldNodeCatalog
from app.data.engine_types import map_component_type
from app.data.resources.map_icons import MapIconCatalog
from app.events.regions import Region
from app.data.database.level_units import GenericUnit, UniqueUnit, UnitGroup
from app.data.database.levels import OBJECTIVE_KEYS

from typing import Any, TYPE_CHECKING, Callable, Dict, List, Set, Tuple

from app.data.database.database_types import DatabaseType as DType
from app.data.resources.resource_types import ResourceType as RType
from app.data.database.components import Component, ComponentType as CType
from app.data.database.weapons import WexpGain
from app.data.validation_errors import InvalidValueError, ValidationError
from app.utilities.data import Data
from app.utilities.typing import NID

if TYPE_CHECKING:
    from app.data.database.database import Database
    from app.data.resources.resources import Resources


def is_nid_in_db_func(catalog: Data):
    def f(nid: NID, _):
        return nid in catalog.keys()
    return f

class DatabaseValidatorEngine():
    def __init__(self, db: Database, resources: Resources):
        self.db = db
        self.resources = resources

        # map of functions that take (nid, level_nid)
        self._validate_db: Dict[DType, Callable[[str, NID], bool]] = {
            DType.CONSTANTS: is_nid_in_db_func(self.db.constants),
            DType.TEAMS: lambda team, _: team in self.db.teams,
            DType.STATS: is_nid_in_db_func(self.db.stats),
            DType.EQUATIONS: is_nid_in_db_func(self.db.equations),
            DType.MCOST: lambda unit_type, _: unit_type in self.db.mcost.unit_types,
            DType.TERRAIN: is_nid_in_db_func(self.db.terrain),
            DType.MINIMAP: lambda terrain_type, _: terrain_type in self.db.minimap.get_minimap_types(),
            DType.WEAPON_RANKS: is_nid_in_db_func(self.db.weapon_ranks),
            DType.WEAPONS: is_nid_in_db_func(self.db.weapons),
            DType.FACTIONS: is_nid_in_db_func(self.db.factions),
            DType.ITEMS: is_nid_in_db_func(self.db.items),
            DType.SKILLS: is_nid_in_db_func(self.db.skills),
            DType.TAGS: is_nid_in_db_func(self.db.tags),
            DType.GAME_VAR_SLOTS: is_nid_in_db_func(self.db.game_var_slots),
            DType.CLASSES: is_nid_in_db_func(self.db.classes),
            DType.SUPPORT_CONSTANTS: is_nid_in_db_func(self.db.support_constants),
            DType.SUPPORT_RANKS: is_nid_in_db_func(self.db.support_ranks),
            DType.AFFINITIES: is_nid_in_db_func(self.db.affinities),
            DType.UNITS: is_nid_in_db_func(self.db.units),
            DType.SUPPORT_PAIRS: is_nid_in_db_func(self.db.support_pairs),
            DType.PARTIES: is_nid_in_db_func(self.db.parties),
            DType.AI: is_nid_in_db_func(self.db.ai),
            DType.DIFFICULTY_MODES: is_nid_in_db_func(self.db.difficulty_modes),
            DType.OVERWORLDS: is_nid_in_db_func(self.db.overworlds),
            DType.LEVELS: is_nid_in_db_func(self.db.levels),
            DType.EVENTS: is_nid_in_db_func(self.db.events),
            DType.TRANSLATIONS: is_nid_in_db_func(self.db.translations),
            DType.LORE: is_nid_in_db_func(self.db.lore),
            DType.RAW_DATA: is_nid_in_db_func(self.db.raw_data),
        }
        self._validate_resources: Dict[RType, Callable[[str, NID], bool]] = {
            RType.ICONS16: is_nid_in_db_func(self.resources.icons16),
            RType.ICONS32: is_nid_in_db_func(self.resources.icons32),
            RType.ICONS80: is_nid_in_db_func(self.resources.icons80),
            RType.PORTRAITS: is_nid_in_db_func(self.resources.portraits),
            RType.ANIMATIONS: is_nid_in_db_func(self.resources.animations),
            RType.PANORAMAS: is_nid_in_db_func(self.resources.panoramas),
            RType.MAP_ICONS: is_nid_in_db_func(self.resources.map_icons),
            RType.MAP_SPRITES: is_nid_in_db_func(self.resources.map_sprites),
            RType.COMBAT_PALETTES: is_nid_in_db_func(self.resources.combat_palettes),
            RType.COMBAT_ANIMS: is_nid_in_db_func(self.resources.combat_anims),
            RType.COMBAT_EFFECTS: is_nid_in_db_func(self.resources.combat_effects),
            RType.TILESETS: is_nid_in_db_func(self.resources.tilesets),
            RType.TILEMAPS: is_nid_in_db_func(self.resources.tilemaps),
            RType.MUSIC: is_nid_in_db_func(self.resources.music),
            RType.SFX: is_nid_in_db_func(self.resources.sfx),
        }
        self._valid_entry_map: Dict[DType, Callable[[], List[str]]] = {}

    def validate(self, xtype: DType | RType | CType, nid: NID, level: NID='all') -> bool:
        if isinstance(xtype, DType):
            return self._validate_db[xtype](nid, level)
        elif isinstance(xtype, RType):
            return self._validate_resources[xtype](nid, level)
        elif isinstance(xtype, CType):
            actual_type = map_component_type(xtype)
            if actual_type:
                return self.validate(actual_type, nid, level)
            return True
        else:
            raise ValueError("Validating Unknown Type %s" % str(xtype))

def sync_keys(data_dict: dict, expected_keys: set, default_value_factory: Callable):
    """Fills and trims a dict inplace.

    This removes all keys from the dict that are not in expected_keys, and
    adds all keys in expected_keys that are not in the dict, filling with the default value
    produced from default_value_factory

    Args:
        data_dict (dict): dictionary of values
        expected_keys (set): expected values in the dictionary
        default_value_factory (Callable): default factory for the default value of the dictionary
    """
    real_keys = set(data_dict.keys())
    missing_keys = expected_keys - real_keys
    extraneous_keys = real_keys - expected_keys
    for key in missing_keys:
        data_dict[key] = default_value_factory()
    for key in extraneous_keys:
        del data_dict[key]

class DatabaseRepair():
    def __init__(self, db: Database, resources: Resources):
        self.db = db
        self.resources = resources
        self.dbv = DatabaseValidatorEngine(db, resources)

    def _val(self, xtype: DType | RType | CType, nid: NID):
        return self.dbv.validate(xtype, nid)

    def validate_db(self):
        """Logs all erroneous entries in the database. References to nonexistent skills, tilemaps, units, etc."""
        # @TODO(mag): implement repairs for all data types
        self.repair_units()
        self.repair_levels()
        self.repair_overworlds()
        self.repair_items_and_skills()

    def autorepair_db(self):
        """Repairs all erroneous entries in the database. References to nonexistent skills, tilemaps, units, etc. are cleared"""
        # @TODO(mag): implement repairs for all data types
        self.repair_units(True)
        self.repair_levels(True)
        self.repair_overworlds(True)
        self.repair_items_and_skills(True)

    def repair_units(self, commit_changes: bool = False) -> List[ValidationError]:
        errors: List[ValidationError] = []

        all_weapon_types = set(self.db.weapons.keys())
        all_stats = set(self.db.stats.keys())
        _default_class = self.db.classes.keys()[0]

        for unit in self.db.units:
            def create_error(field_name, value):
                errors.append(InvalidValueError(DType.UNITS, unit.nid, field_name, value))

            if not self._val(DType.CLASSES, unit.klass):
                create_error("Klass", unit.klass)
                if commit_changes:
                    unit.klass = _default_class

            for tag in unit.tags:
                if not self._val(DType.TAGS, tag):
                    create_error("Tag", tag)
            if commit_changes:
                unit.tags = [tag for tag in unit.tags if self._val(DType.TAGS, tag)]

            if commit_changes:
                # make sure each unit has an entry for every stat, and no extraneous ones
                sync_keys(unit.bases, all_stats, lambda: 0)
                sync_keys(unit.growths, all_stats, lambda: 0)

            for item_nid, _ in unit.starting_items:
                if not self._val(DType.ITEMS, item_nid):
                    create_error("Item", item_nid)
            for _, skill_nid in unit.learned_skills:
                if not self._val(DType.SKILLS, skill_nid):
                    create_error("Skill", skill_nid)

            if commit_changes:
                unit.starting_items = [[item_nid, droppable] for item_nid, droppable in unit.starting_items if self._val(DType.ITEMS, item_nid)]
                unit.learned_skills = [[lvl, skill_nid] for lvl, skill_nid in unit.learned_skills if self._val(DType.SKILLS, skill_nid)]

            if commit_changes:
                # make sure each unit has an entry for every weapon type, and no extraneous ones
                sync_keys(unit.wexp_gain, all_weapon_types, lambda: WexpGain(False, 0))

            for class_nid in unit.alternate_classes:
                if not self._val(DType.CLASSES, class_nid):
                    create_error("Alternate Class", class_nid)

            if commit_changes:
                unit.alternate_classes = [class_nid for class_nid in unit.alternate_classes if self._val(DType.CLASSES, class_nid)]

            if unit.portrait_nid and not self._val(RType.PORTRAITS, unit.portrait_nid):
                create_error("Portrait", unit.portrait_nid)
                if commit_changes:
                    unit.portrait_nid = None

            if unit.affinity and not self._val(DType.AFFINITIES, unit.affinity):
                create_error("Affinity", unit.affinity)
                if commit_changes:
                    unit.affinity = None

        return errors

    def repair_levels(self, commit_changes: bool = False) -> List[ValidationError]:
        default_party = self.db.parties[0].nid
        default_unit = self.db.units[0].nid
        for level in self.db.levels:
            if level.tilemap and not self._val(RType.TILEMAPS, level.tilemap):
                level.tilemap = None

            if level.bg_tilemap and not self._val(RType.TILEMAPS, level.bg_tilemap):
                level.bg_tilemap = None

            if not level.party or not self._val(DType.PARTIES, level.party):
                level.party = default_party

            sync_keys(level.music, set(self.db.music_keys), lambda: None)
            for k, v in level.music.items():
                if not self._val(RType.MUSIC, v):
                    level.music[k] = None
            sync_keys(level.objective, set(OBJECTIVE_KEYS), lambda: '')

            if not level.roam_unit or not self._val(DType.UNITS, level.roam_unit):
                level.roam_unit = default_unit

            level.units = Data([unit for unit in level.units if
                                isinstance(unit, GenericUnit) or self._val(DType.UNITS, unit.nid)])

            level_travelers: Dict[NID, NID] = {}
            for level_unit in level.units:
                if level_unit.starting_traveler:
                    level_travelers[level_unit.nid] = level_unit.starting_traveler
            all_level_units: Set[NID] = set()
            for level_unit in level.units:
                all_level_units.add(level_unit.nid)
            context: Dict[str, Any] = {
                'level_units': all_level_units,
                'level_travelers': level_travelers
            }

            for level_unit in level.units:
                if isinstance(level_unit, GenericUnit):
                    self._repair_generic_unit(level_unit, context)
                else:
                    self._repair_unique_unit(level_unit, context)

            for group in level.unit_groups:
                self._repair_unit_group(group, context)

    # context contains tertiary information that may be necessary to validate
    def _repair_generic_unit(self, unit: GenericUnit, context: Dict[str, Any], commit_changes: bool = False) -> List[ValidationError]:
        _default_class = self.db.classes.keys()[0]
        _default_faction = self.db.factions.keys()[0]
        _default_team = self.db.teams[0]
        level_units: Set[NID] = context['level_units']
        if not self._val(DType.CLASSES, unit.klass):
            unit.klass = _default_class
        if not self._val(DType.FACTIONS, unit.faction):
            unit.faction = _default_faction
        unit.starting_items = [[item_nid, droppable] for item_nid, droppable in unit.starting_items if self._val(DType.ITEMS, item_nid)]
        unit.starting_skills = [skill_nid for skill_nid in unit.starting_skills if self._val(DType.SKILLS, skill_nid)]
        if not self._val(DType.TEAMS, unit.team):
            unit.team = _default_team
        if unit.ai and not self._val(DType.AI, unit.ai):
            unit.ai = None
        if unit.roam_ai and not self._val(DType.AI, unit.roam_ai):
            unit.roam_ai = None
        travelers: Dict[NID, NID] = context['level_travelers']
        for owner, traveler in travelers.items():
            if unit.starting_traveler == traveler and not unit.nid == owner:
                unit.starting_traveler = None
        if unit.starting_traveler not in level_units:
            unit.starting_traveler = None
        if unit.starting_traveler == unit.nid:
            unit.starting_traveler = None
        if not unit.starting_position:
            unit.starting_traveler = None

    # context contains tertiary information that may be necessary to validate
    def _repair_unique_unit(self, unit: UniqueUnit, context: Dict[str, Any], commit_changes: bool = False) -> List[ValidationError]:
        _default_faction = self.db.factions.keys()[0]
        _default_team = self.db.teams[0]
        level_units: Set[NID] = context['level_units']

        if not self._val(DType.TEAMS, unit.team):
            unit.team = _default_team
        if unit.ai and not self._val(DType.AI, unit.ai):
            unit.ai = None
        if unit.roam_ai and not self._val(DType.AI, unit.roam_ai):
            unit.roam_ai = None
        if not self._val(DType.FACTIONS, unit.faction):
            unit.faction = _default_faction
        travelers: Dict[NID, NID] = context['level_travelers']
        for owner, traveler in travelers.items():
            if unit.starting_traveler == traveler and not unit.nid == owner:
                unit.starting_traveler = None
        if unit.starting_traveler not in level_units:
            unit.starting_traveler = None
        if unit.starting_traveler == unit.nid:
            unit.starting_traveler = None
        if not unit.starting_position:
            unit.starting_traveler = None

    def _repair_unit_group(self, group: UnitGroup, context: Dict[str, Any], commit_changes: bool = False) -> List[ValidationError]:
        level_units: Set[NID] = context['level_units']
        group.units = [unit_nid for unit_nid in group.units if unit_nid in level_units]
        group.positions = {unit_nid: pos for unit_nid, pos in group.positions.items() if unit_nid in group.units}
        sync_keys(group.positions, set(group.units), lambda: None)

    def repair_items_and_skills(self, commit_changes: bool = False) -> List[ValidationError]:
        for item in self.db.items:
            if item.icon_nid and not self._val(RType.ICONS16, item.icon_nid):
                item.icon_nid = None
                item.icon_index = (0, 0)
            for component in item.components:
                self._repair_component(component)
        for skill in self.db.skills:
            if skill.icon_nid and not self._val(RType.ICONS16, skill.icon_nid):
                skill.icon_nid = None
                skill.icon_index = (0, 0)
            for component in skill.components:
                self._repair_component(component)

    def _repair_component(self, comp: Component, commit_changes: bool = False) -> List[ValidationError]:
        ctype = comp.expose
        base_component = comp.__class__()
        if ctype:
            if ctype == CType.NewMultipleOptions:
                for k in comp.options.keys():
                    nctype = comp.options[k]
                    value = comp.value[k]
                    base_value = base_component.value[k]
                    comp.value[k] = self._get_repaired_value(nctype, value, base_value)
            else:
                comp.value = self._get_repaired_value(ctype, comp.value, base_component.value)

    def _get_repaired_value(self, ctype: CType | Tuple[CType, CType | List], value: Any, base_value: Any) -> Any:
        if isinstance(ctype, tuple):
            ltype: CType = ctype[0]
            if ltype == CType.MultipleChoice:
                valid_values: List[str] = ctype[1]
                if value not in valid_values:
                    return base_value
            vtype: CType = ctype[1]
            if ltype == CType.List:
                return [v for v in value if self._val(vtype, v)]
            elif ltype == CType.Dict:
                return [[k, v] for k, v in value if self._val(vtype, k)]
        elif ctype == CType.NewMultipleOptions:
            raise ValueError("Shouldn't be calling this function on NewMultipleOptions")
        else:
            if value == None:
                return base_value
            else:
                if not self._val(ctype, value):
                    return base_value
        return value

    def repair_overworlds(self, commit_changes: bool = False) -> List[ValidationError]:
        for overworld in self.db.overworlds:
            if overworld.tilemap and not self._val(RType.TILEMAPS, overworld.tilemap):
                overworld.tilemap = None
            if overworld.music and not self._val(RType.MUSIC, overworld.music):
                overworld.music = None

            all_node_positions: Set[Tuple[int, int]] = set()
            overworld.overworld_nodes = OverworldNodeCatalog([node for node in overworld.overworld_nodes if node.pos])
            for node in overworld.overworld_nodes:
                if not self._val(RType.MAP_ICONS, node.icon):
                    node.icon = MapIconCatalog.DEFAULT()
                if node.level and not self._val(DType.LEVELS, node.level):
                    node.level = None
                all_node_positions.add(node.pos)

            to_delete: List[str] = []
            for pathkey, _ in overworld.map_paths.items():
                p1, p2 = overworld.string_to_tuples(pathkey)
                if p1 not in all_node_positions or p2 not in all_node_positions:
                    to_delete.append(pathkey)
            overworld.map_paths = {k: v for k, v in overworld.map_paths.items() if k not in to_delete}
            overworld.border_tile_width = max(overworld.border_tile_width, 0)