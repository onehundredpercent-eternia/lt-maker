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
        pass

    def render_ui_object(self, ui_object: UIObjectPrefab) -> QPixmap:
        from app.engine.objects.unit import UnitObject
        unit = UnitObject.from_prefab(DB.units[0])
        def surf_eval(arg, local_args):
            try:
                return evaluate(arg[5:], local_args=local_args) if (isinstance(arg, str) and arg.startswith("eval:")) else arg
            except Exception as e:
                logging.error("Failed to eval", arg[5:], repr(e))
        surf = draw_component_surf(ui_object, surf_eval, engine.create_simple_surface, manual_colorkey, {'unit': unit}, True)
        width, height = surf.get_size()

        buff = ctypes.create_string_buffer(rgba32_to_rgba64(engine.surf_to_raw(surf, 'RGBA')))
        img = QtGui.QImage(ctypes.addressof(buff), width, height, QtGui.QImage.Format.Format_RGBA64)

        pixmap = QPixmap()
        pixmap.convertFromImage(img)
        return pixmap
