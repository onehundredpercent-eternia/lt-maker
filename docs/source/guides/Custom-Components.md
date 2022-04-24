# Custom Components

_last updated 2022-04-10_

## Distribution

If you've developed your own custom components, those custom components will be necessary to run your game/project. However, up until now your only option to distribute these custom components was:

1. Petition rainlash to add your custom components to the master branch of the engine, so that others using your custom components would have access to them.
2. Distribute your own bespoke version of the engine to your players that includes the custom components.

Well, now there's a third option. **Project Specific Custom Components**

### How do?

```
Make sure you do this section EXACTLY. Importing python modules at runtime is a fickle thing, so precision is important.
```

In your project's *resources* directory, create a new directory called `custom_components`. Within that directory, create a file called `__init__.py`. 

Place this code into the `__init__.py` file:

```python
import os
import importlib

for module_name in os.listdir(os.path.dirname(__file__)):
    if module_name == '__init__.py' or module_name[-3:] != '.py':
        continue
    print("Importing Custom Components in %s..." % module_name)
    module = importlib.import_module('custom_components.' + module_name[:-3])
    importlib.reload(module)
del module_name
```

Once that's done, you can add the files that contain your custom components to the `custom_components` directory.

So, to confirm, your directory structure now looks like this:

```
project.ltproj/
    resources/
        custom_components/
            __init__.py
            my_components1.py
            my_components2.py
            my_components_etc_and_so_on.py
```

These will be loaded at runtime when you start the editor or the engine and load up your project.

So players of your game can use the canonical Lex Talionis engine with your .ltproj project and its bespoke custom components without any friction.
