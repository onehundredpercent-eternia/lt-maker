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

def _validate_unit_object_list(database: Database, resources: Resources, object_nids: List[NID], field_name: str, db_type: DatabaseType, unit_nid: NID, level_nid=None):
    validator = DatabaseValidatorEngine(database, resources)
    all_errors = []
    all_warnings = []

    for obj_nid in object_nids:
        if not validator.validate(db_type, obj_nid):
            if level_nid:
                all_errors.append(LevelUnitValidationError(level_nid, unit_nid, "Error in %s: No %s with name '%s'" % (field_name, db_type.name, obj_nid)))
            else:
                all_errors.append(UnitValidationError(unit_nid, field_name, obj_nid, db_type))

    return all_errors, all_warnings


def _validate_unique_unit(database: Database, resources: Resources, unique_unit: UniqueUnit, level: LevelPrefab, level_units: Set[NID], travelers: Dict[NID, NID]) -> ValidationResult:
    validator = DatabaseValidatorEngine(database, resources)
    all_errors = []
    all_warnings = []

    if unique_unit.ai and not validator.validate(DatabaseType.AI, unique_unit.ai):
        all_errors.append(LevelUnitValidationError(level.nid, unique_unit.nid, "AI %s does not exist" % unique_unit.ai))

    if unique_unit.roam_ai and not validator.validate(DatabaseType.AI, unique_unit.roam_ai):
        all_errors.append(LevelUnitValidationError(level.nid, unique_unit.nid, "Roam AI %s does not exist" % unique_unit.roam_ai))

    if unique_unit.starting_position and not resources.tilemaps.get(level.tilemap).check_bounds(unique_unit.starting_position):
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

def _validate_generic_unit(database: Database, resources: Resources, generic_unit: GenericUnit, level: LevelPrefab, level_units: Set[NID], travelers: Dict[NID, NID]) -> ValidationResult:
    validator = DatabaseValidatorEngine(database, resources)
    all_item_errors, all_item_warnings = _validate_unit_object_list(database, resources, [i[0] for i in generic_unit.starting_items], 'Items', DatabaseType.ITEMS, generic_unit.nid, level.nid)
    all_skill_errors, all_skill_warnings = _validate_unit_object_list(database, resources, generic_unit.starting_skills, 'Skills', DatabaseType.SKILLS, generic_unit.nid, level.nid)

    all_errors = all_item_errors + all_skill_errors
    all_warnings = all_item_warnings + all_skill_warnings

    if generic_unit.ai and not validator.validate(DatabaseType.AI, generic_unit.ai):
        all_errors.append(LevelUnitValidationError(level.nid, generic_unit.nid, "AI %s does not exist" % generic_unit.ai))

    if generic_unit.roam_ai and not validator.validate(DatabaseType.AI, generic_unit.roam_ai):
        all_errors.append(LevelUnitValidationError(level.nid, generic_unit.nid, "Roam AI %s does not exist" % generic_unit.roam_ai))

    if generic_unit.starting_position and not resources.tilemaps.get(level.tilemap).check_bounds(generic_unit.starting_position):
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

def _validate_region(database: Database, resources: Resources, region: Region, level_tilemap: Optional[TileMapPrefab], level_nid: NID) -> ValidationResult:
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

def validate_levels(database: Database, resources: Resources) -> ValidationResult:
    validator = DatabaseValidatorEngine(database, resources)
    all_errors = []
    all_warnings = []
    for level in database.levels:
        def _validate_attr(dtype, attr, optional=True):
            val = getattr(level, attr)
            if val is None and optional:
                return
            if not validator.validate(dtype, val):
                all_errors.append(LevelValidationError(level.nid, attr, val, dtype))

        _validate_attr(ResourceType.TILEMAPS, 'tilemap')
        _validate_attr(ResourceType.TILEMAPS, 'bg_tilemap')
        _validate_attr(DatabaseType.PARTIES, 'party')

        # music
        for music_key in database.music_keys:
            track = level.music.get(music_key)
            if track is None:
                continue
            if not validator.validate(ResourceType.MUSIC, track):
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
                vres = _validate_unique_unit(database, resources, unit, level, all_level_units, travelers)
            elif isinstance(unit, GenericUnit):
                vres = _validate_generic_unit(database, resources, unit, level, all_level_units, travelers)
            all_errors += vres.errors
            all_warnings += vres.warnings

        for region in level.regions:
            vres = _validate_region(database, resources, region, resources.tilemaps.get(level.tilemap), level.nid)
            all_errors += vres.errors
            all_warnings += vres.warnings

        # level.groups: if any warnings or errors pop up, we can add them here; can't think of any right now
        # level.ai_groups: ditto to the above
    return ValidationResult(all_errors, all_warnings)

# in short, iterates through every component on the item, and verifies that
# the component's value matches its type.
def validate_items_and_skills(database: Database, resources: Resources) -> ValidationResult:
    validator = DatabaseValidatorEngine(database, resources)
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
            if not validator.validate(ctype, cvalue):
                errors.append(error_cls(obj_name, component_name, ctype, cvalue))
        return errors

    all_errors = []
    for skill in database.skills:
        for component in skill.components:
            # attribute components convey info by being present; they don't have values
            if not component.expose:
                continue
            if component.expose == ComponentType.NewMultipleOptions:
                for option in component.options.keys():
                    all_errors += _validate_component_type(skill.nid, component.name, component.options[option], component.value[option])
            else:
                all_errors += _validate_component_type(skill.nid, component.name, component.expose, component.value)

    for item in database.items:
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

def validate_units(database: Database, resources: Resources) -> ValidationResult:
    validator = DatabaseValidatorEngine(database, resources)
    all_errors = []
    all_warnings = []
    for unit in database.units:
        all_item_errors, all_item_warnings = _validate_unit_object_list(database, resources, [i[0] for i in unit.starting_items], 'Starting Items', DatabaseType.ITEMS, unit.nid)
        all_skill_errors, all_skill_warnings = _validate_unit_object_list(database, resources, [i[1] for i in unit.learned_skills], 'Learned Skills', DatabaseType.SKILLS, unit.nid)

        if not validator.validate(DatabaseType.CLASSES, unit.klass):
            all_errors.append(UnitValidationError(unit.nid, 'Class', unit.klass, DatabaseType.CLASSES))

        for k in unit.alternate_classes:
            if not validator.validate(DatabaseType.CLASSES, k):
                all_errors.append(UnitValidationError(unit.nid, 'Alternate Classes', k, DatabaseType.CLASSES))

        all_errors = all_errors + all_item_errors + all_skill_errors
        all_warnings = all_warnings + all_item_warnings + all_skill_warnings

    return ValidationResult(all_errors, all_warnings)

def validate_events(database: Database, resources: Resources) -> ValidationResult:
    ppsr = Preprocessor(database.events)
    all_errors = []
    for event in database.events:
        if event.version() != EventVersion.EVENT:
            all_errors += ppsr.verify_event(event.nid, event.source)
        else:
            # TODO(mag): delete this on 1/1/2024, temporary measure to correctly format projects
            new_source = []
            for line in event._source:
                as_command, _ = event_commands.parse_text_to_command(line)
                if as_command:
                    nid_or_nickname = event_commands.get_command_arguments(line)[0].string
                    text = as_command.to_plain_text()
                    s = text.split(';', 1)
                    if len(s) == 1: # only command
                        reconstituted = nid_or_nickname
                    else:
                        reconstituted = nid_or_nickname + ';' + s[1]
                    new_source.append(reconstituted)
                else:
                    new_source.append(line)
            event.source = '\n'.join(new_source)
            # END
    return ValidationResult(all_errors)

def validate_for_errors(database: Database, resources: Resources) -> List:
    all_errors = validate_events(database, resources).errors
    all_errors += validate_items_and_skills(database, resources).errors
    all_errors += validate_levels(database, resources).errors
    all_errors += validate_units(database, resources).errors
    return all_errors