from PyQt5.QtWidgets import QDoubleSpinBox, QItemDelegate

from app.data.database import DB

from app.extensions.custom_gui import ComboBox

class HexEventDelegate(QItemDelegate):
    event_column = 0
    float_column = 1

    def createEditor(self, parent, option, index):
        print("Create Editor")
        if index.column() == self.event_column:
            editor = ComboBox(parent)
            for event in DB.events:
                if not event.level_nid and not event.trigger:
                    editor.addItem(event.nid)
            return editor
            return editor
        elif index.column() == self.float_column:
            editor = QDoubleSpinBox(parent)
            editor.setRange(0, 20)
            editor.setSingleStep(0.1)
            return editor
        else:
            return super().createEditor(parent, option, index)
