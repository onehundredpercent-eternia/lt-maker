from __future__ import annotations

from .database.database_types import DatabaseType
from .resources.resource_types import ResourceType
from .database.components import ComponentType

def map_component_type(ctype: ComponentType) -> DatabaseType | ResourceType | None:
  if ctype == ComponentType.Bool:
    return None
  if ctype == ComponentType.Int:
    return None
  if ctype == ComponentType.Float:
    return None
  if ctype == ComponentType.String:
    return None
  if ctype == ComponentType.WeaponType:
    return DatabaseType.WEAPONS
  if ctype == ComponentType.WeaponRank:
    return DatabaseType.WEAPON_RANKS
  if ctype == ComponentType.Unit:
    return DatabaseType.UNITS
  if ctype == ComponentType.Class:
    return DatabaseType.CLASSES
  if ctype == ComponentType.Tag:
    return DatabaseType.TAGS
  if ctype == ComponentType.Color3:
    return None
  if ctype == ComponentType.Color4:
    return None
  if ctype == ComponentType.Item:
    return DatabaseType.ITEMS
  if ctype == ComponentType.Skill:
    return DatabaseType.SKILLS
  if ctype == ComponentType.Stat:
    return DatabaseType.STATS
  if ctype == ComponentType.MapAnimation:
    return ResourceType.ANIMATIONS
  if ctype == ComponentType.Equation:
    return DatabaseType.EQUATIONS
  if ctype == ComponentType.MovementType:
    return DatabaseType.MCOST
  if ctype == ComponentType.Sound:
    return ResourceType.SFX
  if ctype == ComponentType.AI:
    return DatabaseType.AI
  if ctype == ComponentType.Music:
    return ResourceType.MUSIC
  if ctype == ComponentType.CombatAnimation:
    return ResourceType.COMBAT_ANIMS
  if ctype == ComponentType.EffectAnimation:
    return ResourceType.COMBAT_EFFECTS
  if ctype == ComponentType.Affinity:
    return DatabaseType.AFFINITIES
  if ctype == ComponentType.Terrain:
    return DatabaseType.TERRAIN
  if ctype == ComponentType.Event:
    return DatabaseType.EVENTS
  return None