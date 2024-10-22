import dataclasses
import json
import typing
from pathlib import Path

import networkx as nx

from model import meta_model


@dataclasses.dataclass(frozen=True)
class Graph:
    nodes: typing.List["Node"]
    edges: typing.List["Edge"]

    def compact(
        self,
        *,
        match_node: typing.Optional[typing.Callable[["Node", "Node"], bool]],
        match_edge: typing.Optional[typing.Callable[["Edge", "Edge"], bool]],
    ) -> "Graph":
        new_nodes = []
        new_edges = []

        node_mappings: typing.Dict[Node, Node] = {}

        for node in self.nodes:
            found_match = False
            for other in new_nodes:
                if match_node(node, other):
                    found_match = True
                    node_mappings[node] = other
                    break
            if not found_match:
                new_nodes.append(node)
                node_mappings[node] = node

        for edge in self.edges:
            edge = Edge(
                id=edge.id,
                source=node_mappings[edge.source],
                target=node_mappings[edge.target],
                type=edge.type,
            )

            found_match = False
            for other in new_edges:
                if match_edge(edge, other):
                    found_match = True
                    break
            if not found_match:
                new_edges.append(edge)

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
    position: typing.Tuple[float, float] | None
    entity: meta_model.Entity

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "entity": self.entity.to_dict(),
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
            position=(d["position"]["x"], d["position"]["y"]),
            entity=meta_model.Entity.from_dict(d["entity"]),
        )

    def with_position(self, pos: typing.Tuple[float, float]) -> "Node":
        return Node(position=pos, entity=self.entity, name=self.name, id=self.id)


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
