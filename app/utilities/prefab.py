from dataclasses import asdict, dataclass

from app.data.serialization.dataclass_serialization import dataclass_from_dict

class PrefabMeta(type):
    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)
        new_cls.save = lambda self: asdict(self)
        new_cls.restore = classmethod(lambda cls, s_dict: dataclass_from_dict(cls, s_dict))
        return dataclass()(new_cls)

class Prefab(metaclass=PrefabMeta):
    def save(self) -> dict:
        raise NotImplementedError

    @classmethod
    def restore(cls, s_dict: dict):
        raise NotImplementedError