import dataclasses
import typing

import pandas as pd


@dataclasses.dataclass
class GroundtruthMention:
    name: str
    entity: str
    document: str
    start_page: int
    end_page: int


def extract_entity(annotation: str):
    formatted = annotation.rstrip()
    formatted = formatted.replace('Ê', '')
    parts = formatted.split(' > ')

    transformed_value = parts[-1]
    if parts[-1] == 'System' or parts[-1] == 'Component':
        transformed_value = 'Resource'

    if parts[-1] == 'Undesired Condition':
        transformed_value = 'Condition'

    return transformed_value


def parse_manual_annotated_file(file_path: str) -> typing.List[GroundtruthMention]:
    groundtruth_df = pd.read_csv(file_path, encoding='utf8', delimiter=';')
    filtered_df = groundtruth_df[['Dokumentname', 'Code', 'Anfang', 'Ende', 'Segment']]

    extracted_mentions = []
    for _, row in filtered_df.iterrows():
        entity = extract_entity(row['Code'])
        if entity != 'Concept in Condition':
            extracted_mentions.append(GroundtruthMention(
                name=row['Segment'],
                entity=entity,
                document=row['Dokumentname'],
                start_page=row['Anfang'],
                end_page=row['Ende']
            ))

    return extracted_mentions
