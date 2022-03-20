from app.data.database import DB

from app.editor.data_editor import SingleDatabaseEditor
from app.editor.base_database_gui import DatabaseTab
from app.editor.hex_editor import hex_type_properties, hex_type_model

class HexTypeDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.hex_types
        title = "Hex Type"
        right_frame = hex_type_properties.HexTypeProperties

        def deletion_func(model, index):
            return len(model._data) > 1

        collection_model = hex_type_model.HexTypeModel
        dialog = cls(data, title, right_frame, (deletion_func, None, None), collection_model, parent)
        return dialog

def get_editor():
    return SingleDatabaseEditor(HexTypeDatabase)

# Testing
# Run "python -m app.editor.hex_type_editor.hex_type_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.resources.resources import RESOURCES
    RESOURCES.load('default.ltproj')
    DB.load('default.ltproj')
    window = SingleDatabaseEditor(HexTypeDatabase)
    window.show()
    app.exec_()
