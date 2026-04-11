from dataclasses import dataclass, field
from typing import Tuple, List, Union, Literal

from app.data.category import CategorizedCatalog
from app.data.resources.resource_types import ResourceType
from app.utilities.data import Data, Prefab
from app.utilities import str_utils

@dataclass
class CreditEntry(Prefab):
    nid: str = None
    sub_nid: str = None
    credit_type: Union[ResourceType, Literal["List", "Text"]] = "Text"
    category: str = "Graphics"

    icon_index: Tuple[int, int] = field(default_factory=tuple)
    contrib: List[Tuple[str, str]] = field(default_factory=list)    # (author, contribution)

    def save_attr(self, name, value):
        if isinstance(value, ResourceType):
            return value.value
        elif name == 'contrib':
            return value.copy()
        return super().save_attr(name, value)

    def restore_attr(self, name, value):
        if name == 'credit_type' and isinstance(value, int):
            return ResourceType(value)
        elif name == 'contrib':
            return value.copy()
        return super().restore_attr(name, value)

    def header(self):
        return self.credit_type.name.replace('_', ' ').capitalize() \
                    if isinstance(self.credit_type, ResourceType) \
                    else self.sub_nid


class CreditCatalog(CategorizedCatalog[CreditEntry]):
    datatype = CreditEntry

    def create_new(self, db):
        nids = [d.nid for d in self]
        nid = sub_nid = str_utils.get_next_name("New Entry", nids)
        new_credit = CreditEntry(nid, sub_nid)
        self.append(new_credit)
        return new_credit

    def check_credits_enabled(self) -> bool:
        """Check if credits should be shown on title screen.
        
        Returns True if:
        1. _show_credits game var is True (override), OR
        2. title_credits constant is True (global setting)
        """
        # Import here to avoid circular imports
        from app.data.database.database import DB
        from app.engine.game_state import game
        
        # Check override first - if explicitly forced, show credits
        if game.game_vars.get('_show_credits', False):
            return True
            
        # Check global constant setting
        return DB.constants.value('title_credits')
