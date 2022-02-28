from app.resources.resources import RESOURCES
from typing import Tuple

from app.constants import TILEHEIGHT, TILEWIDTH, WINHEIGHT, WINWIDTH
from app.data.ui_prefab import UIObjectPrefab
from app.editor.settings import MainSettingsController
from app.editor.ui_editor.ui_renderer_qt import PygameQtRenderer
from app.sprites import SPRITES
from app.utilities import utils
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView


class UIComponentView(QGraphicsView):
    min_scale = 1
    max_scale = 10
    position_clicked = pyqtSignal(int, int)
    position_right_clicked = pyqtSignal(int, int)
    position_double_clicked = pyqtSignal(int, int)
    position_double_right_clicked = pyqtSignal(int, int)
    position_moved = pyqtSignal(int, int)

    def __init__(self, window=None):
        super().__init__()
        self.main_editor = window
        self.settings = MainSettingsController()
        self.qscene = QGraphicsScene(self)
        self.setScene(self.qscene)
        self.setMouseTracking(True)
        self.is_dragging = False

        self.setMinimumSize(WINWIDTH, WINHEIGHT)
        self.setStyleSheet("background-color:rgb(128, 128, 128);")

        self.current_ui_component: UIObjectPrefab = None
        self.selected_ui_component: UIObjectPrefab = None
        self.selected_ui_position: Tuple[int, int] = None

        self.show_outlines: bool = True

        self.pixmap = None
        self.screen_scale = 1

        self.ui_renderer: PygameQtRenderer = PygameQtRenderer()

        self.working_image = None

        self.current_mouse_pos = None

    def center_on_pos(self, pos):
        self.centerOn(pos[0]*TILEWIDTH, pos[1]*TILEHEIGHT)
        self.update_view()

    def set_working_component(self, ui_component: UIObjectPrefab):
        self.current_ui_component = ui_component
        self.update_view()

    def set_selected_component(self, ui_component: UIObjectPrefab):
        self.selected_ui_component = ui_component
        for pos, component in self.current_ui_component.subcomponents:
            if component == ui_component:
                self.selected_ui_position = pos
                self.update_view()
                return

    def clear_scene(self):
        self.qscene.clear()

    def update_view(self, _=None):
        if self.current_ui_component:
            self.clear_scene()
            base_pixmap: QPixmap = None
            offset = (0, 0)
            if self.current_ui_component.canvas:
                if self.current_ui_component.canvas in SPRITES.keys():
                    base_pixmap = SPRITES[self.current_ui_component.canvas].pixmap.copy()
                else:
                    base_pixmap = RESOURCES.panoramas.get(self.current_ui_component.canvas).pixmaps[0].copy()
                offset = tuple(self.current_ui_component.canvas_offset)
            else:
                base_pixmap = QPixmap(*self.current_ui_component.size)
            painter = QPainter()
            painter.begin(base_pixmap)
            component_pixmap = self.ui_renderer.render_ui_object(self.current_ui_component)
            painter.drawPixmap(*offset, *self.current_ui_component.size, component_pixmap)
            painter.end()
            self.working_image = component_pixmap
        else:
            self.working_image = None
            self.clear_scene()
        self.draw_component()

    def draw_selected_component(self):
        if self.selected_ui_component and self.selected_ui_position:
            size = self.selected_ui_component.size
            painter = QPainter()
            painter.begin(self.working_image)
            painter.setPen(QColor(255, 0, 0, 128))
            painter.setBrush(QColor(128, 0, 0, 128))
            painter.drawRect(*self.selected_ui_position, *size)
            painter.end()

    def draw_component_outlines(self):
        if self.current_ui_component and self.current_ui_component.subcomponents:
            painter = QPainter()
            painter.begin(self.working_image)
            for pos, component in self.current_ui_component.subcomponents:
                color = utils.hash_to_color(utils.strhash(component.nid))
                painter.setPen(QPen(QColor(*color, 128), 1))
                size = component.size
                painter.drawRect(*pos, *size)
            # draw bounds of component itself
            size = self.current_ui_component.size
            painter.setPen(QPen(QColor(255, 0, 0, 255), 2))
            painter.drawRect(0, 0, *size)
            painter.end()

    def draw_component(self):
        if self.working_image:
            self.clear_scene()
            if self.show_outlines:
                self.draw_component_outlines()
            self.draw_selected_component()
            if self.current_ui_component and self.current_ui_component.canvas:
                if self.current_ui_component.canvas in SPRITES.keys():
                    canvas_sprite = SPRITES[self.current_ui_component.canvas].pixmap.copy()
                else:
                    panorama = RESOURCES.panoramas.get(self.current_ui_component.canvas)
                    if not panorama.pixmaps:
                        for path in panorama.get_all_paths():
                            panorama.pixmaps.append(QPixmap(path))
                    canvas_sprite = panorama.pixmaps[0].copy()
                canvas = self.qscene.addPixmap(canvas_sprite)
                ox, oy = self.current_ui_component.canvas_offset
                canvas.setPos(-ox, -oy)
            else:
                if self.working_image:
                    white_bg = QPixmap(self.working_image.size())
                    white_bg.fill(QColor(255, 255, 255, 255))
                    self.qscene.addPixmap(white_bg)
            self.qscene.addPixmap(self.working_image)
            self.qscene.setSceneRect(0, 0, self.working_image.width(), self.working_image.height())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        scene_pos = self.mapToScene(event.pos())
        x, y = scene_pos.x(), scene_pos.y()
        pos = (x, y)
        self.is_dragging = True

        if(event.buttons() == Qt.RightButton):
            self.position_right_clicked.emit(*pos)
        else:
            self.position_clicked.emit(*pos)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        self.is_dragging = False

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        scene_pos = self.mapToScene(event.pos())
        x, y = scene_pos.x(), scene_pos.y()
        pos = (x, y)

        if self.current_ui_component and x < self.current_ui_component.size[0] and y < self.current_ui_component.size[1]:
            if(event.buttons() == Qt.RightButton):
                self.position_double_right_clicked.emit(*pos)
            else:
                self.position_double_clicked.emit(*pos)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.pos())
        x, y = scene_pos.x(), scene_pos.y()
        pos = (x, y)

        if self.current_ui_component and x < self.current_ui_component.size[0] and y < self.current_ui_component.size[1]:
            self.position_moved.emit(*pos)
            self.current_mouse_pos = pos
        else:
            self.position_moved.emit(-1, -1)

    def zoom_in(self):
        if self.screen_scale < self.max_scale:
            self.screen_scale += 0.2
            self.scale(1.2, 1.2)

    def zoom_out(self):
        if self.screen_scale > self.min_scale:
            self.screen_scale -= 0.2
            self.scale(0.8, 0.8)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        elif event.angleDelta().y() < 0:
            self.zoom_out()
