import dataclasses


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

    def to_dict(self):
        return {
            "name": self.name,
        }

    @staticmethod
    def from_dict(d: dict):
        return Aspect(
            name=d["name"],
        )


@dataclasses.dataclass
class Entity(ExtractableElement):
    aspect: Aspect

    def to_dict(self):
        res = super().to_dict()
        res['aspect'] = self.aspect.to_dict()
        return res

    @staticmethod
    def from_dict(d: dict):
        return Entity(
            name=d["name"],
            description=d["description"],
            aspect=Aspect.from_dict(d["aspect"])
        )


@dataclasses.dataclass
class Relation(ExtractableElement):
    @staticmethod
    def from_dict(d: dict):
        return Relation(
            name=d["name"],
            description=d["description"],
        )
