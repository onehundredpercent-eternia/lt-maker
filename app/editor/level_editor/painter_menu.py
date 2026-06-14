from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout

from app.data.database.database import DB

from app.utilities import str_utils
from app.utilities.data import Data

from app.extensions.custom_gui import RightClickListView
from app.editor.base_database_gui import DragDropCollectionModel


class PainterMenu(QWidget):
    """
    Generic level-editor side panel for painting positioned, NID-keyed level
    objects (regions, cities, ...) onto the map.

    Subclasses inject the differing pieces via the constructor:
        noun              - display name used for the button/messages
        data_attr         - the Level attribute holding the Data list
        model_cls         - the list model (a PainterModel subclass)
        modify_widget_cls - the edit form widget
        prefab_cls        - the prefab type, with a `(nid)` ctor and `.restore`
    """
    def __init__(self, state_manager, map_view, *, noun, data_attr,
                 model_cls, modify_widget_cls, prefab_cls):
        super().__init__()
        self.state_manager = state_manager
        self.map_view = map_view
        self.noun = noun
        self.data_attr = data_attr
        self.prefab_cls = prefab_cls

        self.current_level = DB.levels.get(self.state_manager.state.selected_level)
        self._data = self._get_data()

        grid = QVBoxLayout()
        self.setLayout(grid)

        self.view = RightClickListView((None, None, None), parent=self)
        self.view.currentChanged = self.on_item_changed

        self.model = model_cls(self._data, self)
        self.view.setModel(self.model)
        grid.addWidget(self.view)

        self.create_button = QPushButton("Create %s..." % noun)
        self.create_button.clicked.connect(self.create_new)
        grid.addWidget(self.create_button)

        self.modify_widget = modify_widget_cls(self._data, self)
        grid.addWidget(self.modify_widget)

        self.check_whether_enabled()
        self.display = self.modify_widget

        self.state_manager.subscribe_to_key(
            type(self).__name__, 'selected_level', self.set_current_level)
        self.state_manager.subscribe_to_key(
            type(self).__name__, 'ui_refresh_signal', self._refresh_view)

    # --- Subclass hooks ---
    def _get_data(self):
        if self.current_level:
            return getattr(self.current_level, self.data_attr)
        return Data()

    def get_center(self, obj):
        """The map position to center on when `obj` is selected, or None."""
        return getattr(obj, 'position', None)

    # --- Shared behavior ---
    def _refresh_view(self, _=None):
        self.model.layoutChanged.emit()

    def update_list(self):
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)

    def check_whether_enabled(self):
        if not len(self._data):
            self.modify_widget.setEnabled(False)

    def _center_on(self, obj):
        center = self.get_center(obj)
        if center:
            self.map_view.center_on_pos(center)

    def set_current_level(self, level_nid):
        self.current_level = DB.levels.get(level_nid)
        self._data = self._get_data()
        self.model._data = self._data
        self.model.update()
        self.modify_widget._data = self._data
        if len(self._data):
            self.modify_widget.setEnabled(True)
            obj = self._data[0]
            self._center_on(obj)
            self.modify_widget.set_current(obj)
        else:
            self.modify_widget.setEnabled(False)

    def select(self, idx):
        index = self.model.index(idx)
        self.view.setCurrentIndex(index)

    def deselect(self):
        self.view.clearSelection()

    def on_item_changed(self, curr, prev):
        if self._data:
            obj = self._data[curr.row()]
            self._center_on(obj)
            self.modify_widget.set_current(obj)

    def get_current(self):
        for index in self.view.selectionModel().selectedIndexes():
            idx = index.row()
            if len(self._data) > 0 and idx < len(self._data):
                return self._data[idx]
        return None

    def create_new(self, example=None):
        nid = str_utils.get_next_name('New %s' % self.noun, self._data.keys())
        created = self.prefab_cls(nid)
        self._data.append(created)
        self.modify_widget.setEnabled(True)
        self.model.update()
        if len(self._data) == 1:
            self.modify_widget.set_current(created)
        idx = self._data.index(created.nid)
        index = self.model.index(idx)
        self.view.setCurrentIndex(index)
        self.state_manager.change_and_broadcast('ui_refresh_signal', None)
        return created


class PainterModel(DragDropCollectionModel):
    allow_delete_last_obj = True
    prefab_cls = None  # Subclasses set this; used by duplicate()

    def new(self, idx):
        ok = self.window.create_new()
        if ok:
            self._data.move_index(len(self._data) - 1, idx + 1)
            self.layoutChanged.emit()

    def duplicate(self, idx):
        view = self.window.view
        obj = self._data[idx]
        new_nid = str_utils.get_next_name(obj.nid, self._data.keys())
        serialized_obj = obj.save()
        new_obj = self.prefab_cls.restore(serialized_obj)
        new_obj.nid = new_nid
        self._data.insert(idx + 1, new_obj)
        self.layoutChanged.emit()
        new_index = self.index(idx + 1)
        view.setCurrentIndex(new_index)
        return new_index

    def delete(self, idx):
        super().delete(idx)
        self.window.check_whether_enabled()
