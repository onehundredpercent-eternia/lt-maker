from app.data.components import Type
from app.utilities import str_utils
from app.resources.resources import Resources
from app.data.weapons import WexpGain
from dataclasses import dataclass
import logging
from app.data.database import Database
from app.utilities.typing import NID
import re
from typing import Callable, Dict, List, Set

@dataclass
class ValidationError():
    category: str
    owner: str
    where: str
    what: str

    def __str__(self) -> str:
        return "Error in %s:%s:%s - %s" % self.category, self.owner, self.where, self.what

    @classmethod
    def does_not_exist(self, nid):
        return "%s does not exist" % nid

class DatabaseValidatorEngine():
    def __init__(self, db: Database, resources: Resources):
        self.db = db
        self.resources = resources

    def validate_unit(self, unit_nid):
        return unit_nid in self.db.units.keys()

    def validate_wtype(self, wtype_nid):
        return wtype_nid in self.db.weapons.keys()

    def validate_wrank(self, wrank_nid):
        return wrank_nid in self.db.weapons.keys()

    def validate_class(self, klass_nid):
        return klass_nid in self.db.classes.keys()

    def validate_tag(self, tag_nid):
        return tag_nid in self.db.tags.keys()

    def validate_item(self, item_nid):
        return item_nid in self.db.items.keys()

    def validate_skill(self, skill_nid):
        return skill_nid in self.db.skills.keys()

    def validate_stat(self, stat_nid):
        return stat_nid in self.db.stats.keys()

    def validate_map_anim(self, anim_nid):
        return anim_nid in self.resources.animations.keys()

    def validate_equation(self, eq_nid):
        return eq_nid in self.db.equations.keys()

    def validate_movement_type(self, mtype_nid):
        return mtype_nid in self.db.mcost.get_unit_types()

    def validate_sound(self, sound_nid):
        return sound_nid in self.resources.sfx.keys()

    def validate_ai(self, ai_nid):
        return ai_nid in self.db.ai.keys()

    def validate_music(self, music_nid):
        return music_nid in self.resources.music.keys()

    def validate_combat_anim(self, anim_nid):
        return anim_nid in self.resources.combat_anims.keys()

    def validate_effect_anim(self, effect_nid):
        return effect_nid in self.resources.combat_effects.keys()

    def validate_affinity(self, affinity):
        return affinity in self.db.affinities.keys()

    def validate_terrain_type(self, terrain_nid):
        return terrain_nid in self.db.mcost.get_terrain_types()

    def validate_event(self, event_nid):
        return len(self.db.events.get_by_nid_or_name(event_nid)) > 0



    def validate_units(self):
        errors: List[ValidationError] = []
        for unit in self.db.units:
            if not self.validate_class(unit.klass):
                errors.append(ValidationError("Units", unit.nid, "klass", ValidationError.does_not_exist(unit.klass)))
        return errors

    def validate(self):
        # @TODO(mag): WIP
        errors: List[ValidationError] = []
        errors += self.validate_units()
        for error in errors:
            logging.error("validation failed: %s", error)
        return errors

    def fill_and_trim(self, data_dict: dict, expected_keys: set, real_keys: set, default_value_factory: Callable):
        missing_keys = expected_keys - real_keys
        extraneous_keys = real_keys - expected_keys
        for key in missing_keys:
            data_dict[key] = default_value_factory()
        for key in extraneous_keys:
            del data_dict[key]

    def repair_units(self):
        all_weapon_types = set(self.db.weapons.keys())
        all_stats = set(self.db.stats.keys())
        for unit in self.db.units:
            # make sure each unit has an entry for every weapon type, and no extraneous ones
            self.fill_and_trim(unit.wexp_gain, all_weapon_types, set(unit.wexp_gain.keys()), lambda: WexpGain(False, 0))
            # make sure each unit has an entry for every stat, and no extraneous ones
            self.fill_and_trim(unit.bases, all_stats, set(unit.bases.keys()), lambda: 0)
            self.fill_and_trim(unit.growths, all_stats, set(unit.growths.keys()), lambda: 0)

    def repair_klasses(self):
        all_weapon_types = set(self.db.weapons.keys())
        all_stats = set(self.db.stats.keys())
        for klass in self.db.classes:
            # make sure each klass has an entry for every weapon type, and no extraneous ones
            self.fill_and_trim(klass.wexp_gain, all_weapon_types, set(klass.wexp_gain.keys()), lambda: WexpGain(False, 0))
            # make sure each klass has an entry for every stat in all dicts
            self.fill_and_trim(klass.bases, all_stats, set(klass.bases.keys()), lambda: 0)
            self.fill_and_trim(klass.growths, all_stats, set(klass.growths.keys()), lambda: 0)
            self.fill_and_trim(klass.growth_bonus, all_stats, set(klass.growth_bonus.keys()), lambda: 0)
            self.fill_and_trim(klass.promotion, all_stats, set(klass.promotion.keys()), lambda: 0)
            self.fill_and_trim(klass.max_stats, all_stats, set(klass.max_stats.keys()), lambda: 0)

    def repair_levels(self):
        for level in self.db.levels:
            all_level_units = set(level.units.keys())
            travelers: Dict[NID, NID] = {}
            for unit in level.units:
                # fix phantom travelers
                unit_traveler = unit.starting_traveler
                if unit_traveler and unit_traveler == unit.nid:
                    logging.error("Unit %s is its own traveler", unit.nid)
                    unit.starting_traveler = None
                    continue
                if unit_traveler and unit_traveler in travelers:
                    logging.error("Found traveler %s originally on unit %s, found duplicate on unit %s in level %s",
                                  unit_traveler, travelers[unit_traveler], unit.nid, level.nid)
                    unit.starting_traveler = None
                    continue
                if unit_traveler and unit_traveler not in all_level_units:
                    logging.error("Found traveler %s on unit %s in level %s that does not exist",
                                  unit_traveler, unit.nid, level.nid)
                    unit.starting_traveler = None
                    continue
                if unit_traveler and level.units.get(unit_traveler) and level.units.get(unit_traveler).starting_position:
                    logging.error("Traveler %s on unit %s is already on map", unit_traveler, unit.nid)
                    unit.starting_traveler = None
                    continue
                travelers[unit_traveler] = unit.nid

    def validate_type(self, expose_type: Type, value: str):
        if expose_type == Type.Int:
            return str_utils.is_int(value)
        elif expose_type == Type.Float:
            return str_utils.is_float(value)
        elif expose_type == Type.String:
            return True
        elif expose_type == Type.WeaponType:
            return self.validate_wtype(value)
        elif expose_type == Type.WeaponRank:
            return self.validate_wrank(value)
        elif expose_type == Type.Unit:
            return self.validate_unit(value)
        elif expose_type == Type.Class:
            return self.validate_class(value)
        elif expose_type == Type.Tag:
            return self.validate_tag(value)
        elif expose_type == Type.Color3:
            return str_utils.is_color3(value)
        elif expose_type == Type.Color4:
            return str_utils.is_color4(value)
        elif expose_type == Type.Item:
            return self.validate_item(value)
        elif expose_type == Type.Skill:
            return self.validate_skill(value)
        elif expose_type == Type.Stat:
            return self.validate_stat(value)
        elif expose_type == Type.MapAnimation: #TODO
            return self.validate_map_anim(value)
        elif expose_type == Type.Equation:
            return self.validate_equation(value)
        elif expose_type == Type.MovementType:
            return self.validate_movement_type(value)
        elif expose_type == Type.TerrainType: #TODO
            return self.validate_terrain_type(value)
        else:
            return False

    def repair(self):
        """Only obvious repairs should be done here.
        """
        self.repair_units()
        self.repair_klasses()
        self.repair_levels()
