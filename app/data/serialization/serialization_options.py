from dataclasses import dataclass

@dataclass
class SerializeOptions():
    as_chunks: bool = False