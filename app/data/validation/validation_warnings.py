from dataclasses import dataclass

from app.utilities.typing import NID

@dataclass
class NoneFieldWarning():
    nid: NID
    field_name: str
    object_type = "Unknown"
    error_template = \
"""
    In {type} '{nid}':
        Warning in field {field_name}:
    {field_name} not set or set to empty.
"""

    def __str__(self) -> str:
        return self.error_template.format(type=self.object_type, nid=self.nid,
                                          field_name=self.field_name)

class LevelNoneFieldWarning(NoneFieldWarning):
    object_type = "Level"

@dataclass
class RegionWarning():
    level: NID
    reg_nid: NID
    what: str
    error_template = \
"""
    In level '{level}' and region '{reg_nid}':
    {what}
"""

    def __str__(self) -> str:
        return self.error_template.format(level=self.level, reg_nid=self.reg_nid, what = self.what)