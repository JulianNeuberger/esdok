import dataclasses


@dataclasses.dataclass
class ExtractableElement:
    name: str
    description: str


@dataclasses.dataclass
class Aspect:
    name: str


@dataclasses.dataclass
class Entity(ExtractableElement):
    aspect: Aspect


@dataclasses.dataclass
class Relation(ExtractableElement):
    pass
