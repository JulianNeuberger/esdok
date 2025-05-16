import dataclasses
from datetime import datetime
import pathlib
import typing
import uuid
from abc import ABC

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import model.knowledge_graph as kg
from model import meta_model
from model.application_model import ApplicationModel
from pipeline.llm_models import ModelInformation
from pipeline.steps.utils import ParsedFile


@dataclasses.dataclass
class DocumentPosition:
    start_page: int
    end_page: int

    def to_dict(self):
        return {"start_page": self.start_page, "end_page": self.end_page}

    @staticmethod
    def from_dict(d: dict):
        return DocumentPosition(start_page=d["start_page"], end_page=d["end_page"])


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
            "document_position": self.document_position.to_dict(),
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
    def parse_nodes(
        result: str,
        entities: typing.Dict[str, meta_model.Entity],
        file: str,
        first_id: int,
    ) -> typing.List[kg.Node]:
        result_list = []
        lines = result.splitlines()

        for i, line in enumerate(lines):
            if "|" not in line:
                print(f"Skipping line '{line}', missing separator pipe!")
                continue
            line_values = line.split("|")
            if len(line_values) != 3:
                print(f"Skipping line '{line}', not enough values separated by pipe!")
                continue
            result_type, name, page = line_values
            if result_type not in entities.keys():
                print(
                    f"Skipping entity of type {result_type}, not a valid entity type."
                )
                continue
            entity = entities[result_type]
            node = kg.Node(
                id=str(first_id + i),
                name=name,
                entity=entity,
                position=(0, 0),
                source=kg.DataSource(
                    file=file,
                    page_start=page,
                    page_end=page,
                ),
            )
            result_list.append(node)

        return result_list

    @staticmethod
    def parse_entity_resolution(
        original_nodes: typing.List[kg.Node], result: str
    ) -> typing.List[typing.List[kg.Node]]:
        nodes_by_id = {n.id: n for n in original_nodes}
        entity_clusters: typing.List[typing.List[kg.Node]] = []
        for line in result.splitlines():
            ids = line.split("|")
            entity_nodes: typing.List[kg.Node] = []
            for raw_id in ids:
                try:
                    node = nodes_by_id[raw_id]
                    entity_nodes.append(node)
                    del nodes_by_id[raw_id]
                except KeyError:
                    print(
                        f"Skipping id '{raw_id}', is not an id of any of the known nodes!"
                    )
            entity_clusters.append(entity_nodes)
        for remaining_node in nodes_by_id.values():
            entity_clusters.append([remaining_node])
        return entity_clusters

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
        entities: typing.Dict[str, meta_model.Entity],
        parsed_file: ParsedFile,
        first_id: int,
    ) -> typing.List[kg.Node]:
        model = ChatOpenAI(model=model.model_name)

        prompt_path = (
            pathlib.Path(__file__).parent.parent.parent.absolute()
            / "res"
            / "prompts"
            / "system_template_entity_extraction.txt"
        )

        with open(prompt_path, "r", encoding="utf8") as f:
            system_template = f.read()

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_template), ("user", "{text}")]
        )

        date_formatted = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        entity_descriptions = "\n".join(
            f"- *{e.name}*: {e.description}" for e in entities.values()
        )

        prompts_dir = (
            pathlib.Path(__file__).parent.parent.parent.absolute() / "res" / "requests" / "mentions"
        )
        prompts_dir.mkdir(exist_ok=True, parents=True)
        prompt = prompt_template.invoke(
            {
                "entity_descriptions_application_model": entity_descriptions,
                "text": parsed_file.content,
            }
        )

        with open(prompts_dir / f"{date_formatted}.txt", "w", encoding="utf8") as f:
            for message in prompt.to_messages():
                f.write("-" * 150)
                f.write("\n")
                f.write(f"{message.type}:\n")
                f.write("-" * 150)
                f.write("\n")
                f.write(message.content)
                f.write("\n")
                f.write("-" * 150)
                f.write("\n")
                f.write("\n")

        parser = StrOutputParser()

        chain = prompt_template | model | parser
        chat_result = chain.invoke(
            {
                "entity_descriptions_application_model": entity_descriptions,
                "text": parsed_file.content,
            }
        )

        answers_dir = (
            pathlib.Path(__file__).parent.parent.parent.absolute() / "res" / "answers" / "mentions"
        )
        answers_dir.mkdir(exist_ok=True)

        with open(answers_dir / f"{date_formatted}.txt", "w", encoding="utf8") as f:
            f.write(chat_result)

        return PromptCreation.parse_nodes(
            chat_result, entities, file=parsed_file.name, first_id=first_id
        )

    @staticmethod
    def resolve_entities_from_file(
        model: ModelInformation, entities: typing.List[kg.Node], parsed_file: ParsedFile
    ) -> typing.List[typing.List[kg.Node]]:
        model = ChatOpenAI(model=model.model_name)

        prompt_path = (
            pathlib.Path(__file__).parent.parent.parent.absolute()
            / "res"
            / "prompts"
            / "system_template_entity_resolution.txt"
        )

        with open(prompt_path, "r", encoding="utf8") as f:
            system_template = f.read()

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_template), ("user", "{text}")]
        )

        date_formatted = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        prompts_dir = (
            pathlib.Path(__file__).parent.parent.parent.absolute() / "res" / "requests" / "entities"
        )
        prompts_dir.mkdir(exist_ok=True, parents=True)

        formatted_entities = "\n".join(
            [f"{e.id}|{e.entity.name}|{e.name}" for e in entities]
        )

        prompt = prompt_template.invoke(
            {
                "entity_list": formatted_entities,
                "text": parsed_file.content,
            }
        )

        with open(prompts_dir / f"{date_formatted}.txt", "w", encoding="utf8") as f:
            for message in prompt.to_messages():
                f.write("-" * 150)
                f.write("\n")
                f.write(f"{message.type}:\n")
                f.write("-" * 150)
                f.write("\n")
                f.write(message.content)
                f.write("\n")
                f.write("-" * 150)
                f.write("\n")
                f.write("\n")

        parser = StrOutputParser()

        chain = prompt_template | model | parser

        chat_result = chain.invoke(
            {
                "entity_list": formatted_entities,
                "text": parsed_file.content,
            }
        )

        answers_dir = (
            pathlib.Path(__file__).parent.parent.parent.absolute() / "res" / "answers" / "entities"
        )
        answers_dir.mkdir(exist_ok=True)

        with open(answers_dir / f"{date_formatted}.txt", "w", encoding="utf8") as f:
            f.write(chat_result)

        return PromptCreation.parse_entity_resolution(entities, chat_result)

    @staticmethod
    def extract_relations_from_file(
        model: ModelInformation,
        relation_descriptions: str,
        entities: typing.List[kg.Node],
        parsed_file: ParsedFile,
    ):
        model = ChatOpenAI(model=model.model_name)

        prompt_path = (
            pathlib.Path(__file__).parent.parent.parent.absolute()
            / "res"
            / "prompts"
            / "system_template_relation_extraction.txt"
        )

        with open(prompt_path, "r", encoding="utf8") as f:
            system_template = f.read()

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_template), ("user", "{text}")]
        )

        date_formatted = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        formatted_entities = "\n".join(
            [f"{e.id}|{e.entity.name}|{e.name}" for e in entities]
        )

        prompts_dir = (
            pathlib.Path(__file__).parent.parent.parent.absolute() / "res" / "requests" / "relations"
        )
        prompts_dir.mkdir(exist_ok=True, parents=True)
        prompt = prompt_template.invoke(
            {
                "relation_descriptions_application_model": relation_descriptions,
                "entities_to_use": formatted_entities,
                "text": parsed_file.content,
            }
        )

        with open(prompts_dir / f"{date_formatted}.txt", "w", encoding="utf8") as f:
            for message in prompt.to_messages():
                f.write("-" * 150)
                f.write("\n")
                f.write(f"{message.type}:\n")
                f.write("-" * 150)
                f.write("\n")
                f.write(message.content)
                f.write("\n")
                f.write("-" * 150)
                f.write("\n")
                f.write("\n")

        parser = StrOutputParser()

        chain = prompt_template | model | parser

        chat_result = chain.invoke(
            {
                "relation_descriptions_application_model": relation_descriptions,
                "entities_to_use": formatted_entities,
                "text": parsed_file.content,
            }
        )

        answers_dir = (
            pathlib.Path(__file__).parent.parent.parent.absolute() / "res" / "answers" / "relations"
        )
        answers_dir.mkdir(exist_ok=True)

        with open(answers_dir / f"{date_formatted}.txt", "w", encoding="utf8") as f:
            f.write(chat_result)

        return PromptCreation.parse_relation_extraction_result(chat_result)

    def run(
        self,
        model: ModelInformation,
        application_model: ApplicationModel,
        current_graph: kg.Graph | None,
        parsed_file: ParsedFile,
    ) -> kg.Graph:
        extracted_nodes = self.extract_entities_from_file(
            model=model,
            parsed_file=parsed_file,
            entities={e.name: e for e in application_model.entities},
            first_id=0 if current_graph is None else len(current_graph.nodes),
        )

        all_nodes = extracted_nodes
        if current_graph is not None:
            all_nodes += current_graph.nodes

        # node_clusters = self.resolve_entities_from_file(
        #     model=model, entities=all_nodes, parsed_file=parsed_file
        # )

        extracted_relations = self.extract_relations_from_file(
            model=model,
            relation_descriptions=application_model.get_relation_descriptions(),
            entities=extracted_nodes,
            parsed_file=parsed_file,
        )

        nodes: typing.Dict[str, kg.Node] = {n.id: n for n in all_nodes}

        edges: typing.List[kg.Edge] = []
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
            nodes=all_nodes,
            edges=edges,
        )

        # graph = graph.compact(
        #     match_node=lambda n1, n2: any(
        #         n1 in cluster and n2 in cluster for cluster in node_clusters
        #     )
        # )

        return graph

    @staticmethod
    def get_name() -> str:
        return "PromptCreation"
