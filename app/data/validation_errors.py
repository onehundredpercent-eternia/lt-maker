from dataclasses import dataclass


from dataclasses import dataclass

@dataclass
class ValidationError():
    category: str
    owner: str
    where: str
    reason: str

    def __str__(self) -> str:
        return ("Error in %s:%s:%s - %s" % (self.category, self.owner, self.where, self.reason))

class InvalidValueError(ValidationError):
    def __init__(self, category, owner, field, invalid_val) -> None:
        msg = "Invalid [%s]: '%s'" % (field, invalid_val if (invalid_val is not None) else "None")
        return super(InvalidValueError).__init__(category, owner, field, msg)