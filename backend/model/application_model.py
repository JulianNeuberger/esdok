import dataclasses
import json
import typing
import random
from pathlib import Path

from model.color import CommonColors
from model.meta_model import Entity, Aspect, Relation, Position
from model.shape import Shape


@dataclasses.dataclass
class ApplicationModel:
    entities: typing.List[Entity]
    relations: typing.List[Relation]

    def get_entity_descriptions(self) -> str:
        description = ""
        for entity in self.entities:
            description = description + f"{entity.name}: {entity.description}\n"
        return description

    def get_relation_descriptions(self) -> str:
        description = ""
        for relation in self.relations:
            description = description + f"{relation.name}: {relation.description}\n"
        return description

    def get_entity_by_name(self, name: str) -> Entity:
        for entity in self.entities:
            if entity.name == name:
                return entity
        raise ValueError(f"Entity with name {name} not part of application model.")

    def get_type_aspect_mapping(self) -> typing.Dict[str, str]:
        return {e.name: e.aspect.name for e in self.entities}

    def to_dict(self) -> dict:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "relations": [r.to_dict() for r in self.relations],
        }

    @staticmethod
    def from_dict(data: dict) -> "ApplicationModel":
        return ApplicationModel(
            entities=[Entity.from_dict(e) for e in data["entities"]],
            relations=[Relation.from_dict(r) for r in data["relations"]],
        )

    def save(self, file_path: typing.Union[str, Path]) -> None:
        with open(file_path, "w") as file:
            json.dump(self.to_dict(), file)

    @staticmethod
    def load(file_path: typing.Union[str, Path]) -> "ApplicationModel":
        with open(file_path, "r") as file:
            return ApplicationModel.from_dict(json.load(file))


def get_dummy_application_model() -> ApplicationModel:
    return ApplicationModel(
        entities=create_dummy_entities(), relations=create_dummy_relations()
    )


def get_random_position(
    x_lower: float = 0.0,
    x_upper: float = 10.0,
    y_lower: float = 0.0,
    y_upper: float = 10.0,
) -> Position:
    return Position(
        x=random.uniform(x_lower, x_upper), y=random.uniform(y_lower, y_upper)
    )


TOOL = Entity(
    name="Tool",
    description="A tool is a thing that is used or required to perform a given task.",
    aspect=Aspect(
        name="operational",
        text_color=CommonColors.BLACK.value,
        shape_color=CommonColors.GREEN.value,
        shape=Shape.PARALLELOGRAM,
    ),
    position=get_random_position(0, 10, 0, 10),
)

ACTOR = Entity(
    name="Actor",
    description="An actor is a human, a group, a system or a machine that is able to perform a task.",
    aspect=Aspect(
        name="organizational",
        text_color=CommonColors.BLACK.value,
        shape_color=CommonColors.RED.value,
        shape=Shape.RECTANGLE,
    ),
    position=get_random_position(0, 10, 0, 10),
)

TASK = Entity(
    name="Task",
    description="A task is a specific piece of work or activity that needs to be done by an actor.",
    aspect=Aspect(
        name="control-flow",
        text_color=CommonColors.BLACK.value,
        shape_color=CommonColors.MAGENTA.value,
        shape=Shape.ROUND_RECTANGLE,
    ),
    position=get_random_position(0, 10, 0, 10),
)


def create_dummy_entities() -> typing.List[Entity]:
    return [TASK, TOOL, ACTOR]


def create_dummy_relations() -> typing.List[Relation]:
    task_require_tool = Relation(
        name="task_requires_tool",
        description="A task_require_tool relation indicates that a specific task cannot be "
        "completed without the use of a particular tool. This relation defines "
        "the dependency between the task and the tool required to perform it.",
        source=TASK,
        target=TOOL,
    )
    actor_performs_task = Relation(
        name="actor_performs_task",
        description="The actor_performs_task relation specifies that an actor (a person, "
        "group, or system) is responsible for carrying out or executing a "
        "particular task. This relation identifies who is performing the task.",
        source=ACTOR,
        target=TASK,
    )

    return [task_require_tool, actor_performs_task]
