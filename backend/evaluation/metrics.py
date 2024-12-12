import dataclasses
import json
import pathlib
import re
import typing
from collections import defaultdict

import nltk
import numpy as np
from scipy.optimize import linear_sum_assignment

import model.knowledge_graph as kg
from evaluation.groundtruth_parser import (
    parse_manual_annotated_file,
)
from model import match


@dataclasses.dataclass
class MatchNode:
    text: str
    type: str


@dataclasses.dataclass
class MatchRelation:
    pass


@dataclasses.dataclass
class Match:
    prediction: MatchNode
    ground_truth: MatchNode
    similarity: float


@dataclasses.dataclass
class MatchResult:
    matches: typing.List[Match]
    missing: typing.List[MatchNode]
    superfluous: typing.List[MatchNode]


def optimal_matching(
    predicted_graph: kg.Graph,
    reference_graph: kg.Graph,
) -> typing.List[Match]:
    predictions = [
        MatchNode(text=n.name, type=n.entity.name) for n in predicted_graph.nodes
    ]
    ground_truth = [
        MatchNode(text=n.name, type=n.entity.name) for n in reference_graph.nodes
    ]

    similarity_dict = get_similarity_dictionary(predicted_graph, reference_graph)

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
            elif pred.type.lower() != true.type.lower():
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
    predicted_graph: kg.Graph,
    reference_graph: kg.Graph,
) -> dict:
    similarities = defaultdict(dict)

    predictions = [
        MatchNode(text=n.name, type=n.entity.name) for n in predicted_graph.nodes
    ]
    ground_truth = [
        MatchNode(text=n.name, type=n.entity.name) for n in reference_graph.nodes
    ]

    for extracted_mention in predictions:
        extracted_name = extracted_mention.text
        for ground_truth_mention in ground_truth:
            ground_truth_name = ground_truth_mention.text
            similarity = match.overlap_similarity(
                extracted_name, ground_truth_name, ignored_pos_tags=["det"]
            )
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


@dataclasses.dataclass
class Stats:
    num_ok: float
    num_wrong: float
    num_gold: float
    num_pred: float

    @property
    def recall(self):
        if self.num_gold == 0:
            if self.num_ok == 0:
                return 1.0
            return 0.0
        return self.num_ok / self.num_gold

    @property
    def precision(self):
        if self.num_pred == 0:
            if self.num_ok == 0:
                return 1.0
            return 0.0
        return self.num_ok / self.num_pred

    @property
    def f1(self):
        p = self.precision
        r = self.recall
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)

    def f_beta(self, beta: float):
        assert beta > 0
        p = self.precision
        r = self.recall
        numerator = (p * beta**2) + r
        if numerator == 0:
            return 0.0
        return (1 + beta**2) * p * r / numerator


def get_stats(
    *,
    predicted_graph: kg.Graph,
    reference_graph: kg.Graph,
    threshold: float = 0.4,
    verbose: bool = False,
) -> Stats:
    predictions = [
        MatchNode(text=n.name, type=n.entity.name) for n in predicted_graph.nodes
    ]
    ground_truth = [
        MatchNode(text=n.name, type=n.entity.name) for n in reference_graph.nodes
    ]

    matches = optimal_matching(predicted_graph, reference_graph)

    num_gold = len(ground_truth)
    num_pred = len(predictions)
    num_ok = 0
    non_ok = 0

    for m in matches:
        if m.prediction is None:
            if verbose:
                print(f"MISSING | {m.ground_truth.text}")
            non_ok += 1
            continue

        if m.ground_truth is None:
            if verbose:
                print(f"ADDITIONAL | {m.prediction.text}")
            non_ok += 1
            continue

        if m.similarity < threshold:
            if verbose:
                print(
                    f"TEXT | ({m.similarity:.2f}) - {m.ground_truth.text} ({m.ground_truth.type}) - "
                    f"{m.prediction.text} ({m.prediction.type})"
                )
            non_ok += 1
            continue

        if m.prediction.type.lower() != m.ground_truth.type.lower():
            if verbose:
                print(
                    f"TYPE | {m.ground_truth.text} ({m.ground_truth.type}) - "
                    f"{m.prediction.text} ({m.prediction.type})"
                )
            non_ok += 1
            continue

        if verbose:
            print(f"OK | {m.ground_truth.text} - {m.prediction.text}")
        num_ok += 1

    return Stats(num_ok=num_ok, num_wrong=non_ok, num_gold=num_gold, num_pred=num_pred)


if __name__ == "__main__":

    def main():
        nltk.download("punkt_tab")

        ground_truth_path = (
            pathlib.Path(__file__).parent.parent.absolute() / "res" / "ground_truth_simple.csv"
        )
        ground_truth = parse_manual_annotated_file(file_path=ground_truth_path)

        knowledge_graph_path = (
            pathlib.Path(__file__).parent.parent.absolute()
            / "res"
            / "result"
            / "model-instances"
            / "simple.json"
        )
        with open(knowledge_graph_path, "r") as file:
            graph = kg.Graph.from_dict(json.load(file))

        matches = optimal_matching(graph, ground_truth)

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

        stats = get_stats(
            predicted_graph=graph,
            reference_graph=ground_truth,
        )

        precision = stats.precision
        recall = stats.recall
        f1 = stats.f1
        f2 = stats.f_beta(2)

        print()
        print()
        print(f"Precision:  {precision:.2%}")
        print(f"Recall:     {recall:.2%}")
        print(f"F1-Score:   {f1:.2%}")
        print(f"F2-Score:   {f2:.2%}")

    main()
