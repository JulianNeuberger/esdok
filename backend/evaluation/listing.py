import pathlib
import typing

import model.knowledge_graph as kg


def get_entity_list(graph: kg.Graph, roots: typing.List[kg.Node]) -> typing.List[kg.Node]:
    nodes = set()
    for e in graph.edges:
        if e.source in roots:
            nodes.add(e.target)
        if e.target in roots:
            nodes.add(e.source)
    return list(nodes)


def get_entities_by_type(graph: kg.Graph, entity_name: str) -> typing.List[kg.Node]:
    return [n for n in graph.nodes if n.entity.name == entity_name]


def get_root_nodes(graph: kg.Graph) -> typing.List[kg.Node]:
    num_incoming_edges: typing.Dict[kg.Node, int] = {
        n: 0 for n in graph.nodes
    }
    for e in graph.edges:
        # num_incoming_edges[e.target] += 1
        num_incoming_edges[e.source] += 1

    ret = []
    for n, i in num_incoming_edges.items():
        if i > 0:
            continue
        ret.append(n)
    return ret


def bfs_traversal(graph: kg.Graph, roots: typing.List[kg.Node], observer: typing.Callable[[kg.Node, typing.List[kg.Node], int], None]) -> None:
    queue: typing.List[kg.Node] = []
    explored: typing.Set[kg.Node] = set()
    parents: typing.Dict[kg.Node, kg.Node] = {}
    for r in roots:
        queue.append(r)
        explored.add(r)
        observer(r, [], 0)
    while len(queue) > 0:
        v = queue.pop(0)
        for e in graph.edges:
            if e.target != v:
                continue
            w = e.source
            if w in explored:
                continue
            path = [v]
            while path[0] in parents:
                path = [parents[path[0]]] + path
            observer(w, path, len(path))
            parents[w] = v
            explored.add(w)
            queue.append(w)


def print_level(nodes: typing.List[kg.Node], tree: typing.Dict[kg.Node, typing.Dict[kg.Node, typing.Dict]], level: int) -> typing.List[str]:
    ret = []
    for node in nodes:
        if level == 0:
            ret.append(f"├── {node.name} ({node.entity.name})")
        else:
            ret.append(f"| {'   ' * level} └── {node.name} ({node.entity.name})")
        sub_tree = tree[node]
        if len(sub_tree) > 0:
            ret += print_level(list(sub_tree.keys()), sub_tree, level + 1)

    return ret


if __name__ == "__main__":

    def main():
        graph_path = (
            pathlib.Path(__file__).parent.parent
            / "res"
            / "result"
            / "model-instances"
            / "simple.json"
        )
        # root_name = "vacuum chamber"
        # root_type = "Product"
        graph = kg.Graph.load(graph_path)
        # roots = []
        # for n in graph.nodes:
        #     if n.entity.name != root_type:
        #         continue
        #     if root_name.lower() not in n.name.lower():
        #         continue
        #     roots.append(n)
        # assert len(roots) > 0
        # entities = get_entity_list(graph, roots)
        #
        # entities_by_type = {}
        # for e in entities:
        #     if e.entity.name not in entities_by_type:
        #         entities_by_type[e.entity.name] = []
        #     entities_by_type[e.entity.name].append(e)
        #
        # focused_csv_path = (
        #     pathlib.Path(__file__).parent.parent
        #     / "res"
        #     / "experiments"
        #     / "focused_list_3dprinter.csv"
        # )
        #
        # with open(focused_csv_path, "w") as focused_csv:
        #     for t, es in entities_by_type.items():
        #         for e in es:
        #             focused_csv.write(f'"{t}";"{e.name}"\n')

        tree: typing.Dict[kg.Node, typing.Dict[kg.Node, typing.Dict]] = {}

        def obs(node, path, level):
            cur = tree
            for cur_node in path:
                cur = cur[cur_node]
            cur[node] = {}
        roots = list(set(get_entities_by_type(graph, "Product") + get_root_nodes(graph)))
        bfs_traversal(graph, roots, obs)

        complete_txt_path = (
            pathlib.Path(__file__).parent.parent
            / "res"
            / "experiments"
            / "complete_list_3dprinter.txt"
        )
        with open(complete_txt_path, "w", encoding="utf8") as complete_txt_file:
            lines = print_level(list(tree.keys()), tree, 0)
            complete_txt_file.write("\n".join(lines))


    main()
