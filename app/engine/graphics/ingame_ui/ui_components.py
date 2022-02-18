from __future__ import annotations

from abc import ABC, abstractmethod
from app.data.units import UnitPrefab
from app.utilities.typing import NID
from app.engine.objects.ui_object import UIObject
from app.engine.interfaces.idrawable import IDrawable
from app.engine.evaluate import evaluate
import logging
from typing import Any, Callable, Dict, List, Tuple, Type

from app.data.database import DB
from app.data.items import ItemPrefab
from app.data.skills import SkillPrefab
from app.engine import engine, icons
from app.engine.fonts import FONT
from app.engine.graphics.ui_framework.ui_framework_layout import HAlignment
from app.engine.objects.unit import UnitObject
from app.engine.sprites import SPRITES
from app.utilities import utils


class SurfComponent(ABC):
    @abstractmethod
    def to_surf(self, create_surface=engine.create_surface) -> engine.Surface:
        pass

class ChibiPortrait(SurfComponent):
    """
    Component prefab for drawing chibi portraits
    """
    def __init__(self, unit: UnitObject | NID=None):
        if isinstance(unit, NID):
            self.unit: UnitPrefab = DB.units.get(unit)
            self.game_unit = False
        else:
            self.unit: UnitObject = unit
            self.game_unit = True

    def to_surf(self, create_surface=engine.create_surface) -> engine.Surface:
        chibi_dimensions = (32, 32)
        surf = create_surface(chibi_dimensions, transparent=True)

        # Draw portrait/faction on surf
        if self.game_unit and self.unit.generic:
            icons.draw_faction(surf, DB.factions.get(self.unit.faction), (0, 0))
        else:
            icons.draw_chibi(surf, self.unit.portrait_nid, (0, 0))
        return surf

class Text(SurfComponent):
    """
    Component prefab for drawing text
    """
    def __init__(self, font: str='text', color: str='white', text: str='text', width: str='24', alignment: str='center'):
        self.font: FONT = FONT[font]
        self.color: str = color
        self.text: str = str(text)
        self.width: int = int(width)
        self.alignment: HAlignment = HAlignment(alignment)

    def to_surf(self, create_surface=engine.create_surface) -> engine.Surface:
        surf = create_surface((self.width, self.font.height), transparent=True)
        if self.alignment == HAlignment.RIGHT:
            self.font.blit(self.text, surf, (max(0, self.width - self.font.width(self.text)), 0), self.color)
        elif self.alignment == HAlignment.CENTER:
            self.font.blit(self.text, surf, (max(0, self.width//2 - self.font.width(self.text)//2), 0), self.color)
        else:
            self.font.blit(self.text, surf, (0, 0), self.color)
        return surf

class Name(SurfComponent):
    '''
    Component prefab for drawing unit/item/skill name text
    '''
    def __init__(self, font: str='info', color: str='grey', source: ItemPrefab | SkillPrefab | UnitObject=None, width: int='92', alignment: str='center'):
        self.font: str = font
        self.color: str = color
        self.width: int = int(width)
        self.alignment: str = alignment
        self.source: ItemPrefab | SkillPrefab | UnitObject = source

    def to_surf(self, create_surface=engine.create_surface) -> engine.Surface:
        name: str = None
        if isinstance(self.source, UnitObject):
            name = self.get_unit_name(self.source)

        if isinstance(self.source, ItemPrefab):
            name = self.source.name

        if isinstance(self.source, SkillPrefab):
            name = self.source.name

        return Text(self.font, self.color, name, self.width, self.alignment).to_surf(create_surface)

    def get_unit_name(self, unit):
        unit_name: str = None
        if unit.generic:
            short_name = DB.classes.get(unit.klass).name
            unit_name = short_name + " " + str(unit.level)
        else:
            unit_name = unit.name
        return unit_name


class StatBar(SurfComponent):
    """
    Component prefab for drawing resource based-stats (i.e. Health, Mana)
    """

    args = ['EvalCurrentStat', 'EvalMaxStat', 'BarColor', 'StatName']

    def __init__(self, curr_stat: int=0, max_stat: int=1, color: str='yellow', stat_name: str='health'):
        self.curr_stat: int = curr_stat
        self.max_stat: int = max_stat
        self.color: str = color
        self.stat_name: str = stat_name

    def to_surf(self, create_surface=engine.create_surface) -> engine.Surface:
        # Create surf
        surf = create_surface((54, 14), transparent=True)
        font = FONT['info']

        # Draw health or mana text icon based on stat_name
        if self.stat_name == 'health':
            surf.blit(SPRITES.get('unit_info_hp'), (0, 0))
        else:
            surf.blit(SPRITES.get('unit_info_sp'), (0, 0))
        surf.blit(SPRITES.get('unit_info_slash'), (32, 1))

        # Text for current value / maximum value
        font.blit_right(str(self.curr_stat), surf, (33, -4), color='grey')
        font.blit_right(str(self.max_stat), surf, (55, -4), color='grey')

        # Bar background BG
        bg_surf = SPRITES.get('health_bar2_bg')
        surf.blit(bg_surf, (2, 10))

        # Draw the actual bar
        bar_ratio = utils.clamp(float(self.curr_stat) / float(self.max_stat), 0, 1)
        if bar_ratio > 0:
            if self.color == 'yellow':
                bar_surf = SPRITES.get('health_bar2')
            else:
                bar_surf = SPRITES.get('health_bar2_red')
            idx = int(bar_ratio * bar_surf.get_width())
            bar_surf = engine.subsurface(bar_surf, (0, 0, idx, 2))
            surf.blit(bar_surf, (3, 11))

        return surf

class Icon(SurfComponent):
    """
    Component prefab for drawing skill/item icons
    """

    args = ['Item/Skill']

    def __init__(self, source: ItemPrefab | SkillPrefab | NID=None):
        if isinstance(source, NID):
            if source in DB.items.keys():
                self.source = DB.items.get(source)
            elif source in DB.skills.keys():
                self.source = DB.skills.get(source)
        else:
            self.source: ItemPrefab | SkillPrefab = source

    def to_surf(self, create_surface=engine.create_surface) -> engine.Surface:
        icon_dimensions = (16, 16)
        surf = create_surface(icon_dimensions, transparent=True)
        icon = icons.get_icon(self.source)
        if icon:
            surf.blit(icon, (0, 0))
        return surf

COMPONENT_MAP: Dict[str, Type[SurfComponent]] = {
    'chibi' : ChibiPortrait,
    'text' : Text,
    'name' : Name,
    'stat_bar' : StatBar,
    'icon' : Icon
}

def draw_component_surf(ui_object: UIObject, _eval_func: Callable[[str, Dict], str] = None, create_surface: Callable[[], engine.Surface]=engine.create_surface,
                        post_process: Callable[[engine.Surface], engine.Surface]=None, local_args: Dict[str, Any] = None, log_errors = True) -> engine.Surface:
    # default eval
    if not _eval_func:
        _eval_func = lambda arg, lc: evaluate(arg[5:], local_args=lc) if isinstance(arg, str) and arg.startswith("eval:") else arg

    # Create the base surface
    surf = create_surface(ui_object.size, transparent=True)
    if ui_object.bg_sprite:
        bg = SPRITES.get(ui_object.bg_sprite).copy()
        if post_process:
            bg = post_process(bg)
        surf.blit(bg, (0,0))

    ui_args = {}
    sublocal_args = local_args.copy() if local_args else {}
    for argtype, argvalue in ui_object.arguments.items():
        ui_args[argtype] = _eval_func(argvalue, local_args)
        sublocal_args[argtype] = _eval_func(argvalue, local_args)

    # If this UI object has a value and its nid references a corresponding component, blit it to the surf
    if ui_object.nid in COMPONENT_MAP.keys():
        surf = COMPONENT_MAP[ui_object.nid](**ui_args).to_surf(create_surface)
        if post_process:
            surf = post_process(surf)
        surf.blit(surf, (0,0))

    # Iterate through each subcomponent and draw each one
    for pos, component in ui_object.subcomponents:
        try:
            subsurf = draw_component_surf(component, _eval_func, create_surface, post_process, sublocal_args, log_errors)
            surf.blit(subsurf, pos)
        except Exception as e:
            if log_errors:
                logging.error("Drawing of component '%s' in component '%s' failed with error '%s'", component.nid, ui_object.nid, repr(e))
            if component.can_be_invalid:
                pass
            else:
                return create_surface(ui_object.size, transparent=True)

    return surf
