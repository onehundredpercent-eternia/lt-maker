from __future__ import annotations

import math
import os
import threading
from typing import TYPE_CHECKING, Optional, Tuple, Type
from PyQt5 import QtCore

from PyQt5.QtCore import QRect, QSize, Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QFontMetrics, QPainter, QPalette, QTextCursor, QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QApplication,
                             QCheckBox, QCompleter, QDialog, QFrame,
                             QGridLayout, QHBoxLayout, QHeaderView, QLabel,
                             QLineEdit, QListView, QMenu, QMessageBox,
                             QPlainTextEdit, QPushButton, QSizePolicy,
                             QSpinBox, QSplitter, QStyle, QStyledItemDelegate,
                             QTextEdit, QToolBar, QVBoxLayout, QWidget)

from app import dark_theme
from app.constants import PORTRAIT_HEIGHT, PORTRAIT_WIDTH
from app.data.database.database import DB
from app.data.resources.resources import RESOURCES
from app.data.resources.sounds import SFX, Song
from app.editor.event_editor import event_autocompleter, event_formatter
from app.editor.event_editor.utils import EditorLanguageMode
from app.editor.settings import MainSettingsController
from app.engine.sound import get_sound_thread
from app.events import event_validators
from app.events.event_portrait import EventPortrait
from app.utilities import str_utils

if TYPE_CHECKING:
    from app.editor.event_editor.event_properties import EventProperties
    from app.editor.event_editor.event_text_editor import EventTextEditor

class SoundWidget(QWidget):
    def __init__(self) -> None:
        super().__init__(None)
        self.play_button = QPushButton("Play Sound", self)
        self.play_button.clicked.connect(self.play_sound)
        self.sound: Optional[SFX | Song] = None

        layout = QVBoxLayout()
        layout.addWidget(self.play_button)
        self.setLayout(layout)

    def set_sound(self, sound: SFX | Song):
        self.sound = sound
        if sound:
            self.play_button.setDisabled(False)
        else:
            self.play_button.setDisabled(True)

    def play_sound(self):
        if self.sound and isinstance(self.sound, SFX):
            get_sound_thread().play_sfx(self.sound.nid)
        elif self.sound and isinstance(self.sound, Song):
            get_sound_thread().load_songs([self.sound.nid])
            get_sound_thread().play_raw_music(self.sound.nid)
            # only play 10 sec preview
            t = threading.Timer(5.0, self.stop_sound, [self.sound.nid])
            t.daemon = True
            t.start()

    def stop_sound(self, song_nid):
        get_sound_thread().stop_raw_music(song_nid)


class EventObjectViewer(QWidget):
    def __init__(self, parent: EventTextEditor):
        super().__init__(parent)
        self.editor = parent

        self.frame = QFrame()
        main_frame_layout = QVBoxLayout()

        self.sound_player = SoundWidget()
        self.image_display = QLabel(self)
        self.curr_data = None
        self.curr_dtype = None

        main_frame_layout.addWidget(self.sound_player)
        main_frame_layout.addWidget(self.image_display)
        self.frame.setLayout(main_frame_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.frame)
        self.setLayout(layout)
        self.frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)

    def update_display(self):
        data = self.curr_data
        dtype = self.curr_dtype
        self.sound_player.hide()
        self.image_display.hide()
        if dtype == event_validators.Sound:
            sfx = RESOURCES.sfx.get(data)
            if sfx:
                self.sound_player.set_sound(sfx)
                self.sound_player.show()
        elif dtype == event_validators.Music:
            music = RESOURCES.music.get(data)
            if music:
                self.sound_player.set_sound(music)
                self.sound_player.show()
        elif dtype in (event_validators.Portrait, event_validators.PortraitNid, event_validators.Speaker, event_validators.UniqueUnit,
                       event_validators.Unit, event_validators.GlobalUnit, event_validators.GlobalUnitOrConvoy):
            portrait = RESOURCES.portraits.get(data)
            if not portrait:
                unit = DB.units.get(data)
                if unit:
                    portrait = RESOURCES.portraits.get(unit.portrait_nid)
            if portrait:
                if not portrait.pixmap:
                    portrait.pixmap = QPixmap(portrait.full_path)
                pixmap = portrait.pixmap.copy(*EventPortrait.main_portrait_coords)
                self.image_display.setPixmap(pixmap)
                self.image_display.show()
        elif dtype in (event_validators.Panorama,):
            panorama = RESOURCES.panoramas.get(data)
            if panorama:
                if not panorama.pixmaps:
                    for path in panorama.get_all_paths():
                        panorama.pixmaps.append(QPixmap(path))
                pixmap = panorama.pixmaps[0]
                self.image_display.setPixmap(pixmap)
                self.image_display.show()
        self.frame.updateGeometry()
        self.updateGeometry()

    def displaying_data(self) -> bool:
        return not all([self.sound_player.isHidden(), self.image_display.isHidden()])

    def set_data(self, data: str, dtype: Type[event_validators.Validator]):
        if data == self.curr_data and dtype == self.curr_dtype:
            return
        self.curr_data = data
        self.curr_dtype = dtype
        valid = self.update_display()
        return valid