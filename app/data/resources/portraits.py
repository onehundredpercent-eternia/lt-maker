import random
from pathlib import Path
from typing import List, Optional, Set, Tuple
from typing_extensions import override

from app.constants import INFO_PORTRAIT_WIDTH, INFO_PORTRAIT_HEIGHT
from app.data.category import CategorizedCatalog
from app.data.resources.base_catalog import ManifestCatalog
from app.data.resources.resource_prefab import WithResources
from app.utilities import utils
from app.utilities.data import Prefab

def _update_talk(talk_state: int, max_state: int, reverse: bool = True) -> Tuple[int, int, bool]:
    if talk_state == 0 or talk_state == max_state-1:
        reverse = not reverse
        next_update = random.randint(70, 160)
    else:
        next_update = random.randint(30, 50)
        if random.randint(1, 10) == 1:  # 10% chance to reverse
            reverse = not reverse

    mt = 2 if random.randint(1, 10) == 1 else 1    # 10% chance to skip a frame
    if reverse:
        next_state = talk_state - mt
    else:
        next_state = talk_state + mt
    next_state = utils.clamp(next_state, 0, max_state-1)

    return next_state, next_update, reverse

class PortraitPrefab(WithResources, Prefab):
    def __init__(self, nid, full_path=None, pix=None):
        self.nid = nid
        self.full_path = full_path
        self.image = None
        self.pixmap = pix

        self.blinking_offset = [0, 0]
        self.smiling_offset = [0, 0]
        self.info_offset = (0, 0)

        self.full_size = (160, 112)
        self.face_size = (96, 80)
        self.blink_size = (32, 16)
        self.mouth_size = (32, 16)
        self.blink_frames = 2
        self.mouth_frames = 3

    @override
    def set_full_path(self, full_path):
        self.full_path = full_path

    @override
    def used_resources(self) -> List[Optional[Path]]:
        return [Path(self.full_path)]

    def save(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['blinking_offset'] = self.blinking_offset
        s_dict['smiling_offset'] = self.smiling_offset
        s_dict['info_offset'] = self.info_offset

        s_dict['full_size'] = self.full_size
        s_dict['face_size'] = self.face_size
        s_dict['blink_size'] = self.blink_size
        s_dict['mouth_size'] = self.mouth_size
        s_dict['blink_frames'] = self.blink_frames
        s_dict['mouth_frames'] = self.mouth_frames
        return s_dict

    @classmethod
    def restore(cls, s_dict):
        self = cls(s_dict['nid'])
        self.blinking_offset = [int(_) for _ in s_dict['blinking_offset']]
        self.smiling_offset = [int(_) for _ in s_dict['smiling_offset']]
        self.info_offset = tuple(int(_) for _ in s_dict['info_offset'])

        self.full_size = tuple(int(_) for _ in s_dict['full_size'])
        self.face_size = tuple(int(_) for _ in s_dict['face_size'])
        self.blink_size = tuple(int(_) for _ in s_dict['blink_size'])
        self.mouth_size = tuple(int(_) for _ in s_dict['mouth_size'])
        self.blink_frames = int(s_dict.get('blink_frames', 0))
        self.mouth_frames = int(s_dict.get('mouth_frames', 0))
        return self

    def get_face_frame(self) -> Tuple[int, int, int, int]:
        return (self.full_size[0] - self.face_size[0] - self.blink_size[0],
                self.full_size[1] - self.face_size[1] - self.mouth_size[1]*2,
                *self.face_size)

    def get_blink_frame(self, idx: int) -> Tuple[int, int, int, int]:
        return (self.full_size[0] - self.blink_size[0],
                self.full_size[1] - self.mouth_size[1]*2 - self.blink_size[1]*(self.blink_frames-idx),
                *self.blink_size)

    def get_mouth_frame(self, idx: int, smile: bool = False) -> Tuple[int, int, int, int]:
        return (self.full_size[0] - self.blink_size[0] - self.mouth_size[0]*(self.mouth_frames-idx+1),
                self.full_size[1] - self.mouth_size[1] * (2 if smile else 1),
                *self.mouth_size)

    def get_minimug(self) -> Tuple[int, int, int, int]:
        return (*utils.tuple_sub(self.full_size, (32, 32)), 32, 32)

    def get_neutral_mouth(self) -> Tuple[int, int, int, int]:
        return (self.full_size[0] - self.blink_size[0] - self.mouth_size[0],
                self.full_size[1] - self.mouth_size[1]*2,
                *self.mouth_size)

    def get_blink_coord(self) -> Tuple[int, int]:
        return utils.tuple_sub(self.face_size, self.blink_size, self.blinking_offset)

    def get_mouth_coord(self) -> Tuple[int, int]:
        return utils.tuple_sub(self.face_size, self.mouth_size, self.smiling_offset)

    def get_wink(self, left_wink: bool = True) -> Tuple[int, int, int, int]:
        return (self.full_size[0] - (self.blink_size[0] if left_wink else self.blink_size[0]//2),
                self.full_size[1] - self.mouth_size[1]*2 - self.blink_size[1],
                self.blink_size[0] // 2,
                self.blink_size[1])

    def get_wink_coord(self, left_wink: bool = True) -> Tuple[int, int]:
        return utils.tuple_sub(self.face_size, self.blink_size, self.blinking_offset,
                                (0 if left_wink else -self.blink_size[0]//2, 0))

    def get_info_coord(self) -> Tuple[int, int]:
        return utils.tuple_sub(self.face_size, self.info_offset,
                                (INFO_PORTRAIT_WIDTH, INFO_PORTRAIT_HEIGHT))

class PortraitCatalog(ManifestCatalog[PortraitPrefab], CategorizedCatalog[PortraitPrefab]):
    manifest = 'portraits.json'
    title = 'portraits'
    datatype = PortraitPrefab
