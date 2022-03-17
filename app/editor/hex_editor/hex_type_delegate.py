from PyQt5.QtWidgets import QDoubleSpinBox, QItemDelegate

from app.editor.custom_widgets import GlobalEventBox

class HexTypeDelegate(QItemDelegate):
    event_column = 0
    float_column = 1

    def create_editor(self, parent, option, index):
        if index.column() == self.event_column:
            editor = GlobalEventBox(parent)
            return editor
        elif index.column() == self.float_column:
            editor = QDoubleSpinBox(parent)
            editor.setRange(0, 20)
            editor.setStepSize(0.1)
            return editor
        else:
            return super().createEditor(parent, option, index)
