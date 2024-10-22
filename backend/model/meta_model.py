import dataclasses

from model.color import Color
from model.shape import Shape


@dataclasses.dataclass
class DocumentPosition:
    start_page: int
    end_page: int

    def to_dict(self):
        return {
            "start_page": self.start_page,
            "end_page": self.end_page
        }

    @staticmethod
    def from_dict(d: dict):
        return DocumentPosition(start_page=d["start_page"],
                                end_page=d["end_page"])


@dataclasses.dataclass
class ExtractableElement:
    name: str
    description: str
    document: str
    reference: DocumentPosition

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "document": self.document,
            "reference": self.reference.to_dict()
        }

    @staticmethod
    def from_dict(d: dict):
        return ExtractableElement(
            name=d["name"],
            description=d["description"],
            document=d["document"],
            reference=DocumentPosition.from_dict(d["reference"])
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


@dataclasses.dataclass
class Position:
    x: float
    y: float

    def to_dict(self):
        return {"x": self.x, "y": self.y}

    @staticmethod
    def from_dict(d: dict):
        return Position(x=d["x"], y=d["y"])


@dataclasses.dataclass
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
            document=d["document"],
            reference=DocumentPosition.from_dict(d["reference"]),
            description=d["description"],
            aspect=Aspect.from_dict(d["aspect"]),
            position=Position.from_dict(d["position"]),
        )


@dataclasses.dataclass
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
            document=d["document"],
            reference=DocumentPosition.from_dict(d["reference"]),
            description=d["description"],
            source=Entity.from_dict(d["source"]),
            target=Entity.from_dict(d["target"]),
        )
