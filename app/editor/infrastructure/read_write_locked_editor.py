import sys
from typing import Optional
from PyQt5.QtWidgets import QApplication, QWidget

class ReadWriteLockedEditor(QWidget):
    def __init__(self, name) -> None:
        super().__init__()
        self.name = name

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w1 = ReadWriteLockedEditor('w1')
    w2 = ReadWriteLockedEditor('w2')
    w1.show()
    w2.show()
    sys.exit(app.exec_())
