import difflib
import typing

import nltk

import model.knowledge_graph as kg


def char_similarity(s1: str, s2: str) -> float:
    s1 = s1.lower()
    s2 = s2.lower()
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def token_similarity(s1: str, s2: str) -> float:
    s1 = s1.lower()
    s2 = s2.lower()
    tokens_1 = nltk.tokenize.word_tokenize(s1)
    tokens_2 = nltk.tokenize.word_tokenize(s2)
    return difflib.SequenceMatcher(None, tokens_1, tokens_2).ratio()


def overlap_similarity(
    s1: str, s2: str, ignored_pos_tags: typing.List[str] = None
) -> float:
    if ignored_pos_tags is not None:
        ignored_pos_tags = [p.lower() for p in ignored_pos_tags]

    s1 = s1.lower()
    s2 = s2.lower()
    pos_tagged_1 = nltk.pos_tag(nltk.word_tokenize(s1))
    pos_tagged_2 = nltk.pos_tag(nltk.word_tokenize(s2))
    pos_tagged_1 = [
        (token, pos)
        for token, pos in pos_tagged_1
        if ignored_pos_tags is None or pos.lower() not in ignored_pos_tags
    ]
    pos_tagged_2 = [
        (token, pos)
        for token, pos in pos_tagged_2
        if ignored_pos_tags is None or pos.lower() not in ignored_pos_tags
    ]

    tokens1 = [t for t, _ in pos_tagged_1]
    tokens2 = [t for t, _ in pos_tagged_2]
    same_tokens = [t for t in tokens1 if t in tokens2]
    return len(same_tokens) / (max(len(tokens1), len(tokens2)))


def node_matcher(
    text_matcher: typing.Callable,
    similarity_threshold: float,
    case_sensitive: bool = False,
):
    def f(n1: kg.Node, n2: kg.Node) -> bool:
        name1 = n1.name
        if not case_sensitive:
            name1 = name1.lower()
        name2 = n2.name
        if not case_sensitive:
            name2 = name2.lower()

        type1 = n1.entity.name
        if not case_sensitive:
            type1 = type1.lower()
        type2 = n2.entity.name
        if not case_sensitive:
            type2 = type2.lower()

        if type1 != type2:
            return False

        sim = text_matcher(name1, name2)
        return sim >= similarity_threshold

    return f


# def node_similarity_matcher(
#     similarity_threshold: float,
#     case_sensitive: bool = False,
# ) -> typing.Callable[[kg.Node, kg.Node], bool]:
#     def match_node_by_string_similarity(node1: kg.Node, node2: kg.Node) -> bool:
#         name1 = node1.name
#         if not case_sensitive:
#             name1 = name1.lower()
#         name2 = node2.name
#         if not case_sensitive:
#             name2 = name2.lower()
#
#         type1 = node1.entity.name
#         if not case_sensitive:
#             type1 = type1.lower()
#         type2 = node2.entity.name
#         if not case_sensitive:
#             type2 = type2.lower()
#
#         if type1 != type2:
#             return False
#         ratio = difflib.SequenceMatcher(None, name1, name2).ratio()
#         return ratio > similarity_threshold
#
#     return match_node_by_string_similarity


def strict_edge_matcher(e1: kg.Edge, e2: kg.Edge) -> bool:
    if e1.type != e2.type:
        return False
    if e1.source != e2.source:
        return False
    if e1.target != e2.target:
        return False
    return True
