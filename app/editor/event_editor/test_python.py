# editor.py

from PyQt5 import QtGui, QtWidgets
from app.extensions.py_syntax import PythonHighlighter

app = QtWidgets.QApplication([])
editor = QtWidgets.QPlainTextEdit()
highlight = PythonHighlighter(editor.document())
editor.show()

# Load syntax.py into the editor for demo purposes
infile = open('app/extensions/py_syntax.py', 'r')
editor.setPlainText(infile.read())

app.exec_()