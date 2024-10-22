import dataclasses
import json
import random
import typing
from pathlib import Path

import networkx as nx

from model.meta_model import Position


@dataclasses.dataclass(frozen=True)
class Graph:
    nodes: typing.List["Node"]
    edges: typing.List["Edge"]

    def merge(
        self,
        other: "Graph",
        match_edge: typing.Optional[typing.Callable[["Edge", "Edge"], bool]],
        match_node: typing.Optional[typing.Callable[["Node", "Node"], bool]],
    ) -> "Graph":
        # copy lists, elements are immutable
        new_nodes = [n for n in self.nodes]
        new_edges = [e for e in self.edges]

        node_mappings = {}
        for other_node in other.nodes:
            has_match = False
            for self_node in self.nodes:
                if match_node(self_node, other_node):
                    # found a matching node, record the mapping
                    has_match = True
                    node_mappings[other_node] = self_node
                    print(f"Merging node {self_node.name} and node {other_node.name}")
                    break

            if not has_match:
                # unique node
                node_mappings[other_node] = other_node
                new_nodes.append(other_node)

        for other_edge in other.edges:
            # update node arguments, as they may have been matched
            other_edge = Edge(
                id=other_edge.id,
                source=node_mappings[other_edge.source],
                target=node_mappings[other_edge.target],
                type=other_edge.type,
            )

            has_match = False
            for self_edge in self.edges:
                # try and find a match
                if match_edge(self_edge, other_edge):
                    has_match = True
                    break

            if not has_match:
                new_edges.append(other_edge)

        return Graph(nodes=new_nodes, edges=new_edges)

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

    def layout(self) -> "Graph":
        g = nx.Graph()
        g.add_nodes_from([n.id for n in self.nodes])
        g.add_edges_from([(r.source.id, r.target.id) for r in self.edges])

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
class Node:
    id: str
    name: str
    type: str
    position: typing.Tuple[float, float] | None
    aspect: Aspect | None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "aspect": self.aspect.to_dict(),
            "position": {
                "x": self.position[0],
                "y": self.position[1],
            },
        }

    @staticmethod
    def from_dict(d: dict) -> "Node":
        return Node(
            id=d["id"],
            name=d["name"],
            type=d["type"],
            position=(d["position"]["x"], d["position"]["y"]),
            aspect=Aspect.from_dict(d["aspect"]),
        )

    def with_position(self, pos: typing.Tuple[float, float]) -> "Node":
        return Node(
            position=pos, aspect=self.aspect, type=self.type, name=self.name, id=self.id
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
