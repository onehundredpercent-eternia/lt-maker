from PyQt5.QtCore import QSettings

class SessionSettingsController():
    """
    Provides an interface for interacting with session variables that are reset on launch
    """

    def __init__(self, company='rainlash', product='Lex Talionis'):
        QSettings.setDefaultFormat(QSettings.IniFormat)
        self.state = QSettings(company, product)

    def reset(self):
        self.set_show_validation_error_on_save()

    def set_show_validation_error_on_save(self, value=1):
        self.state.setValue("show_validation_error_on_save", value)

    def should_show_validation_error_on_save(self):
        return self.state.value("show_validation_error_on_save", 1)