import typing
import json
import difflib
from evaluation.groundtruth_parser import GroundtruthMention, parse_manual_annotated_file
from model.knowledge_graph import Graph, Node
import numpy as np
from scipy.optimize import linear_sum_assignment


def calculate_similarity(s1: str, s2: str) -> float:
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def optimal_matching(extracted_mentions, groundtruth_mentions, similarity_dict):
    # todo: This code must be checked for correctness
    # Erstellen der Kostenmatrix (negativ der Ähnlichkeiten, da wir minimieren wollen)
    cost_matrix = np.zeros((len(extracted_mentions), len(groundtruth_mentions)))

    # Erstelle eine Zuordnung der Indizes zu den Namen
    extracted_names = [mention.name for mention in extracted_mentions]
    groundtruth_names = [mention.name for mention in groundtruth_mentions]

    for i, extracted_name in enumerate(extracted_names):
        for j, gt_name in enumerate(groundtruth_names):
            # Ähnlichkeit in die Matrix eintragen (negativ, weil wir maximieren wollen)
            similarity = similarity_dict.get(extracted_name, {}).get(gt_name, 0.0)
            cost_matrix[i, j] = -similarity

    # Verwenden des Hungarian Algorithmus, um das optimale Matching zu finden
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Matching Ergebnis ausgeben
    matching = []
    total_similarity = 0
    for i, j in zip(row_ind, col_ind):
        extracted_mention = extracted_names[i]
        gt_mention = groundtruth_names[j]
        similarity = -cost_matrix[i, j]  # Negatives Vorzeichen rückgängig machen
        matching.append((extracted_mention, gt_mention, similarity))
        total_similarity += similarity

    return matching, total_similarity


def get_similarity_dictionary(extracted_mentions: typing.List[Node],
                   groundtruth_mentions: typing.List[GroundtruthMention]) -> dict:
    similarities = {}
    for extracted_mention in extracted_mentions:
        for gt_mention in groundtruth_mentions:
            similarity = calculate_similarity(extracted_mention.name, gt_mention.name)

            if extracted_mention.name not in similarities.keys():
                similarities[extracted_mention.name] = {}
            if gt_mention.name not in similarities[extracted_mention.name]:
                similarities[extracted_mention.name][gt_mention.name] = 0.0
            similarities[extracted_mention.name][gt_mention.name] = similarity

    return similarities




if __name__ == '__main__':
    ground_truth = parse_manual_annotated_file(r'../files/groundtruth_result.csv')
    print(ground_truth)
    exit(-1)

    with open(r'../result/extracted_information.json', "r") as file:
            extracted_mentions = Graph.from_dict(json.load(file))
    ground_truth_simple = [g.name for g in ground_truth]
    extracted_simple = [e.name for e in extracted_mentions.nodes]

    sim_dict = get_similarity_dictionary(ground_truth, ground_truth)

    matching, total_similarity = optimal_matching(ground_truth, ground_truth, sim_dict)

    print("Matching:")
    for match in matching:
        print(f"{match[0]} matched with {match[1]} (Similarity: {match[2]})")

    print(f"Total Similarity: {total_similarity}")

