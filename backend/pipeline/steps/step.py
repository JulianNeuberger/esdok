import dataclasses
import random
import typing
import uuid
from abc import ABC

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import api_key
from model.application_model import ApplicationModel
import model.knowledge_graph as kg
from pipeline.llm_models import ModelInformation
from pipeline.steps.utils import ParsedFile


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
class EntityResult:
    id: str
    type: str
    name: str
    aspect: str
    document: str
    document_position: DocumentPosition

    def to_dict(self) -> typing.Dict[str, str]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "aspect": self.aspect,
            "document": self.document,
            "document_position": self.document_position.to_dict()
        }


@dataclasses.dataclass
class RelationResult:
    id: str
    source: str
    target: str
    name: str

    def to_dict(self) -> typing.Dict[str, str]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "name": self.name,
        }


class BasePipelineStep(ABC):

    def run(self, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def get_name() -> str:
        raise NotImplementedError()


class PromptCreation(BasePipelineStep):
    @staticmethod
    def parse_entity_extraction_result(
        result: str, type_aspect_mapping: typing.Dict[str, str]
    ) -> typing.List[EntityResult]:
        result_list = []
        lines = result.splitlines()

        for i, line in enumerate(lines):
            if "|" not in line:
                print(f"Skipping line '{line}', missing separator pipe!")
                continue
            line_values = line.split("|")
            if len(line_values) != 4:
                print(f"Skipping line '{line}', not enough values separated by pipe!")
                continue
            result_type, name, start_page, end_page = line_values
            result = EntityResult(
                id=f"n{i}",
                type=result_type,
                name=name,
                aspect=type_aspect_mapping[result_type],
                document='',
                document_position=DocumentPosition(start_page=start_page, end_page=end_page)
            )
            result_list.append(result)

        return result_list

    @staticmethod
    def parse_relation_extraction_result(result: str) -> typing.List[RelationResult]:
        result_list = []
        lines = result.splitlines()

        for i, line in enumerate(lines):
            if "|" not in line:
                print(f"Skipping line '{line}', missing separator pipe")
                continue

            line_values = line.split("|")
            if len(line_values) != 3:
                print(f"Skipping line '{line}', not enough values")
                continue

            name, source, target = line_values
            result = RelationResult(id=f"e{i}", source=source, target=target, name=name)
            result_list.append(result)

        return result_list

    @staticmethod
    def extract_entities_from_file(
        model: ModelInformation,
        entity_descriptions: str,
        type_aspect_mapping: typing.Dict[str, str],
        parsed_file: ParsedFile,
    ) -> typing.List[EntityResult]:
        model = ChatOpenAI(model=model.model_name)

        with open(
            "prompts/system_template_entity_extraction.txt", "r", encoding="utf8"
        ) as f:
            system_template = f.read()

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_template), ("user", "{text}")]
        )

        parser = StrOutputParser()

        chain = prompt_template | model | parser

        return PromptCreation.parse_entity_extraction_result(
            chain.invoke(
                {
                    "entity_descriptions_application_model": entity_descriptions,
                    "text": parsed_file,
                }
            ),
            type_aspect_mapping=type_aspect_mapping,
        )

    @staticmethod
    def extract_relations_from_file(
        model: ModelInformation,
        relation_descriptions: str,
        entities_to_use: typing.List[EntityResult],
        parsed_file: ParsedFile,
    ):
        model = ChatOpenAI(model=model.model_name)

        with open(
            "prompts/system_template_relation_extraction.txt", "r", encoding="utf8"
        ) as f:
            system_template = f.read()

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_template), ("user", "{text}")]
        )

        formatted_entities_to_use = ""
        for entity in entities_to_use:
            formatted_entities_to_use = (
                formatted_entities_to_use
                + f"({entity.id}, {entity.type}, {entity.name})\n"
            )

        parser = StrOutputParser()

        chain = prompt_template | model | parser

        return PromptCreation.parse_relation_extraction_result(
            chain.invoke(
                {
                    "relation_descriptions_application_model": relation_descriptions,
                    "entities_to_use": formatted_entities_to_use,
                    "text": parsed_file,
                }
            )
        )

    def run(
        self,
        model: ModelInformation,
        application_model: ApplicationModel,
        parsed_file: ParsedFile,
    ) -> kg.Graph:
        api_key.set_llm_api_key(model=model.model_name)
        extracted_entities = self.extract_entities_from_file(
            model=model,
            entity_descriptions=application_model.get_entity_descriptions(),
            type_aspect_mapping=application_model.get_type_aspect_mapping(),
            parsed_file=parsed_file,
        )

        extracted_relations = self.extract_relations_from_file(
            model=model,
            relation_descriptions=application_model.get_relation_descriptions(),
            entities_to_use=extracted_entities,
            parsed_file=parsed_file,
        )

        aspects: typing.Dict[str, kg.Aspect] = {}

        nodes: typing.Dict[str, kg.Node] = {}
        for e in extracted_entities:
            if e.aspect not in aspects.keys():
                # TODO: how to load this? from application model?
                aspects[e.aspect] = kg.Aspect(
                    name=e.aspect, shape="rect", color="default"
                )

            nodes[e.id] = kg.Node(
                id=str(uuid.uuid4()),
                name=e.name,
                type=e.type,
                position=(random.random() * 500, random.random() * 500),
                document_position=(e.document_position.start_page, e.document_position.end_page),
                aspect=aspects[e.aspect],
            )

        edges: typing.List[kg.Edge] = []
        if len(extracted_relations) > 0:
            for r in extracted_relations:
                edges.append(
                    kg.Edge(
                        id=str(uuid.uuid4()),
                        type=r.name,
                        source=nodes[r.source],
                        target=nodes[r.target],
                    )
                )

        graph = kg.Graph(
            nodes=list(nodes.values()),
            edges=edges,
        )

        return graph

    @staticmethod
    def get_name() -> str:
        return "PromptCreation"
