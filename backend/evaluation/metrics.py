import collections
import dataclasses
import difflib
import json
import pathlib
import re
import typing
from collections import defaultdict

import nltk
import numpy as np
from scipy.optimize import linear_sum_assignment

from evaluation.groundtruth_parser import (
    parse_manual_annotated_file,
)
from model.knowledge_graph import Graph


@dataclasses.dataclass
class MatchNode:
    text: str
    type: str
    page: int
    file: str


@dataclasses.dataclass
class MatchRelation:
    pass


@dataclasses.dataclass
class Match:
    prediction: MatchNode
    ground_truth: MatchNode
    similarity: float


def char_similarity(s1: str, s2: str) -> float:
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def token_similarity(s1: str, s2: str) -> float:
    tokens_1 = nltk.tokenize.word_tokenize(s1)
    tokens_2 = nltk.tokenize.word_tokenize(s2)
    return difflib.SequenceMatcher(None, tokens_1, tokens_2).ratio()


@dataclasses.dataclass
class MatchResult:
    matches: typing.List[Match]
    missing: typing.List[MatchNode]
    superfluous: typing.List[MatchNode]


def optimal_matching(
    predictions: typing.List[MatchNode],
    ground_truth: typing.List[MatchNode],
    similarity_dict: dict,
) -> typing.List[Match]:
    len_extracted = len(predictions)
    len_ground_truth = len(ground_truth)

    # pad with dummy nodes (None values)
    if len_extracted < len_ground_truth:
        predictions += [None] * (len_ground_truth - len_extracted)
    if len_ground_truth < len_extracted:
        ground_truth += [None] * (len_extracted - len_ground_truth)

    # Similarity matrix
    cost_matrix = np.zeros((len(predictions), len(ground_truth)))

    for i, pred in enumerate(predictions):
        for j, true in enumerate(ground_truth):
            if pred is None or true is None:
                similarity = 0.0
            else:
                similarity = similarity_dict.get(pred.text, {}).get(true.text, 0.0)
            cost_matrix[i, j] = -similarity

    # Apply Hungarian Algorithm to find an optimal matching
    row_indices, col_indices = linear_sum_assignment(cost_matrix)

    # Build matches
    matches = []
    for i, j in zip(row_indices, col_indices):
        pred = predictions[i]
        true = ground_truth[j]
        similarity = -cost_matrix[i, j]
        matches.append(
            Match(
                pred,
                true,
                similarity=similarity,
            )
        )

    return matches


def get_similarity_dictionary(
    extracted_mentions: typing.List[MatchNode],
    ground_truth_mentions: typing.List[MatchNode],
) -> dict:
    similarities = defaultdict(dict)

    for extracted_mention in extracted_mentions:
        extracted_name = extracted_mention.text
        for ground_truth_mention in ground_truth_mentions:
            ground_truth_name = ground_truth_mention.text
            similarity = token_similarity(extracted_name, ground_truth_name)
            similarities[extracted_name][ground_truth_name] = similarity

    return dict(similarities)


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


def print_matches(matches: typing.List[Match]):
    for match in matches:
        print(f"--- {match.similarity:.4f} ---------------------------")
        if match.prediction is not None:
            print(f"Pred: {match.prediction.text} ({match.prediction.type})")
        else:
            print(f"Pred: ---")
        if match.ground_truth is not None:
            ground_truth_text = match.ground_truth.text.replace("\n", "")
            ground_truth_text = re.sub(r"\s{2,}", " ", ground_truth_text)
            print(f"True: {ground_truth_text} ({match.ground_truth.type})")
        else:
            print(f"True: ---")


Stats = collections.namedtuple("Stats", ["num_ok", "num_wrong", "num_gold", "num_pred"])


def get_stats(
    *,
    predictions: typing.List[MatchNode],
    ground_truth: typing.List[MatchNode],
    matches: typing.List[Match],
    threshold: float = 0.4,
) -> Stats:
    num_gold = len(ground_truth)
    num_pred = len(predictions)
    num_ok = 0
    non_ok = 0

    for match in matches:
        if match.prediction is None or match.ground_truth is None:
            non_ok += 1
            continue

        if match.prediction.type != match.ground_truth.type:
            non_ok += 1
            continue

        if match.similarity < threshold:
            non_ok += 1
            continue

        num_ok += 1

    return Stats(num_ok=num_ok, num_wrong=non_ok, num_gold=num_gold, num_pred=num_pred)


if __name__ == "__main__":

    def main():
        nltk.download("punkt_tab")

        ground_truth_path = (
            pathlib.Path(__file__).parent.parent.absolute() / "res" / "ground_truth.csv"
        )
        ground_truth_nodes = parse_manual_annotated_file(file_path=ground_truth_path)

        knowledge_graph_path = (
            pathlib.Path(__file__).parent.parent.absolute()
            / "result"
            / "model-instances"
            / "simple.json"
        )
        with open(knowledge_graph_path, "r") as file:
            graph = Graph.from_dict(json.load(file))

        predictions = [
            MatchNode(text=n.name, type=n.entity.name, page=0, file="")
            for n in graph.nodes
        ]
        ground_truth = [
            MatchNode(text=n.name, type=n.entity, page=0, file="")
            for n in ground_truth_nodes
        ]

        sim_dict = get_similarity_dictionary(predictions.copy(), ground_truth.copy())

        matches = optimal_matching(predictions.copy(), ground_truth.copy(), sim_dict)

        match_threshold = 0.8
        ok_matches = [m for m in matches if m.similarity > match_threshold]

        print()
        print(f"### > {match_threshold} #######################")
        print_matches(ok_matches)
        print()
        print(f"### < {match_threshold} and > 0.5 #############")
        print_matches([m for m in matches if 0.5 < m.similarity < match_threshold])
        print()
        print(f"### < 0.5 #####################################")
        print_matches([m for m in matches if 0.0 < m.similarity < 0.5])
        print()
        print(f"### = 0.0 #####################################")
        print_matches([m for m in matches if m.similarity == 0.0])

        num_ok, num_wrong, num_gold, num_pred = get_stats(
            predictions=predictions.copy(),
            ground_truth=ground_truth.copy(),
            matches=matches,
        )

        precision = num_ok / num_pred if num_pred > 0 else 0.0
        recall = num_ok / num_gold if num_gold > 0 else 0.0
        f1 = calculate_f1_score(precision=precision, recall=recall)

        print()
        print(f"Ok: {num_ok}, pred: {num_pred}, gold: {num_gold}")

        print()
        print()
        print(f"Precision:  {precision:.2%}")
        print(f"Recall:     {recall:.2%}")
        print(f"F1-Score:   {f1:.2%}")

    main()
