import dataclasses
from enum import Enum


@dataclasses.dataclass(frozen=True, eq=True)
class Color:
    r: int
    g: int
    b: int

    @property
    def rgb(self):
        return self.r, self.g, self.b

    @property
    def hex(self):
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}".upper()

    def to_dict(self):
        return {"r": self.r, "g": self.g, "b": self.b, "hex": self.hex}

    @staticmethod
    def from_dict(d: dict):
        return Color(r=d["r"], g=d["g"], b=d["b"])


class CommonColors(Enum):
    RED = Color(r=255, g=0, b=0)
    GREEN = Color(r=0, g=255, b=0)
    BLUE = Color(r=0, g=0, b=255)
    ORANGE = Color(r=255, g=165, b=0)
    YELLOW = Color(r=255, g=255, b=0)
    PURPLE = Color(r=128, g=0, b=128)
    CYAN = Color(r=0, g=255, b=255)
    MAGENTA = Color(r=255, g=0, b=255)
    BLACK = Color(r=0, g=0, b=0)
    WHITE = Color(r=255, g=255, b=255)
    GREY = Color(r=128, g=128, b=128)
