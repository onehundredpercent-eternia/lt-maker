import os
from pathlib import Path
import shutil
from typing import List, Optional, Set
from typing_extensions import override

from app.data.resources.base_catalog import ManifestCatalog
from app.data.resources.resource_prefab import WithResources
from app.utilities.data import HasNid, Prefab
from app.utilities.typing import NestedPrimitiveDict

class SoundFontPrefab(HasNid, WithResources, Prefab):
    def __init__(self, nid):
        self.nid = nid

    @override
    def set_full_path(self, full_path):
        self.full_path = full_path

    @override
    def used_resources(self) -> List[Optional[Path]]:
        return [Path(self.full_path)]

    def save(self) -> NestedPrimitiveDict:
        return {"nid": self.nid}

    @classmethod
    def restore(cls, s_dict: NestedPrimitiveDict):
        return cls(s_dict["nid"])

class SongPrefab(HasNid, WithResources, Prefab):
    def __init__(self, nid, format='ogg'):
        self.nid = nid
        self.format = format

        # path info
        self.full_path = None
        # Mutually exclusive. Can't have both start and battle versions
        self.intro_full_path = None
        self.battle_full_path = None

    def set_intro_full_path(self, full_path):
        self.intro_full_path = full_path

    def set_battle_full_path(self, full_path):
        self.battle_full_path = full_path

    def save(self) -> NestedPrimitiveDict:
        return {"nid": self.nid,
                "format": self.format}

    @override
    def set_full_path(self, path: str) -> None:
        self.full_path = path + '.' + self.format
        parent_path = Path(path).parent
        battle_full_path = parent_path / (self.nid + '-battle.' + self.format)
        intro_full_path = parent_path / (self.nid + '-intro.' + self.format)
        if battle_full_path.exists():
            self.battle_full_path = str(battle_full_path)
        elif intro_full_path.exists():
            self.intro_full_path = str(intro_full_path)

    @override
    def used_resources(self) -> List[Optional[Path]]:
        paths = [Path(self.full_path)]
        paths.append(Path(self.intro_full_path) if self.intro_full_path else None)
        paths.append(Path(self.battle_full_path) if self.battle_full_path else None)
        return paths

    @classmethod
    def restore(cls, s_dict: NestedPrimitiveDict):
        return cls(s_dict['nid'], format=s_dict['format'])

class MusicCatalog(ManifestCatalog[SongPrefab]):
    filetype = ''
    manifest = 'music.json'
    title = 'music'
    datatype = SongPrefab

class SFXPrefab(HasNid, WithResources, Prefab):
    def __init__(self, nid, full_path=None, tag=None):
        self.nid = nid
        self.tag = tag
        # self.length = None
        self.full_path = full_path

    @override
    def set_full_path(self, full_path):
        self.full_path = full_path

    @override
    def used_resources(self) -> List[Optional[Path]]:
        return [Path(self.full_path)]

    def save(self):
        return (self.nid, self.tag)

    @classmethod
    def restore(cls, s_tuple):
        self = cls(s_tuple[0], tag=s_tuple[1])
        # if len(s_tuple) > 2:
        #     self.length = s_tuple[2]
        return self

class SFXCatalog(ManifestCatalog[SFXPrefab]):
    manifest = 'sfx.json'
    title = 'sfx'
    filetype = '.ogg'
    datatype = SFXPrefab

class SoundFontCatalog(ManifestCatalog[SoundFontPrefab]):
    manifest = 'soundfonts.json'
    title = 'soundfonts'
    filetype = '.sf2'
    datatype = SoundFontPrefab