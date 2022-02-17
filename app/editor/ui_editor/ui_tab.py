from typing import Callable, Optional, Tuple

from app.data.database import DB
from app.data.ui_prefab import UIObjectPrefab
from app.editor.lib.state_editor.editor_state_manager import EditorStateManager
from app.editor.settings.main_settings_controller import MainSettingsController
from app.editor.ui_editor.ui_component_model import ComponentModel
from app.editor.ui_editor.ui_editor_view import UIComponentView
from app.editor.ui_editor.ui_property_menus import (UIContainerProperties,
                                                    UIElementProperties)
from app.utilities.typing import NID
from app.utilities.utils import tuple_add, tuple_sub
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QDialog,
                             QDialogButtonBox, QFrame, QGridLayout, QListView,
                             QPushButton, QSplitter, QVBoxLayout, QWidget)


class ComponentMenu(QWidget):
    def __init__(self, parent=None, state_manager=None, model=None, on_edit=None, on_add=None, on_new=None):
        super().__init__(parent)
        self.ui_editor = parent
        self.state_manager: EditorStateManager = state_manager
        self.on_edit: Callable = on_edit
        self.on_add: Callable = on_add
        self.on_new: Callable = on_new

        grid = QGridLayout()
        self.setLayout(grid)

        self.view = QListView(self)
        self.view.doubleClicked.connect(self.on_double_click)

        self.model: ComponentModel = model
        self.view.setModel(self.model)

        grid.addWidget(self.view, 3, 0, 1, 2)

        self.edit_button = QPushButton("Edit")
        grid.addWidget(self.edit_button, 4, 0, 1, 1)
        self.edit_button.clicked.connect(self.on_edit_click)

        self.add_button = QPushButton("Add")
        grid.addWidget(self.add_button, 4, 1, 1, 1)
        self.add_button.clicked.connect(self.on_add_click)

        self.reset_button = QPushButton('Create new')
        grid.addWidget(self.reset_button, 5, 0, 1, 2)
        self.reset_button.clicked.connect(self.on_new_click)

        self.state_manager.subscribe_to_key(self.__class__.__name__, 'ui_refresh_signal', lambda _: self.model.layoutChanged.emit())

    def on_edit_click(self):
        if self.on_edit:
            self.on_edit(self.get_current_nid())

    def on_add_click(self):
        if self.on_add:
            self.on_add(self.get_current_nid())

    def on_new_click(self):
        if self.on_new:
            self.on_new()

    def on_double_click(self):
        # double click intuitive functionality:
        # if i double click a basic Text component, i want to add it to my workspace
        # if i double click a complex Minimug component, i want to edit it
        curr = DB.custom_ui.get(self.get_current_nid())
        if curr and curr.generic:
            self.on_add_click()
        elif curr and not curr.generic:
            self.on_edit_click()

    def on_visibility_changed(self, state):
        pass

    def get_alpha(self):
        return int(self.alpha_slider.value())

    def set_working_nid(self, nid):
        idx = self.model.index(DB.custom_ui.index(nid))
        self.view.setCurrentIndex(idx)

    def get_current_nid(self):
        index = self.view.currentIndex()
        ui_component = DB.custom_ui[index.row()]
        return ui_component.nid

    def delete_component(self):
        self.model.delete(self.view.currentIndex().row())

    def keyPressEvent(self, keypress) -> None:
        if keypress.key() == Qt.Key_Delete:
            self.delete_component()
        else:
            pass

class UIEditor(QDialog):
    def __init__(self, parent: Optional[QWidget]) -> None:
        super().__init__(parent=parent)
        self.save()
        self.setWindowTitle("UI Editor")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet("font: 10pt;")
        self.settings = MainSettingsController()

        self.state_manager = EditorStateManager()
        self.model = ComponentModel(DB.custom_ui, self)

        desktop = QDesktopWidget()
        main_screen_size = desktop.availableGeometry(desktop.primaryScreen())
        default_size = main_screen_size.width()*0.7, main_screen_size.height()*0.7
        self.resize(*default_size)

        self.current: UIObjectPrefab = None
        self.selected_component: UIObjectPrefab = None
        self.selected_component_offset: Tuple[int, int] = (0, 0)

        self.view = UIComponentView(self)
        self.view.set_working_component(self.current)
        self.view.position_clicked.connect(self.select_component)
        self.view.position_right_clicked.connect(self.deselect_component)
        self.view.position_moved.connect(self.move_component)

        right_splitter = QSplitter(self)
        right_splitter.setOrientation(Qt.Vertical)
        right_splitter.setChildrenCollapsible(False)
        self.subcomponent_property_menu = UIElementProperties(self, self.state_manager)
        self.component_property_menu = UIContainerProperties(self, self.state_manager)
        right_splitter.addWidget(self.subcomponent_property_menu)
        right_splitter.addWidget(self.component_property_menu)

        self.main_splitter = QSplitter(self)
        self.main_splitter.setChildrenCollapsible(False)

        view_frame = QFrame()
        view_layout = QVBoxLayout()
        view_layout.addWidget(self.view)
        view_frame.setLayout(view_layout)

        self.component_menu = ComponentMenu(self, self.state_manager, model=self.model, on_edit=self.set_working, on_add=self.add_component_to_workspace, on_new=self.new_component)
        self.component_menu.setFixedWidth(200)
        self.model.window = self.component_menu
        self.main_splitter.addWidget(self.component_menu)
        self.main_splitter.addWidget(view_frame)
        self.main_splitter.addWidget(right_splitter)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.main_splitter)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.layout.addWidget(self.buttonbox)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.state_manager.subscribe_to_key(self.__class__.__name__, 'ui_refresh_signal', self.view.update_view)

        # Restore Geometry
        geometry = self.settings.component_controller.get_geometry(self.__class__.__name__)
        if geometry:
            self.restoreGeometry(geometry)
        state = self.settings.component_controller.get_state(self.__class__.__name__)
        if state:
            self.main_splitter.restoreState(state)

        self.view.update_view()

    def keyPressEvent(self, keypress) -> None:
        if keypress.key() == self.settings.get_editor_close_button():
            self.reject()
        elif keypress.key() == Qt.Key_Delete:
            self.delete_selected()
        else:
            pass

    def save(self):
        self.saved_data = DB.save()
        return self.saved_data

    def accept(self):
        self.save_geometry()
        super().accept()

    def reject(self):
        self.save_geometry()
        self.restore()
        super().reject()

    def closeEvent(self, a0) -> None:
        self.save_geometry()
        return super().closeEvent(a0)

    def restore(self):
        DB.restore(self.saved_data)

    def set_working(self, nid: NID):
        self.current = DB.custom_ui.get(nid)
        self.selected_component = None
        self.selected_component_offset = (0, 0)
        self.view.set_working_component(self.current)
        self.component_property_menu.set_selected(self.current)
        self.view.update_view()

    def add_component_to_workspace(self, nid: NID):
        if self.current:
            if DB.custom_ui.get(nid):
                copy = UIObjectPrefab.restore(DB.custom_ui.get(nid).save())
                new_component = (0, 0), copy
                self.current.subcomponents.append(new_component)
                self.view.update_view()

    def new_component(self):
        component = self.model.create_new()
        self.set_working(component)
        self.view.update_view()

    def deselect_component(self):
        self.selected_component = None
        self.view.set_selected_component(None)
        self.subcomponent_property_menu.set_selected(None)
        self.view.update_view()

    def select_component(self, x: int, y: int):
        if not self.current:
            self.selected_component = None
        elif self.current and self.current.subcomponents:
            clicked_selected = False
            for top_left, component in self.current.subcomponents:
                left, top = top_left
                right, bottom = tuple_add(top_left, component.size)
                if left < x and x < right:
                    if top < y and y < bottom:
                        if self.selected_component != component:
                            self.selected_component = component
                            self.selected_component_offset = x - left, y - top
                            self.view.set_selected_component(self.selected_component)
                            self.subcomponent_property_menu.set_selected(self.selected_component)
                            return
                        else:
                            self.selected_component_offset = x - left, y - top
                            clicked_selected = True
            # coudln't find anything
            if not clicked_selected:
                self.deselect_component()

    def move_component(self, x, y):
        if self.view.is_dragging:
            if x > -1 and y > -1:
                if self.selected_component:
                    component_idx = -1
                    for idx, pair in enumerate(self.current.subcomponents):
                        _, component = pair
                        if component == self.selected_component:
                            component_idx = idx
                            break
                    if component_idx != -1:
                        _, component = self.current.subcomponents.pop(component_idx)
                        new_pos = tuple_sub((x, y), self.selected_component_offset)
                        new_pair = new_pos, component
                        self.current.subcomponents.append(new_pair)
                    self.view.set_selected_component(self.selected_component)
                    self.view.update_view()

    def delete_selected(self):
        if self.selected_component:
            for idx, pair in enumerate(self.current.subcomponents):
                _, component = pair
                if component == self.selected_component:
                    self.current.subcomponents.pop(idx)
                    self.deselect_component()


    def save_geometry(self):
        self.settings.component_controller.set_geometry(self.__class__.__name__, self.saveGeometry())
        self.settings.component_controller.set_state(self.__class__.__name__, self.main_splitter.saveState())

# Run "python -m app.editor.ui_editor.ui_tab" from main directory
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    ui_editor = UIEditor(None)
    ui_editor.exec_()
