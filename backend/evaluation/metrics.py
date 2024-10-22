import dataclasses
import typing
import json
import difflib
from evaluation.groundtruth_parser import GroundtruthMention, parse_manual_annotated_file
from model.knowledge_graph import Graph, Node
import numpy as np
from scipy.optimize import linear_sum_assignment
from collections import defaultdict


@dataclasses.dataclass
class Match:
    extracted_mention: Node
    ground_truth_mention: GroundtruthMention
    similarity: float


def calculate_similarity(s1: str, s2: str) -> float:
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def optimal_matching(extracted_mentions: typing.List[Node], ground_truth_mentions: typing.List[GroundtruthMention],
                     similarity_dict: dict) -> typing.List[Match]:
    len_extracted = len(extracted_mentions)
    len_ground_truth = len(ground_truth_mentions)

    if len_extracted > len_ground_truth:
        for i in range(len_extracted - len_ground_truth):
            ground_truth_mentions.append(GroundtruthMention(name=f'Dummy_GT_{i+1}', entity='', document='',
                                                            start_page=-1, end_page=-1))
    elif len_ground_truth > len_extracted:
        for i in range(len_ground_truth - len_extracted):
            extracted_mentions.append(Node(id=f'{i + 1}', name=f'Dummy_T_{i + 1}', type='Dummy', position=None, aspect=None))

    # Similarity matrix
    cost_matrix = np.zeros((len(extracted_mentions), len(ground_truth_mentions)))

    for i, extracted_mention in enumerate(extracted_mentions):
        for j, ground_truth_mention in enumerate(ground_truth_mentions):
            if 'Dummy' in extracted_mention.name or 'Dummy' in ground_truth_mention.name:
                similarity = 0.0
            else:
                similarity = similarity_dict.get(extracted_mention.name, {}).get(ground_truth_mention.name, 0.0)
            cost_matrix[i, j] = -similarity

    # Apply Hungarian Algorithm to find an optimal matching
    row_indices, col_indices = linear_sum_assignment(cost_matrix)

    # Build matches
    matches = []
    for i, j in zip(row_indices, col_indices):
        extracted_mention = extracted_mentions[i]
        ground_truth_mention = ground_truth_mentions[j]
        similarity = -cost_matrix[i, j]
        matches.append(Match(extracted_mention=extracted_mention,
                             ground_truth_mention=ground_truth_mention,
                             similarity=similarity))

    return matches


def get_similarity_dictionary(extracted_mentions: typing.List[Node],
                              ground_truth_mentions: typing.List[GroundtruthMention]) -> dict:
    similarities = defaultdict(dict)

    for extracted_mention in extracted_mentions:
        extracted_name = extracted_mention.name
        for ground_truth_mention in ground_truth_mentions:
            ground_truth_name = ground_truth_mention.name
            similarity = calculate_similarity(extracted_name, ground_truth_name)
            similarities[extracted_name][ground_truth_name] = similarity

    return dict(similarities)


def count_match_types_regardless_of_entity_type(matches: typing.List[Match],
                                                threshold: float = 0.8) -> typing.Tuple[int, int, int, int]:
    correct_matches = 0     # Number of correct matches
    incorrect_matches = 0   # Number of incorrect matches
    not_matched = 0     # Number of ground truth mentions not found
    over_matched = 0    # Number of extracted mentions that should not be found

    for match in matches:
        if 'Dummy' in match.extracted_mention.name:
            over_matched += 1
        elif 'Dummy' in match.ground_truth_mention.name:
            not_matched += 1
        elif calculate_similarity(match.extracted_mention.name, match.ground_truth_mention.name) > threshold:
            correct_matches += 1
        else:
            incorrect_matches += 1

    return correct_matches, incorrect_matches, not_matched, over_matched


def calculate_precision(correct_matches: int, incorrect_matches: int) -> float:
    if correct_matches + incorrect_matches > 0:
        return correct_matches / (correct_matches + incorrect_matches)

    return 0.0


def calculate_recall(correct_matches: int, not_matched: int) -> float:
    if correct_matches + not_matched > 0:
        return correct_matches / (correct_matches + not_matched)
    return 0.0


def calculate_f1_score(precision: float, recall: float) -> float:
    if precision + recall > 0:
        return 2 * (precision * recall) / (precision + recall)
    return 0.0


if __name__ == '__main__':
    ground_truth = parse_manual_annotated_file(r'../files/groundtruth_result.csv')

    with open(r'../result/extracted_information.json', "r") as file:
        extracted_mentions = Graph.from_dict(json.load(file))

    sim_dict = get_similarity_dictionary(extracted_mentions.nodes, ground_truth)

    matching = optimal_matching(extracted_mentions.nodes, ground_truth, sim_dict)

    print("Matching:")
    for match in matching:
        print(match)

    correct_m, incorrect_m, not_m, _ = count_match_types_regardless_of_entity_type(matching, 0.8)

    precision = calculate_precision(correct_matches=correct_m, incorrect_matches=incorrect_m)
    recall = calculate_recall(correct_matches=correct_m, not_matched=not_m)

    print(f'Precision: {precision}')
    print(f'Recall: {recall}')
    print(f'F1-Score: {calculate_f1_score(precision=precision, recall=recall)}')
