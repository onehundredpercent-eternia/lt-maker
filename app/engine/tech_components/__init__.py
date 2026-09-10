import os
import importlib

for module in os.listdir(os.path.dirname(__file__)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    print("Importing Tech Components in %s..." % module)
    importlib.import_module('app.engine.tech_components.' + module[:-3])
del module
