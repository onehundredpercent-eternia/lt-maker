from app.data.database.database import DB

from app.editor.base_database_gui import DatabaseTab
from app.editor.data_editor import SingleDatabaseEditor

from app.editor.party_editor import party_model, party_properties

class PartyDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.parties
        title: str = _("Party")
        right_frame = party_properties.PartyProperties

        def deletion_func(model, index):
            return model.rowCount() > 1

        collection_model = party_model.PartyModel
        return cls(data, title, right_frame, (deletion_func, None, None), collection_model, parent)

# Run "python -m app.editor.party_editor.party_tab" from main directory
if __name__ == '__main__':
    import sys
    import gettext
    from PyQt5.QtWidgets import QApplication, QPushButton
    app = QApplication(sys.argv)
    from app.data.resources.resources import RESOURCES
    current_locale = 'en_US'
    locale_path = 'locale/'
    translation_module = gettext.translation(
        domain='messages',
        localedir=locale_path,
        languages=[current_locale]
    )
    translation_module.install()  # Magically make the _ function globally available
    RESOURCES.load('default.ltproj')
    DB.load('default.ltproj')
    window = SingleDatabaseEditor(PartyDatabase)
    delete_eirika_button = QPushButton("Delete Eirika")
    def delete_eirika():
        if 'Eirika' in DB.units.keys():
            DB.units.remove_key('Eirika')
            unit_box_model = window.tab.right_frame.leader_box.model
            unit_box_model.dataChanged.emit(unit_box_model.index(
                0), unit_box_model.index(unit_box_model.rowCount()))
    delete_eirika_button.clicked.connect(delete_eirika)
    window.layout().addWidget(delete_eirika_button)
    window.show()
    app.exec_()
