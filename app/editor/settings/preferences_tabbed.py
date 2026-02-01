from PyQt5 import QtGui
from PyQt5.QtWidgets import (QVBoxLayout, QApplication, QTabWidget,
                              QWidget, QScrollArea)

from app import dark_theme
from app.editor.settings import preference_definitions
from app.editor.settings.preference_definitions import Preference, PreferenceCategory, PreferenceType
from app.extensions.custom_gui import Dialog
from app.editor.settings import MainSettingsController
from app.editor import timer
from app.editor.settings.preference_components import (
    BooleanPreference, DoublePreference, ChoicePreference,
    FontPreference, KeybindingPreference, MousebindingPreference, PreferenceSection, PreferenceWidget
)

class TabbedPreferencesDialog(Dialog):
    """
    A tabbed preferences dialog that organizes settings into logical categories.
    Uses reusable preference components for consistency and maintainability.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.setWindowTitle("Preferences")

        # Main layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Settings controller
        self.settings = MainSettingsController()

        # Create tab widget
        self.tab_widget = QTabWidget(self)
        # Store references to keybinding widgets for event handling
        self._keybinding_widgets = []

        # Create tabs
        self._preference_widgets: dict[Preference, PreferenceWidget] = {}
        self._create_tabs()
        self._add_handlers()

        # Add tab widget and buttons to layout
        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.buttonbox)

        # default size
        self.resize(600, 500)

    def _create_scrollable_tab(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        """Create a scrollable tab container."""
        # Create main widget for the tab
        tab = QWidget()

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # Create content widget
        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content.setLayout(content_layout)

        # Set content in scroll area
        scroll.setWidget(content)

        # Create tab layout
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)

        # Add tab to tab widget
        self.tab_widget.addTab(tab, title)

        return tab, content_layout

    def _create_tabs(self):
        """Create all tabs."""
        for category in PreferenceCategory:
            tab, layout = self._create_scrollable_tab(category.value)
            sections = Preference.get_sections_for_category(category)
            for section in sections:
                pref_section = PreferenceSection(section)
                section_preferences = Preference.get_by_section(category, section)
                for pref in section_preferences:
                    widget = self._create_preference_widget(pref)
                    self._preference_widgets[pref] = widget
                    pref_section.add_preference(widget)
                layout.addWidget(pref_section)
                layout.addStretch()

    def _add_handlers(self):
        """Adds special handling to certain preferences that require it."""
        self._preference_widgets[Preference.PLACE_BUTTON].valueChanged.connect(self._on_place_changed)
        self._preference_widgets[Preference.SELECT_BUTTON].valueChanged.connect(self._on_select_changed)
        self._preference_widgets[Preference.AUTOSAVE_TIME].valueChanged.connect(self._on_autosave_changed)
        self._preference_widgets[Preference.THEME].valueChanged.connect(self._on_theme_changed)

    def _create_preference_widget(self, pref: Preference) -> PreferenceWidget:
        """Create the appropriate widget for a given preference."""
        definition = pref.definition

        if definition.pref_type == PreferenceType.BOOLEAN:
            widget = BooleanPreference(definition.label, tooltip=definition.tooltip)
        elif definition.pref_type == PreferenceType.CHOICE:
            widget = ChoicePreference(definition.label, options=definition.options, tooltip=definition.tooltip)
        elif definition.pref_type == PreferenceType.DOUBLE:
            widget = DoublePreference(definition.label, min_val=definition.min_val,
                                      max_val=definition.max_val, decimals=definition.decimals,
                                      tooltip=definition.tooltip)
        elif definition.pref_type == PreferenceType.FONT:
            widget = FontPreference(definition.label, monospace_only=definition.monospace_only,
                                    tooltip=definition.tooltip)
        elif definition.pref_type == PreferenceType.KEYBINDING:
            widget = KeybindingPreference(definition.label, tooltip=definition.tooltip)
            self._keybinding_widgets.append(widget)
        elif definition.pref_type == PreferenceType.MOUSEBINDING:
            widget = MousebindingPreference(definition.label, tooltip=definition.tooltip)
        else:
            raise ValueError(f"Unsupported preference type: {definition.pref_type}")

        value = self.settings.get_preference(pref)
        # Apply UI conversions based on preference
        if definition.pref_type == PreferenceType.MOUSEBINDING:
            value = preference_definitions.button_to_name.get(value, definition.default_value)
        elif pref == Preference.THEME:
            value = dark_theme.ThemeType(int(value)).name
        widget.set_value(value)
        return widget

    # Event handlers
    def _on_select_changed(self, value):
        """Handle select button change - ensure it differs from place button."""
        if value == self._preference_widgets[Preference.PLACE_BUTTON].get_value():
            # Swap the place button to the other option
            other = 'R-click' if value == 'L-click' else 'L-click'
            self._preference_widgets[Preference.PLACE_BUTTON].set_value(other)

    def _on_place_changed(self, value):
        """Handle place button change - ensure it differs from select button."""
        if value == self._preference_widgets[Preference.SELECT_BUTTON].get_value():
            # Swap the select button to the other option
            other = 'R-click' if value == 'L-click' else 'L-click'
            self._preference_widgets[Preference.SELECT_BUTTON].set_value(other)

    def _on_theme_changed(self, value):
        """Handle theme change - apply immediately."""
        ap = QApplication.instance()
        theme_type = dark_theme.ThemeType[value]
        dark_theme.set(ap, theme_type)
        self.window.set_icons(theme_type)

    def _on_autosave_changed(self, value):
        """Handle autosave time change - apply immediately."""
        t = timer.get_timer()
        t.autosave_timer.stop()
        t.autosave_timer.setInterval(int(value * 60 * 1000))
        t.autosave_timer.start()

    def keyPressEvent(self, keypress: QtGui.QKeyEvent) -> None:
        """Handle key press events, routing to keybinding widgets if needed."""
        # Check if any keybinding widget is awaiting input
        for kb_widget in self._keybinding_widgets:
            if kb_widget.is_awaiting_key():
                kb_widget.keyPressEvent(keypress)
                return
        # Otherwise, use default behavior
        super().keyPressEvent(keypress)

    def accept(self):
        """Save all settings when OK is clicked."""
        for pref, widget in self._preference_widgets.items():
            value = widget.get_value()
            defn = pref.definition
            if defn.pref_type == PreferenceType.MOUSEBINDING:
                storage_value = preference_definitions.name_to_button[value]
            elif pref == Preference.THEME:
                theme_type = dark_theme.ThemeType[value]
                storage_value = theme_type.value
            elif defn.pref_type == PreferenceType.BOOLEAN:
                # Convert bool to int (Qt settings quirk)
                storage_value = 1 if value else 0
            else:
                storage_value = value
            self.settings.set_preference(pref, storage_value)
        super().accept()
