import model.knowledge_graph as kg
from model import match


def test_merge():
    a1 = kg.Aspect(name="a1", shape="circle", color="red")
    a2 = kg.Aspect(name="a2", shape="rect", color="blue")

    g1n1 = kg.Node(id="g1_n1", name="abcd", type="t1", position=(0, 0), aspect=a1)
    g1n2 = kg.Node(id="g1_n2", name="wxyz", type="t1", position=(0, 0), aspect=a1)

    g1 = kg.Graph(
        nodes=[g1n1, g1n2],
        edges=[
            kg.Edge(id="g1_e1", source=g1n1, target=g1n2, type="r1"),
        ],
    )

    exact_match = kg.Node(
        id="g2_n1", name="abcd", type="t1", position=(0, 0), aspect=a1
    )
    match_75_percent = kg.Node(
        id="g2_n2", name="abc", type="t1", position=(0, 0), aspect=a1
    )
    different_type = kg.Node(
        id="g2_n2", name="abcd", type="t2", position=(0, 0), aspect=a1
    )
    zero_percent_match = kg.Node(
        id="g2_n3", name="fghi", type="t1", position=(0, 0), aspect=a1
    )

    g2n2 = kg.Node(id="g1_n2", name="wxyz", type="t1", position=(0, 0), aspect=a1)
    duplicate_edge = kg.Edge(id="g2_e1", source=exact_match, target=g2n2, type="r1")
    new_edge = kg.Edge(
        id="g2_e2", source=exact_match, target=zero_percent_match, type="r2"
    )

    g2 = kg.Graph(
        nodes=[g2n2, exact_match, match_75_percent, different_type, zero_percent_match],
        edges=[duplicate_edge, new_edge],
    )

    g3 = g1.merge(
        g2,
        match_node=match.node_similarity_matcher(0.5),
        match_edge=match.strict_edge_matcher,
    )

    assert len(g3.nodes) == 4
    assert len(g3.edges) == 2


def test_compact():
    a1 = kg.Aspect(name="a1", shape="circle", color="red")
    a2 = kg.Aspect(name="a2", shape="rect", color="blue")

    n1 = kg.Node(id="n1", name="abcd", type="t1", position=(0, 0), aspect=a1)  # keep
    n2 = kg.Node(id="n2", name="wxyz", type="t1", position=(0, 0), aspect=a1)  # keep
    n3 = kg.Node(
        id="n3", name="abc", type="t1", position=(0, 0), aspect=a1
    )  # discard (match 75%)
    n4 = kg.Node(
        id="n4", name="abc", type="t2", position=(0, 0), aspect=a1
    )  # keep (type)
    n5 = kg.Node(id="n5", name="a", type="t1", position=(0, 0), aspect=a1)  # keep
    n6 = kg.Node(
        id="n6", name="abcd", type="t1", position=(0, 0), aspect=a2
    )  # keep (aspect)

    graph = kg.Graph(
        nodes=[n1, n2, n3, n4, n5, n6],
        edges=[
            kg.Edge(id="e1", source=n1, target=n2, type="r1"),  # keep
            kg.Edge(id="e2", source=n3, target=n2, type="r1"),  # discard (same nodes)
            kg.Edge(id="e3", source=n4, target=n2, type="r1"),  # keep (different nodes)
            kg.Edge(id="e4", source=n3, target=n2, type="r2"),  # keep (different types)
        ],
    )

    assert len(graph.nodes) == 6
    assert len(graph.edges) == 4

    graph = graph.compact(
        match_node=match.node_similarity_matcher(0.6),
        match_edge=match.strict_edge_matcher,
    )

    assert len(graph.nodes) == 5
    assert len(graph.edges) == 3
