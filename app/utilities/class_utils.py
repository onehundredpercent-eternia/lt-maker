def recursive_subclasses(ctype: type):
    all_subclasses = []
    subclasses = ctype.__subclasses__()
    for subclass in subclasses:
        all_subclasses += recursive_subclasses(subclass)
    all_subclasses += subclasses
    return all_subclasses

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
