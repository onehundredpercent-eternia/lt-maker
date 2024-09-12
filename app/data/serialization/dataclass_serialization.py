from dataclasses import fields, is_dataclass
from typing import get_origin

def dataclass_from_dict(klass, d):
    if d == None:
        return d
    if(get_origin(klass) == dict):
        return {k:dataclass_from_dict(klass.__args__[1],d[k]) for k in d}
    if(get_origin(klass) == list):
        return [dataclass_from_dict(klass.__args__[0],x) for x in d]
    if(get_origin(klass) == tuple):
        return tuple([dataclass_from_dict(klass.__args__[i],d[i]) for i in range(len(klass.__args__))])
    if(is_dataclass(klass)):
        fieldtypes = {f.name:f.type for f in fields(klass)}
        return klass(**{f:dataclass_from_dict(fieldtypes[f],d[f]) for f in d if f in fieldtypes})
    else:
        return d # Not a dataclass field