import pathlib
import dataclasses
import typing
import xml.etree.ElementTree as ET

from model.application_model import get_random_position, ApplicationModel
from model.color import CommonColors
from model.meta_model import Aspect, Relation, Entity
from model.shape import Shape

OPERATIONAL_ASPECT = Aspect(
    name="operational",
    text_color=CommonColors.BLACK.value,
    shape_color=CommonColors.GREEN.value,
    shape=Shape.PARALLELOGRAM,
)

ORGANIZATIONAL_ASPECT = Aspect(
    name="organizational",
    text_color=CommonColors.BLACK.value,
    shape_color=CommonColors.RED.value,
    shape=Shape.RECTANGLE,
)

CONTROL_FLOW_ASPECT = Aspect(
    name="control-flow",
    text_color=CommonColors.BLACK.value,
    shape_color=CommonColors.MAGENTA.value,
    shape=Shape.ROUND_RECTANGLE,
)

# Change that later for other data (or remove it completely) (its hard coded to map Biffls things
ASPECT_MAPPING = {
    "Product": OPERATIONAL_ASPECT,
    "Business Management, Quality Management, Product, Process, Resource": CONTROL_FLOW_ASPECT,
    "Resource Actor": ORGANIZATIONAL_ASPECT,
    "Business Management, Quality Management, Risk Management": CONTROL_FLOW_ASPECT,
    "Resource System": ORGANIZATIONAL_ASPECT,
    "Resource Component": ORGANIZATIONAL_ASPECT,
    "Business Management, Quality Management, Risk Management, Product, Process, Resource": CONTROL_FLOW_ASPECT,
    "Process, Resource": OPERATIONAL_ASPECT,
    "Quality Management, Risk Management": OPERATIONAL_ASPECT,
    "Process": CONTROL_FLOW_ASPECT,
    "Product, Process, Resource": OPERATIONAL_ASPECT,
}

RELATION_CONNECTOR = {
    "Condition has Condition Concept": ("Concept in Condition", "Condition"),
    "Condition Concept is related to a PPR property": (
        "Concept in Condition",
        "PPR Property",
    ),
    "PPR Asset has a a PPR property": ("PPR Property", "PPR Asset"),
    "Condition contributes to Condition": ("Condition", "Condition"),
    "Condition Concept is related to a PPR asset": (
        "Concept in Condition",
        "PPR Asset",
    ),
}

EER_NAME = "EER Name:"
EER_DESCRIPTION = "EER Description:"
EER_ASPECTS = "EER Aspects:"
EER_EXAMPLE = "EER Example:"


@dataclasses.dataclass
class ParsedElement:
    type: str
    name: str
    description: str
    aspects: str
    example: str


def format_value(input_string: str, prefix: str) -> str:
    return input_string.lstrip().removeprefix(prefix).lstrip()


def extract_name_and_type(parsed_lines: typing.List[str]) -> typing.Tuple[str, str]:
    formatted_line = (
        format_value(parsed_lines[0], EER_NAME)
        .replace("\n", "")
        .replace('"', "")
        .strip()
    )

    name = ""
    element_type = ""

    if len(parsed_lines) == 1:
        if formatted_line.startswith("Relation"):
            element_type = "Relation"
            name = formatted_line.removeprefix("Relation ").strip()
        elif formatted_line.startswith("Entity"):
            element_type = "Entity"
            name = formatted_line.removeprefix("Entity ").strip()
        else:
            print(
                f"Could not parse {parsed_lines[0]}. Unknown beginning. Must start either with Relation or Entity"
            )

    return name, element_type


def extract_description(parsed_lines: typing.List[str]) -> str:
    return " ".join(parsed_lines)


def extract_example(parsed_lines: typing.List[str], concatenate: bool = True) -> str:
    if concatenate:
        return " ".join(parsed_lines)
    return parsed_lines[0]


def extract_aspects(parsed_lines: typing.List[str]) -> str:
    def format_aspect(aspect: str) -> str:
        return aspect.replace("\n", "").replace('"', "").replace("'", "").lstrip()

    if len(parsed_lines) == 1:
        return format_aspect(parsed_lines[0])
    return ""


def extract_eer_info(input_string):
    # Split the input string into lines based on the delimiter
    lines = input_string.split("//")

    line_result = {EER_NAME: [], EER_DESCRIPTION: [], EER_ASPECTS: [], EER_EXAMPLE: []}

    def process_line(line: str, key: str):
        if line.lstrip().startswith(key):
            line_result[key].append(format_value(line, key))

    for line in lines:
        process_line(line, EER_NAME)
        process_line(line, EER_DESCRIPTION)
        process_line(line, EER_ASPECTS)
        process_line(line, EER_EXAMPLE)

    name, element_type = extract_name_and_type(line_result[EER_NAME])

    return ParsedElement(
        type=element_type,
        name=name,
        description=extract_description(line_result[EER_DESCRIPTION]),
        aspects=extract_aspects(line_result[EER_ASPECTS]),
        example=extract_example(line_result[EER_EXAMPLE]),
    )


def create_application_model(parsed_elements: typing.List[ParsedElement]):
    def get_entity_by_name(entities: typing.List[Entity], name: str) -> Entity | None:
        for entity in entities:
            if entity.name == name:
                return entity
        return None

    # First create entities
    entities = []
    for element in parsed_elements:
        if element.type == "Entity":
            entities.append(
                Entity(
                    name=element.name,
                    description=element.description,
                    aspect=ASPECT_MAPPING[element.aspects],
                    position=get_random_position(0, 10, 0, 10),
                )
            )

    relations = []
    for element in parsed_elements:
        if element.type == "Relation":
            relations.append(
                Relation(
                    name=element.name,
                    description=element.description,
                    source=get_entity_by_name(
                        entities, RELATION_CONNECTOR[element.name][0]
                    ),
                    target=get_entity_by_name(
                        entities, RELATION_CONNECTOR[element.name][1]
                    ),
                )
            )

    return ApplicationModel(entities=entities, relations=relations)


def parse_xml_file(
    file: typing.Union[str, pathlib.Path, typing.IO, bytes]
) -> ApplicationModel:
    # Parse the XML data
    tree = ET.parse(file)
    root = tree.getroot()

    # Parse EER elements
    parsed_elements = []
    for panel in root.findall(".//panel_attributes"):
        if "// EER" in panel.text:
            parsed_elements.append(extract_eer_info(panel.text))

    return create_application_model(parsed_elements)


if __name__ == "__main__":
    application_model_file = (
        pathlib.Path(__file__).parent.parent.absolute()
        / "files"
        / "EER Model CEN PAN Space Lab Experiment 241006e.uxf"
    )

    with open(application_model_file, "r") as f:
        print(parse_xml_file(f))
