from typing import Callable
from PyQt5 import QtGui
from PyQt5.QtWidgets import QDialog, QGridLayout, QDialogButtonBox, QWidget
from PyQt5.QtCore import Qt

from app.editor.settings import MainSettingsController

class DatabaseEditorDialog(QDialog):
    def __init__(self, parent: QWidget, database_tab: QWidget, on_accept: Callable, on_apply: Callable, on_cancel: Callable, title: str = 'Database Editor'):
        super().__init__(parent)
        self.on_accept = on_accept
        self.on_cancel = on_cancel
        self.on_apply = on_apply

        self.set_up()
        self.tab = database_tab
        self.tab.setParent(self)
        self.grid.addWidget(self.tab, 0, 0, 1, 2)

        self.setWindowTitle(title)

        # Restore Geometry
        self.settings = MainSettingsController()
        geometry = self.settings.component_controller.get_geometry(self._type())
        if geometry:
            self.restoreGeometry(geometry)

    def keyPressEvent(self, keypress: QtGui.QKeyEvent) -> None:
        if keypress.key() == self.settings.get_editor_close_button():
            self.reject()

    def set_up(self):
        self.setStyleSheet("font: 10pt;")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint, True)

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

    def accept(self):
        super().accept()
        if self.on_accept:
            self.on_accept
        self.save_geometry()

    def reject(self):
        super().reject()
        if self.on_cancel:
            self.on_cancel()
        self.save_geometry()

    def apply(self):
        if self.on_apply:
            self.on_apply()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.save_geometry()

    def _type(self):
        return self.tab.__class__.__name__

    def save_geometry(self):
        self.settings.component_controller.set_geometry(self._type(), self.saveGeometry())