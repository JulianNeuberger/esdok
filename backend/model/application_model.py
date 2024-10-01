import dataclasses
import typing

from model.meta_model import Entity, Aspect, Relation


@dataclasses.dataclass
class ApplicationModel:
    entities: typing.List[Entity]
    relations: typing.List[Relation]

    def get_entity_descriptions(self) -> str:
        description = ''
        for entity in self.entities:
            description = description + f'{entity.name}: {entity.description}\n'
        return description

    def get_relation_descriptions(self) -> str:
        description = ''
        for relation in self.relations:
            description = description + f'{relation.name}: {relation.description}\n'
        return description

    def get_type_aspect_mapping(self) -> typing.Dict[str, str]:
        return {e.name: e.aspect.name for e in self.entities}

    def to_dict(self) -> dict:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "relations": [r.to_dict() for r in self.relations],
        }


def get_dummy_application_model() -> ApplicationModel:
    return ApplicationModel(
        entities=create_dummy_entities(),
        relations=create_dummy_relations()
    )


def create_dummy_entities() -> typing.List[Entity]:
    tool = Entity(name='Tool',
                  description='A tool is a thing that is used or required to perform a given task.',
                  aspect=Aspect(name='operational'))

    actor = Entity(name='Actor',
                   description='An actor is a human, a group, a system or a machine that is able to perform a task.',
                   aspect=Aspect(name='organizational'))

    task = Entity(name='Task',
                  description='A task is a specific piece of work or activity that needs to be done by an actor.',
                  aspect=Aspect(name='control-flow'))

    return [task, tool, actor]


def create_dummy_relations() -> typing.List[Relation]:
    task_require_tool = Relation(name='task_requires_tool',
                                 description='A task_require_tool relation indicates that a specific task cannot be '
                                             'completed without the use of a particular tool. This relation defines '
                                             'the dependency between the task and the tool required to perform it.')
    actor_performs_task = Relation(name='actor_performs_task',
                                   description='The actor_performs_task relation specifies that an actor (a person, '
                                               'group, or system) is responsible for carrying out or executing a '
                                               'particular task. This relation identifies who is performing the task.')

    return [task_require_tool, actor_performs_task]
