import dataclasses
from dataclasses import field
from enum import Enum


@dataclasses.dataclass
class Color:
    _r: int = field(init=False, repr=False)
    _g: int = field(init=False, repr=False)
    _b: int = field(init=False, repr=False)
    _hex_value: str = field(init=False, repr=False)

    r: int
    g: int
    b: int

    def __post_init__(self):
        self.rgb = (self.r, self.g, self.b)

    @property
    def rgb(self):
        return self._r, self._g, self._b

    @rgb.setter
    def rgb(self, values):
        self._r, self._g, self._b = values
        self._hex_value = self._rgb_to_hex(self._r, self._g, self._b)

    @property
    def hex(self):
        return self._hex_value

    @hex.setter
    def hex(self, value):
        self._hex_value = value
        self._r, self._g, self._b = self._hex_to_rgb(self._hex_value)

    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        return f"#{r:02x}{g:02x}{b:02x}".upper()

    def _hex_to_rgb(self, hex_value: str):
        hex_value = hex_value.lstrip("#")
        return tuple(int(hex_value[i : i + 2], 16) for i in (0, 2, 4))

    def to_dict(self):
        return {"r": self._r, "g": self._g, "b": self._b, "hex": self._hex_value}

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
