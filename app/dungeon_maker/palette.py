import json

# Floor types:
# default
# grass
# ruins
# checkerboard

class Palette:
    def __init__(self):
        self.floor1: str = "default"
        self.floor2: str = "default"
        self.water: bool = False
        self.location: str = None

    @classmethod
    def from_json(cls, fn: str) -> "Palette":
        with open(fn) as fp:
            data = json.load(fp)
        self = cls()
        self.floor1 = data['floor1']
        self.floor2 = data['floor2']
        self.location = data.get('location', None)
        self.water = data.get('water', False)
        return self
