import dataclasses

from model.color import Color
from model.shape import Shape


@dataclasses.dataclass(frozen=True, eq=True)
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


@dataclasses.dataclass(frozen=True, eq=True)
class Aspect:
    name: str
    text_color: Color
    shape_color: Color
    shape: Shape

    def to_dict(self):
        return {
            "name": self.name,
            "textColor": self.text_color.to_dict(),
            "shapeColor": self.shape_color.to_dict(),
            "shape": self.shape.value,
        }

    @staticmethod
    def from_dict(d: dict):
        return Aspect(
            name=d["name"],
            text_color=Color.from_dict(d["textColor"]),
            shape_color=Color.from_dict(d["shapeColor"]),
            shape=Shape(d["shape"]),
        )


@dataclasses.dataclass(frozen=True, eq=True)
class Position:
    x: float
    y: float

    def to_dict(self):
        return {"x": self.x, "y": self.y}

    @staticmethod
    def from_dict(d: dict):
        return Position(x=d["x"], y=d["y"])


@dataclasses.dataclass(frozen=True, eq=True)
class Entity(ExtractableElement):
    aspect: Aspect
    position: Position

    def to_dict(self):
        res = super().to_dict()
        res["aspect"] = self.aspect.to_dict()
        res["position"] = self.position.to_dict()
        return res

    @staticmethod
    def from_dict(d: dict):
        return Entity(
            name=d["name"],
            description=d["description"],
            aspect=Aspect.from_dict(d["aspect"]),
            position=Position.from_dict(d["position"]),
        )


@dataclasses.dataclass(frozen=True, eq=True)
class Relation(ExtractableElement):
    source: Entity
    target: Entity

    def to_dict(self):
        res = super().to_dict()
        res["source"] = self.source.to_dict()
        res["target"] = self.target.to_dict()
        return res

    @staticmethod
    def from_dict(d: dict):
        return Relation(
            name=d["name"],
            description=d["description"],
            source=Entity.from_dict(d["source"]),
            target=Entity.from_dict(d["target"]),
        )
