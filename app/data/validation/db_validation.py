from __future__ import annotations
from ast import Tuple
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from app.data.database.components import ComponentType
from app.data.database.database import Database
from app.data.database.database_types import DatabaseType
from app.data.database.database_validator import DatabaseValidatorEngine
from app.data.database.level_units import GenericUnit, UniqueUnit
from app.data.database.levels import OBJECTIVE_KEYS, LevelPrefab
from app.data.resources.resource_types import ResourceType
from app.data.resources.resources import Resources
from app.data.resources.tiles import TileMapPrefab
from app.data.validation.validation_errors import (
    ComponentValidationError, ItemComponentValidationError, LevelValidationError, SkillComponentValidationError, LevelUnitValidationError, UnitValidationError)
from app.events.event_prefab import EventVersion
from app.events import event_commands
from app.data.validation.validation_warnings import LevelNoneFieldWarning, RegionWarning
from app.events.python_eventing.preprocessor import Preprocessor
from app.events.regions import Region
from app.utilities.typing import NID

@dataclass
class ValidationResult():
    errors: List = field(default_factory=list)
    warnings: List = field(default_factory=list)

class DBChecker():
    def __init__(self, db: Database, resources: Resources) -> None:
        self.db = db
        self.resources = resources
        self.dve = DatabaseValidatorEngine(db, resources)

    def validate_generic_list(self, objs: List[NID], dtype: DatabaseType):
        return [nid for nid in objs if not self.dve.validate(dtype, nid)]

    def _validate_unique_unit(self, unique_unit: UniqueUnit, level: LevelPrefab, level_units: Set[NID], travelers: Dict[NID, NID]) -> ValidationResult:
        all_errors = []
        all_warnings = []

        if unique_unit.ai and not self.dve.validate(DatabaseType.AI, unique_unit.ai):
            all_errors.append(LevelUnitValidationError(level.nid, unique_unit.nid, "AI %s does not exist" % unique_unit.ai))

        if unique_unit.roam_ai and not self.dve.validate(DatabaseType.AI, unique_unit.roam_ai):
            all_errors.append(LevelUnitValidationError(level.nid, unique_unit.nid, "Roam AI %s does not exist" % unique_unit.roam_ai))

        if unique_unit.starting_position and not self.resources.tilemaps.get(level.tilemap).check_bounds(unique_unit.starting_position):
            all_errors.append(LevelUnitValidationError(level.nid, unique_unit.nid, "Starting Position %s is out of bounds" % unique_unit.starting_position))

        if travelers.get(unique_unit.nid):
            traveler = travelers.get(unique_unit.nid)
            if traveler not in level_units:
                all_errors.append(LevelUnitValidationError(level.nid, unique_unit.nid, "Traveler %s is not loaded into level" % traveler))
            elif traveler == unique_unit.nid:
                all_errors.append(LevelUnitValidationError(level.nid, unique_unit.nid, "Unit is its own traveler"))
            elif level.units.get(traveler).starting_position:
                all_errors.append(LevelUnitValidationError(level.nid, unique_unit.nid, "Traveler %s already has position on map" % traveler))
            elif traveler in [v for k, v in travelers.items() if k != unique_unit.nid]:
                all_errors.append(LevelUnitValidationError(level.nid, unique_unit.nid, "Multiple units have identical traveler %s" % traveler))

        return ValidationResult(all_errors, all_warnings)

    def _validate_generic_unit(self, generic_unit: GenericUnit, level: LevelPrefab, level_units: Set[NID], travelers: Dict[NID, NID]) -> ValidationResult:
        invalid_items = self.validate_generic_list([i[0] for i in generic_unit.starting_items], DatabaseType.ITEMS)
        invalid_skills = self.validate_generic_list(generic_unit.starting_skills, DatabaseType.SKILLS)
        item_errs = [LevelUnitValidationError(level.nid, generic_unit.nid, "Error in %s: No %s with name '%s'" % ('Items', DatabaseType.ITEMS.name, nid)) for nid in invalid_items]
        skill_errs = [LevelUnitValidationError(level.nid, generic_unit.nid, "Error in %s: No %s with name '%s'" % ('Skills', DatabaseType.SKILLS.name, nid)) for nid in invalid_skills]

        all_errors = item_errs + skill_errs
        all_warnings = []
        if generic_unit.ai and not self.dve.validate(DatabaseType.AI, generic_unit.ai):
            all_errors.append(LevelUnitValidationError(level.nid, generic_unit.nid, "AI %s does not exist" % generic_unit.ai))

        if generic_unit.roam_ai and not self.dve.validate(DatabaseType.AI, generic_unit.roam_ai):
            all_errors.append(LevelUnitValidationError(level.nid, generic_unit.nid, "Roam AI %s does not exist" % generic_unit.roam_ai))

        if generic_unit.starting_position and not self.resources.tilemaps.get(level.tilemap).check_bounds(generic_unit.starting_position):
            all_errors.append(LevelUnitValidationError(level.nid, generic_unit.nid, "Starting Position %s is out of bounds" % generic_unit.starting_position))

        if travelers.get(generic_unit.nid):
            traveler = travelers.get(generic_unit.nid)
            if traveler not in level_units:
                all_errors.append(LevelUnitValidationError(level.nid, generic_unit.nid, "Traveler %s is not loaded into level" % traveler))
            elif traveler == generic_unit.nid:
                all_errors.append(LevelUnitValidationError(level.nid, generic_unit.nid, "Unit is its own traveler"))
            elif level.units.get(traveler).starting_position:
                all_errors.append(LevelUnitValidationError(level.nid, generic_unit.nid, "Traveler %s already has position on map" % traveler))
            elif traveler in [v for k, v in travelers.items() if k != generic_unit.nid]:
                all_errors.append(LevelUnitValidationError(level.nid, generic_unit.nid, "Multiple units have identical traveler %s" % traveler))

        return ValidationResult(all_errors, all_warnings)

    def _validate_region(self, region: Region, level_tilemap: Optional[TileMapPrefab], level_nid: NID) -> ValidationResult:
        all_errors = []
        all_warnings = []
        if not level_tilemap:
            all_warnings.append(RegionWarning(level_nid, region.nid, 'Region exists but no tilemap exists in level.'))
        # @TODO(mag): determine if all regions should have positions/it's warning-worthy
        # if not region.position: append "Region has no position"
        if region.position:
            rx, ry = region.position
            rxb, ryb = rx + region.size[0], ry + region.size[1]
            if rx < 0 or ry < 0 or rxb > level_tilemap.width or ryb > level_tilemap.height:
                all_warnings.append(RegionWarning(level_nid, region.nid, 'Region bounds exceed tilemap size or region not in tilemap'))
        return ValidationResult(all_errors, all_warnings)

    def validate_levels(self) -> ValidationResult:
        all_errors = []
        all_warnings = []
        for level in self.db.levels:
            def _validate_attr(dtype, attr, optional=True):
                val = getattr(level, attr)
                if val is None and optional:
                    return
                if not self.dve.validate(dtype, val):
                    all_errors.append(LevelValidationError(level.nid, attr, val, dtype))

            _validate_attr(ResourceType.TILEMAPS, 'tilemap')
            _validate_attr(ResourceType.TILEMAPS, 'bg_tilemap')
            _validate_attr(DatabaseType.PARTIES, 'party')

            # music
            for music_key in self.db.music_keys:
                track = level.music.get(music_key)
                if track is None:
                    continue
                if not self.dve.validate(ResourceType.MUSIC, track):
                    all_errors.append(LevelValidationError(level.nid, 'music:%s' % music_key, track, ResourceType.MUSIC))

            # objective, warning only
            for objtv in OBJECTIVE_KEYS:
                if not level.objective.get(objtv):
                    all_warnings.append(LevelNoneFieldWarning(level.nid, 'objective:%s' % objtv))

            _validate_attr(DatabaseType.UNITS, 'roam_unit', not level.roam)

            all_level_units = set(level.units.keys())
            travelers: Dict[NID, NID] = {unit.nid: unit.starting_traveler for unit in level.units}
            for unit in level.units:
                if isinstance(unit, UniqueUnit):
                    vres = self._validate_unique_unit(unit, level, all_level_units, travelers)
                elif isinstance(unit, GenericUnit):
                    vres = self._validate_generic_unit(unit, level, all_level_units, travelers)
                all_errors += vres.errors
                all_warnings += vres.warnings

            for region in level.regions:
                vres = self._validate_region(region, self.resources.tilemaps.get(level.tilemap), level.nid)
                all_errors += vres.errors
                all_warnings += vres.warnings

            # level.groups: if any warnings or errors pop up, we can add them here; can't think of any right now
            # level.ai_groups: ditto to the above
        return ValidationResult(all_errors, all_warnings)

    # in short, iterates through every component on the item, and verifies that
    # the component's value matches its type.
    def validate_items_and_skills(self) -> ValidationResult:
        def _validate_component_type(obj_name: str, component_name: str, ctype: ComponentType | Tuple[ComponentType, ComponentType], cval, is_item=False) -> List[ComponentValidationError]:
            if is_item:
                error_cls = ItemComponentValidationError
            else:
                error_cls = SkillComponentValidationError
            types_and_values = []
            if isinstance(ctype, tuple):
                container = ctype[0]
                value_type = ctype[1]
                if container == ComponentType.List:
                    # list of nids
                    types_and_values = [(value_type, value) for value in cval]
                elif container in (ComponentType.Dict, ComponentType.FloatDict):
                    # see elsewhere for usages: always dict of 'nid: int'
                    types_and_values = [(value_type, key) for key, _ in cval]
                elif container == ComponentType.MultipleChoice:
                    # short-circuit. we don't use DB validation for this
                    if not cval in value_type:
                        return [error_cls(obj_name, component_name, ComponentType.MultipleChoice, cval)]
            else:
                types_and_values = [(ctype, cval)]

            errors = []
            for ctype, cvalue in types_and_values:
                if not self.dve.validate(ctype, cvalue):
                    errors.append(error_cls(obj_name, component_name, ctype, cvalue))
            return errors

        all_errors = []
        for skill in self.db.skills:
            for component in skill.components:
                # attribute components convey info by being present; they don't have values
                if not component.expose:
                    continue
                if component.expose == ComponentType.NewMultipleOptions:
                    for option in component.options.keys():
                        all_errors += _validate_component_type(skill.nid, component.name, component.options[option], component.value[option])
                else:
                    all_errors += _validate_component_type(skill.nid, component.name, component.expose, component.value)

        for item in self.db.items:
            for component in item.components:
                # attribute components convey info by being present; they don't have values
                if not component.expose:
                    continue
                if component.expose == ComponentType.NewMultipleOptions:
                    for option in component.options.keys():
                        all_errors += _validate_component_type(item.nid, component.name, component.options[option], component.value[option], True)
                else:
                    all_errors += _validate_component_type(item.nid, component.name, component.expose, component.value, True)
        return ValidationResult(all_errors)

    def validate_units(self) -> ValidationResult:
        all_errors = []
        all_warnings = []
        for unit in self.db.units:
            item_errs = [UnitValidationError(unit.nid, 'Starting Items', inid, DatabaseType.ITEMS) for inid in self.validate_generic_list(unit.get_items(), DatabaseType.ITEMS)]
            skill_errs = [UnitValidationError(unit.nid, 'Learned Skills', snid, DatabaseType.SKILLS) for snid in self.validate_generic_list(unit.get_skills(), DatabaseType.SKILLS)]

            if not self.dve.validate(DatabaseType.CLASSES, unit.klass):
                all_errors.append(UnitValidationError(unit.nid, 'Class', unit.klass, DatabaseType.CLASSES))

            for k in unit.alternate_classes:
                if not self.dve.validate(DatabaseType.CLASSES, k):
                    all_errors.append(UnitValidationError(unit.nid, 'Alternate Classes', k, DatabaseType.CLASSES))

            all_errors = all_errors + item_errs + skill_errs

        return ValidationResult(all_errors, all_warnings)

    def validate_events(self) -> ValidationResult:
        ppsr = Preprocessor(self.db.events)
        all_errors = []
        for event in self.db.events:
            if event.is_python_event():
                all_errors += ppsr.verify_event(event.nid, event.source)
        return ValidationResult(all_errors)

    def validate_for_errors(self) -> List:
        all_errors = self.validate_events().errors
        all_errors += self.validate_items_and_skills().errors
        all_errors += self.validate_levels().errors
        all_errors += self.validate_units().errors
        return all_errors
