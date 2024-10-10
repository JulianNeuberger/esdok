import difflib
import typing

import model.knowledge_graph as kg


def node_similarity_matcher(
    similarity_threshold: float,
) -> typing.Callable[[kg.Node, kg.Node], bool]:
    def match_node_by_string_similarity(node1: kg.Node, node2: kg.Node) -> bool:
        if node1.type != node2.type:
            return False
        if node1.aspect != node2.aspect:
            return False
        return (
            difflib.SequenceMatcher(None, node1.name, node2.name).ratio()
            > similarity_threshold
        )

    return match_node_by_string_similarity


def strict_edge_matcher(e1: kg.Edge, e2: kg.Edge) -> bool:
    if e1.type != e2.type:
        return False
    if e1.source != e2.source:
        return False
    if e1.target != e2.target:
        return False
    return True
