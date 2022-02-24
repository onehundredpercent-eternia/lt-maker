from app.engine.text_evaluator import TextEvaluator
import ctypes

from app.constants import COLORKEY
from app.data.database import DB
from app.data.ui_prefab import UIObjectPrefab
from app.engine import engine, image_mods
from app.engine.evaluate import evaluate
from app.engine.graphics.ingame_ui.ui_components import draw_component_surf
from app.utilities.byte_utils import rgba32_to_rgba64
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap

import logging

def manual_colorkey(surf):
    return image_mods.simple_color_convert(surf, {COLORKEY: (0, 0, 0, 0)})

class PygameQtRenderer(object):
    def __init__(self) -> None:
        self.local_units = None

    def render_ui_object(self, ui_object: UIObjectPrefab) -> QPixmap:
        if not self.local_units:
            from app.engine.objects.unit import UnitObject
            self.local_units = {}
            for unit in DB.units:
                new_unit = UnitObject.from_prefab(unit)
                self.local_units[new_unit.nid] = new_unit
        local_args = {'unit': list(self.local_units.values())[0]}
        local_args.update(self.local_units)
        evaler = TextEvaluator(logging.getLogger(), None, unit=list(self.local_units.values())[0])
        surf = draw_component_surf(ui_object, engine.create_simple_surface, manual_colorkey, local_args, True, evaler)
        width, height = surf.get_size()

        buff = ctypes.create_string_buffer(rgba32_to_rgba64(engine.surf_to_raw(surf, 'RGBA')))
        img = QtGui.QImage(ctypes.addressof(buff), width, height, QtGui.QImage.Format.Format_RGBA64)

        pixmap = QPixmap()
        pixmap.convertFromImage(img)
        return pixmap
