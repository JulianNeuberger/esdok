import dataclasses
import difflib
import json
import typing
from pathlib import Path

import networkx as nx
import nltk

from model import meta_model


def node_match(threshold: float = 0.6):
    def match(n1, n2) -> float:
        if n1["type"].lower() != n2["type"].lower():
            return False

        n1_tokens = [t.lower() for t in nltk.word_tokenize(n1["name"])]
        n2_tokens = [t.lower() for t in nltk.word_tokenize(n2["name"])]
        sim = difflib.SequenceMatcher(None, n1_tokens, n2_tokens).ratio()
        is_matching = sim > threshold
        return is_matching

    return match


def edge_match(e1, e2):
    if e1["type"].lower() == e2["type"].lower():
        return True
    return False


def should_merge(
    c1: typing.List["Node"],
    c2: typing.List["Node"],
    match_node: typing.Optional[typing.Callable[["Node", "Node"], bool]],
) -> bool:
    for n1 in c1:
        for n2 in c2:
            if match_node(n1, n2):
                return True
    return False


@dataclasses.dataclass(frozen=True)
class Graph:
    nodes: typing.List["Node"]
    edges: typing.List["Edge"]

    def compact(
        self,
        *,
        match_node: typing.Optional[typing.Callable[["Node", "Node"], bool]] = None,
        match_edge: typing.Optional[typing.Callable[["Edge", "Edge"], bool]] = None,
    ) -> "Graph":
        new_nodes = []
        new_edges = []

        node_mappings: typing.Dict[str, Node] = {}

        if match_node is not None:
            un_merged_clusters = [[n] for n in self.nodes]
            merged_clusters = []

            while len(un_merged_clusters) > 0:
                cluster = un_merged_clusters.pop(0)
                clusters_to_merge = []
                for other in un_merged_clusters:
                    if should_merge(cluster, other, match_node):
                        clusters_to_merge.append(other)
                for other in clusters_to_merge:
                    un_merged_clusters.remove(other)
                    cluster += other
                merged_clusters.append(cluster)

            for cluster in merged_clusters:
                n: Node
                cluster = sorted(cluster, key=lambda n: len(n.name), reverse=True)
                representative = cluster[0]
                new_nodes.append(representative)
                for n in cluster:
                    node_mappings[n.id] = representative
                print([n.name for n in cluster])
        else:
            for node in self.nodes:
                new_nodes.append(node)
                node_mappings[node.id] = node

        if match_edge is not None:
            for edge in self.edges:
                edge = Edge(
                    id=edge.id,
                    source=node_mappings[edge.source.id],
                    target=node_mappings[edge.target.id],
                    type=edge.type,
                )

                found_match = False
                for other in new_edges:
                    if match_edge(edge, other):
                        found_match = True
                        break
                if not found_match:
                    new_edges.append(edge)
        else:
            for edge in self.edges:
                new_edges.append(
                    Edge(
                        id=edge.id,
                        source=node_mappings[edge.source.id],
                        target=node_mappings[edge.target.id],
                        type=edge.type,
                    )
                )

        return Graph(new_nodes, new_edges)

    def union(self, other: "Graph") -> "Graph":
        return Graph(
            nodes=self.nodes + other.nodes,
            edges=self.edges + other.edges,
        )

    def merge(
        self,
        other: "Graph",
        *,
        match_node: typing.Optional[typing.Callable[["Node", "Node"], bool]],
        match_edge: typing.Optional[typing.Callable[["Edge", "Edge"], bool]],
    ) -> "Graph":
        graph = self.union(other)
        graph = graph.compact(match_node=match_node, match_edge=match_edge)
        return graph

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

    @staticmethod
    def from_dict(d: dict) -> "Graph":
        return Graph(
            nodes=[Node.from_dict(n) for n in d["nodes"]],
            edges=[Edge.from_dict(e) for e in d["edges"]],
        )

    @staticmethod
    def load(file_path: typing.Union[str, Path]) -> "Graph":
        with open(file_path) as f:
            graph_json = json.load(f)
            graph = Graph.from_dict(graph_json)
            return graph

    def save(self, file_path: typing.Union[str, Path]) -> None:
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f)

    def replace_node(self, node: "Node") -> "Graph":
        updated_edges = []
        for e in self.edges:
            if e.source.id == node.id:
                e = Edge(id=e.id, source=node, target=e.target, type=e.type)
            if e.target.id == node.id:
                e = Edge(id=e.id, source=e.source, target=node, type=e.type)
            updated_edges.append(e)
        updated_nodes = []
        for n in self.nodes:
            if n.id == node.id:
                updated_nodes.append(node)
            else:
                updated_nodes.append(n)
        return Graph(nodes=updated_nodes, edges=updated_edges)

    def to_nx(self) -> nx.Graph:
        g = nx.Graph()
        g.add_nodes_from(
            (n.id, {"name": n.name, "type": n.entity.name, "id": n.id})
            for n in self.nodes
        )
        g.add_edges_from(
            (r.source.id, r.target.id, {"type": r.type}) for r in self.edges
        )
        return g

    def layout(self) -> "Graph":
        g = self.to_nx()
        pos = nx.kamada_kawai_layout(g, scale=500)

        knowledge_graph = self
        for n in self.nodes:
            n_pos = pos[n.id]
            assert n_pos.shape == (2,)
            pos_as_tuple = (n_pos[0], n_pos[1])
            knowledge_graph = knowledge_graph.replace_node(
                n.with_position(pos_as_tuple)
            )
        return knowledge_graph

    def graph_edit_distance(
        self, other: "Graph", timeout_seconds: float = 60 * 2
    ) -> float:
        g1 = self.to_nx()
        g2 = other.to_nx()

        return nx.graph_edit_distance(
            g1,
            g2,
            node_match=node_match(threshold=0.6),
            edge_match=edge_match,
            timeout=timeout_seconds,
        )


@dataclasses.dataclass(frozen=True, eq=True)
class Aspect:
    name: str
    shape: str
    color: str

    def to_dict(self):
        return {
            "name": self.name,
            "shape": self.shape,
            "color": self.color,
        }

    @staticmethod
    def from_dict(d: dict) -> "Aspect":
        return Aspect(name=d["name"], shape=d["shape"], color=d["color"])


@dataclasses.dataclass(frozen=True, eq=True)
class DataSource:
    file: str
    page_start: int
    page_end: int

    def to_dict(self):
        return {
            "file": self.file,
            "pageStart": self.page_start,
            "pageEnd": self.page_end,
        }

    @staticmethod
    def from_dict(d: dict) -> "DataSource":
        return DataSource(
            file=d["file"], page_start=d["pageStart"], page_end=d["pageEnd"]
        )


@dataclasses.dataclass(frozen=True, eq=True)
class Node:
    id: str
    name: str
    position: typing.Tuple[float, float] | None
    entity: meta_model.Entity
    source: DataSource

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "entity": self.entity.to_dict(),
            "position": {
                "x": self.position[0],
                "y": self.position[1],
            },
            "source": self.source.to_dict(),
        }

    @staticmethod
    def from_dict(d: dict) -> "Node":
        return Node(
            id=d["id"],
            name=d["name"],
            position=(d["position"]["x"], d["position"]["y"]),
            entity=meta_model.Entity.from_dict(d["entity"]),
            source=DataSource.from_dict(d["source"]),
        )

    def with_position(self, pos: typing.Tuple[float, float]) -> "Node":
        return Node(
            source=self.source,
            position=pos,
            entity=self.entity,
            name=self.name,
            id=self.id,
        )


@dataclasses.dataclass(frozen=True, eq=True)
class Edge:
    id: str
    source: Node
    target: Node
    type: str

    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "type": self.type,
        }

    @staticmethod
    def from_dict(d: dict) -> "Edge":
        return Edge(
            id=d["id"],
            source=Node.from_dict(d["source"]),
            target=Node.from_dict(d["target"]),
            type=d["type"],
        )
