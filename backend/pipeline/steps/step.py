import dataclasses
import typing
import os
import langchain.prompts as lc_prompts
import api_key

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import BaseOutputParser
from abc import ABC

from model.application_model import ApplicationModel
from model.meta_model import Entity
from pipeline.llm_models import Models, ModelInformation
from pipeline.steps.utils import ParsedFile


@dataclasses.dataclass
class EntityResult:
    id: str
    type: str
    name: str
    aspect: str

    def to_dict(self) -> typing.Dict[str, str]:
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'aspect': self.aspect
        }


@dataclasses.dataclass
class RelationResult:
    id: str
    source: str
    target: str
    name: str

    def to_dict(self) -> typing.Dict[str, str]:
        return {
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'name': self.name
        }


class BasePipelineStep(ABC):

    def run(self, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def get_name() -> str:
        raise NotImplementedError()


class PromptCreation(BasePipelineStep):
    @staticmethod
    def parse_entity_extraction_result(result: str,
                                       type_aspect_mapping: typing.Dict[str, str]) -> typing.List[EntityResult]:
        result_list = []
        lines = result.splitlines()


        for i, line in enumerate(lines):
            result_type, name = line.split('|')
            result = EntityResult(id=f'n{i}', type=result_type, name=name, aspect=type_aspect_mapping[result_type])
            result_list.append(result)

        return result_list

    @staticmethod
    def parse_relation_extraction_result(result: str) -> typing.List[RelationResult]:
        print(result)
        result_list = []
        lines = result.splitlines()

        for i, line in enumerate(lines):
            name, source, target = line.split('|')
            result = RelationResult(id=f'e{i}', source=source, target=target, name=name)
            result_list.append(result)

        return result_list

    @staticmethod
    def extract_entities_from_file(model: ModelInformation, entity_descriptions: str,
                                   type_aspect_mapping: typing.Dict[str, str],
                                   parsed_file: ParsedFile) -> typing.List[EntityResult]:
        model = ChatOpenAI(model=model.model_name)

        with open('prompts/system_template_entity_extraction.txt', 'r', encoding='utf8') as f:
            system_template = f.read()

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_template), ("user", "{text}")]
        )

        parser = StrOutputParser()

        chain = prompt_template | model | parser

        return PromptCreation.parse_entity_extraction_result(
            chain.invoke({"entity_descriptions_application_model": entity_descriptions,
                          "text": parsed_file}), type_aspect_mapping=type_aspect_mapping)

    @staticmethod
    def extract_relations_from_file(model: ModelInformation, relation_descriptions: str,
                                    entities_to_use: typing.List[EntityResult], parsed_file: ParsedFile):
        model = ChatOpenAI(model=model.model_name)

        with open('prompts/system_template_relation_extraction.txt', 'r', encoding='utf8') as f:
            system_template = f.read()

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_template), ("user", "{text}")]
        )

        formatted_entities_to_use = ''
        for entity in entities_to_use:
            formatted_entities_to_use = formatted_entities_to_use + f'({entity.id}, {entity.type}, {entity.name})\n'

        print(formatted_entities_to_use)
        parser = StrOutputParser()

        chain = prompt_template | model | parser

        return PromptCreation.parse_relation_extraction_result(
            chain.invoke({"relation_descriptions_application_model": relation_descriptions,
                          "entities_to_use": formatted_entities_to_use,
                          "text": parsed_file}))


    def run(self, model: ModelInformation,
            application_model: ApplicationModel,
            parsed_file: ParsedFile) -> typing.Tuple[typing.List[EntityResult], typing.List[RelationResult]]:
        api_key.set_llm_api_key(model=model.model_name)
        extracted_entities = self.extract_entities_from_file(model=model,
                                                             entity_descriptions=application_model.get_entity_descriptions(),
                                                             type_aspect_mapping=application_model.get_type_aspect_mapping(),
                                                             parsed_file=parsed_file)

        extracted_relations = self.extract_relations_from_file(model=model,
                                                               relation_descriptions=application_model.get_relation_descriptions(),
                                                               entities_to_use=extracted_entities,
                                                               parsed_file=parsed_file)

        return extracted_entities, extracted_relations

    @staticmethod
    def get_name() -> str:
        return 'PromptCreation'
