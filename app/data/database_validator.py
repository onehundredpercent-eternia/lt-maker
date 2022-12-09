from __future__ import annotations
from app.data.database.database_types import DatabaseType as DType
from app.data.database.weapons import WexpGain
from app.data.validation_errors import InvalidValueError, ValidationError
from app.utilities.data import Data
from app.utilities.typing import NID
from typing import Callable, Dict, List, Set, TYPE_CHECKING

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
        self._valid_entry_map: Dict[DType, Callable[[], List[str]]] = {}

    def validate(self, type: DType, nid: NID, level: NID='all') -> bool:
        return self._validate_db[type](nid, level)

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
        self.validators = DatabaseValidatorEngine(db, resources)

    def validate_db(self):
        pass

    def autorepair_db(self):
        """Repairs all erroneous entries in the database. Pointers to nonexistent skills, tilemaps, units, etc. are cleared"""
        # @TODO(mag): implement repairs for all data types
        self.repair_units()

    def repair_units(self):
        all_weapon_types = set(self.db.weapons.keys())
        all_stats = set(self.db.stats.keys())
        all_classes = set(self.db.classes.keys())
        _default_class = self.db.classes.keys()[0]
        all_tags = set(self.db.tags.keys())
        all_items = set(self.db.items.keys())
        all_skills = set(self.db.skills.keys())
        all_portraits = set(self.resources.portraits.keys())
        all_affinities = set(self.db.affinities.keys())
        for unit in self.db.units:
            if unit.klass not in all_classes:
                unit.klass = _default_class

            unit.tags = [tag for tag in unit.tags if tag in all_tags]

            # make sure each unit has an entry for every stat, and no extraneous ones
            sync_keys(unit.bases, all_stats, lambda: 0)
            sync_keys(unit.growths, all_stats, lambda: 0)

            unit.starting_items = [(item_nid, droppable) for item_nid, droppable in unit.starting_items if item_nid in all_items]

            unit.learned_skills = [(lvl, skill_nid) for lvl, skill_nid in unit.learned_skills if skill_nid in all_skills]

            # make sure each unit has an entry for every weapon type, and no extraneous ones
            sync_keys(unit.wexp_gain, all_weapon_types, lambda: WexpGain(False, 0))

            unit.alternate_classes = [class_nid for class_nid in unit.alternate_classes if class_nid in all_classes]

            if unit.portrait_nid:
                if not unit.portrait_nid in all_portraits:
                    unit.portrait_nid = None

            if unit.affinity:
                if not unit.affinity in all_affinities:
                    unit.affinity = None
