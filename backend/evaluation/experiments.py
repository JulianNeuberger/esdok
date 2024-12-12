import json
import pathlib
import typing

from dotenv import load_dotenv

from evaluation import pet, metrics
from model import knowledge_graph as kg
from model import meta_model as mm
from model.application_model import ApplicationModel
from pipeline.llm_models import Models
from pipeline.steps.step import PromptCreation
from pipeline.steps.utils import ParsedFile


def pet_document_to_graph(doc: pet.PetDocument) -> kg.Graph:
    mentions: typing.Dict[str, kg.Node] = {}
    nodes: typing.List[kg.Node] = []

    entity: pet.PetEntity
    for i, entity in enumerate(doc.entities):
        if len(entity.mention_indices) == 0:
            continue

        mention_candidates = [doc.mentions[m_idx] for m_idx in entity.mention_indices]
        mention_candidates = sorted(
            mention_candidates,
            key=lambda m: len(m.token_document_indices),
            reverse=True,
        )
        mention = mention_candidates[0]

        node = kg.Node(
            id=str(i),
            name=mention.text(doc),
            source=kg.DataSource(file=doc.name, page_start=1, page_end=1),
            position=(0, 0),
            entity=mm.Entity(
                name=mention.type,
                description="",
                aspect=mm.Aspect(
                    name="",
                    text_color=mm.Color(0, 0, 0),
                    shape_color=mm.Color(0, 0, 0),
                    shape=mm.Shape.RECTANGLE,
                ),
                position=mm.Position(0, 0),
            ),
        )
        nodes.append(node)

        for mention_idx in entity.mention_indices:
            mentions[str(mention_idx)] = node

    edges: typing.List[kg.Edge] = []
    relation: pet.PetRelation
    for i, relation in enumerate(doc.relations):
        edges.append(
            kg.Edge(
                id=str(i),
                type=relation.type,
                source=mentions[str(relation.head_mention_index)],
                target=mentions[str(relation.tail_mention_index)],
            )
        )

    return kg.Graph(nodes=list(nodes), edges=edges)


def run_pet_experiments():
    document_path = (
        pathlib.Path(__file__).parent.parent.absolute()
        / "res"
        / "experiments"
        / "pet"
        / "all.new.jsonl"
    )
    documents = pet.NewPetFormatImporter(document_path).do_import()

    application_model_path = (
        pathlib.Path(__file__).parent.parent.absolute()
        / "res"
        / "result"
        / "application-models"
        / "pet.json"
    )

    graph_folder = (
        pathlib.Path(__file__).parent.parent.absolute()
        / "res"
        / "experiments"
        / "pet"
        / "generic-method"
    )
    graph_folder.mkdir(exist_ok=True, parents=True)

    model = Models.GPT_4o_2024_05_13.value

    spec_metrics = {"gde": [], "p": [], "r": [], "f1": [], "f2": []}

    generic_metrics = {"gde": [], "p": [], "r": [], "f1": [], "f2": []}

    for document in documents:
        print(f"{document.name} ------------------------- ")

        expected_graph_path = (
            pathlib.Path(__file__).parent.parent.absolute()
            / "res"
            / "experiments"
            / "pet"
            / "expected"
            / f"{document.id}.json"
        )
        expected_graph_path.parent.mkdir(exist_ok=True, parents=True)
        expected_graph = pet_document_to_graph(document)
        expected_graph.save(expected_graph_path)

        specific_prompt_path = (
            pathlib.Path(__file__).parent.parent.absolute()
            / "res"
            / "experiments"
            / "pet"
            / "specific-prompt"
            / f"{document.id}.json"
        )
        specific_prompt_path.parent.mkdir(exist_ok=True, parents=True)
        specific_prompt_graph = pet_document_to_graph(
            pet.NewPetFormatImporter(specific_prompt_path).do_import()[0]
        )
        specific_prompt_graph.save(
            specific_prompt_path.parent / f"graph-{document.id}.json"
        )

        if not (graph_folder / f"{document.name}.json").exists():
            application_model = ApplicationModel.load(application_model_path)
            prompt_step = PromptCreation()
            file = ParsedFile(
                name=document.name, number_of_pages=1, content=document.text
            )
            generic_method_graph = prompt_step.run(
                model=model,
                application_model=application_model,
                parsed_file=file,
                current_graph=None,
            )
            generic_method_graph.save(graph_folder / f"{document.name}.json")
        else:
            generic_method_graph = kg.Graph.load(graph_folder / f"{document.name}.json")

        specific_stats = metrics.get_stats(
            predicted_graph=specific_prompt_graph,
            reference_graph=expected_graph,
            threshold=0.2,
        )

        generic_stats = metrics.get_stats(
            predicted_graph=generic_method_graph,
            reference_graph=expected_graph,
            threshold=0.2,
            verbose=True,
        )

        spec_metrics["r"].append(specific_stats.recall)
        spec_metrics["p"].append(specific_stats.precision)
        spec_metrics["f1"].append(specific_stats.f1)
        spec_metrics["f2"].append(specific_stats.f_beta(2))

        generic_metrics["r"].append(generic_stats.recall)
        generic_metrics["p"].append(generic_stats.precision)
        generic_metrics["f1"].append(generic_stats.f1)
        generic_metrics["f2"].append(generic_stats.f_beta(2))

        specific_prompt_gde = specific_prompt_graph.graph_edit_distance(
            expected_graph, timeout_seconds=5 * 60
        )
        generic_method_gde = generic_method_graph.graph_edit_distance(
            expected_graph, timeout_seconds=5 * 60
        )

        spec_metrics["gde"].append(specific_prompt_gde)
        generic_metrics["gde"].append(generic_method_gde)

        print(
            f"specific --- "
            f"p: {specific_stats.precision:.2f}, "
            f"r: {specific_stats.recall:.2f}, "
            f"f1: {specific_stats.f1:.2f}"
        )
        print(
            f"generic  --- "
            f"p: {generic_stats.precision:.2f}, "
            f"r: {generic_stats.recall:.2f}, "
            f"f1: {generic_stats.f1:.2f}"
        )
        print()
        print()

    print("-------------------")
    print(
        "Special Prompt:",
        f"p: {sum(spec_metrics['p']) / len(spec_metrics['p']):.2f}",
        f"r: {sum(spec_metrics['r']) / len(spec_metrics['r']):.2f}",
        f"f1: {sum(spec_metrics['f1']) / len(spec_metrics['f1']):.2f}",
        f"f2: {sum(spec_metrics['f2']) / len(spec_metrics['f2']):.2f}",
    )
    print(
        "Generic Method:",
        f"p: {sum(generic_metrics['p']) / len(generic_metrics['p']):.2f}",
        f"r: {sum(generic_metrics['r']) / len(generic_metrics['r']):.2f}",
        f"f1: {sum(generic_metrics['f1']) / len(generic_metrics['f1']):.2f}",
        f"f2: {sum(generic_metrics['f2']) / len(generic_metrics['f2']):.2f}",
    )

    results_file = (
        pathlib.Path(__file__).parent / "res" / "experiments" / "pet" / "results.json"
    )
    results_file.parent.mkdir(exist_ok=True, parents=True)
    with open(results_file, "w") as f:
        json.dump(
            {
                "specific_metrics": spec_metrics,
                "generic_metrics": generic_metrics,
            },
            f,
        )


if __name__ == "__main__":
    load_dotenv()
    run_pet_experiments()
