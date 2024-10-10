import dataclasses

from model.color import Color
from model.shape import Shape


@dataclasses.dataclass
class ExtractableElement:
    name: str
    description: str

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
        }

    @staticmethod
    def from_dict(d: dict):
        return ExtractableElement(
            name=d["name"],
            description=d["description"],
        )


@dataclasses.dataclass
class Aspect:
    name: str
    text_color: Color
    shape_color: Color
    shape: Shape

    def to_dict(self):
        return {
            "name": self.name,
            "text_color": self.text_color.to_dict(),
            "shape_color": self.shape_color.to_dict(),
            "shape": self.shape.value
        }

    @staticmethod
    def from_dict(d: dict):
        return Aspect(
            name=d["name"],
            text_color=Color.from_dict(d["text_color"]),
            shape_color=Color.from_dict(d["shape_color"]),
            shape=d["shape"]
        )


@dataclasses.dataclass
class Position:
    x: float
    y: float

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }

    @staticmethod
    def from_dict(d: dict):
        return Position(x=d["x"],
                        y=d["y"]
                        )


@dataclasses.dataclass
class Entity(ExtractableElement):
    aspect: Aspect
    position: Position

    def to_dict(self):
        res = super().to_dict()
        res['aspect'] = self.aspect.to_dict()
        res['position'] = self.position.to_dict()
        return res

    @staticmethod
    def from_dict(d: dict):
        return Entity(
            name=d["name"],
            description=d["description"],
            aspect=Aspect.from_dict(d["aspect"]),
            position=Position.from_dict(d["position"])
        )


@dataclasses.dataclass
class Relation(ExtractableElement):
    start: Entity
    end: Entity

    def to_dict(self):
        res = super().to_dict()
        res['start'] = self.start.to_dict()
        res['end'] = self.end.to_dict()
        return res

    @staticmethod
    def from_dict(d: dict):
        return Relation(
            name=d["name"],
            description=d["description"],
            start=d["start"],
            end=d["end"]
        )
