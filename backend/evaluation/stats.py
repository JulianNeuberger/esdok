import os
import pathlib


from model import knowledge_graph as kg

specific_prompt_path = (
    pathlib.Path(__file__).parent.parent.absolute()
    / "res"
    / "experiments"
    / "pet"
    / "specific-prompt"
)

spec_num_entities = []
spec_num_relations = []
for file in os.listdir(specific_prompt_path):
    if not file.startswith("graph-"):
        continue

    graph = kg.Graph.load(specific_prompt_path / file)
    spec_num_entities.append(len(graph.nodes))
    spec_num_relations.append(len(graph.edges))

print("spec entities: ", f"{sum(spec_num_entities) / len(spec_num_entities): .2f}")
print("spec relations:", f"{sum(spec_num_relations) / len(spec_num_relations): .2f}")

generic_prompt_path = (
    pathlib.Path(__file__).parent.parent.absolute()
    / "res"
    / "experiments"
    / "pet"
    / "generic-method"
)

gen_num_entities = []
gen_num_relations = []
for file in os.listdir(generic_prompt_path):
    graph = kg.Graph.load(generic_prompt_path / file)
    gen_num_entities.append(len(graph.nodes))
    gen_num_relations.append(len(graph.edges))

print("gen. entities: ", f"{sum(gen_num_entities) / len(gen_num_entities): .2f}")
print("gen. relations:", f"{sum(gen_num_relations) / len(gen_num_relations): .2f}")
