import os
import pathlib

import flask
from flask import Flask, request
from flask_cors import CORS

import model.knowledge_graph as kg
from model import match
from model.application_model import ApplicationModel
from model.meta_model import Entity, Relation
from parser.parse import parse_xml_file
from pipeline.llm_models import Models
from pipeline.steps.file_loader import FileLoader
from pipeline.steps.step import PromptCreation

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

application_models_directory = (
    pathlib.Path(__file__).parent.absolute() / "result" / "application-models"
)
application_models_directory.mkdir(exist_ok=True)

model_instances_directory = (
    pathlib.Path(__file__).parent.absolute() / "result" / "model-instances"
)
model_instances_directory.mkdir(exist_ok=True)


@app.route("/graph/", methods=["GET"])
def list_knowledge_graphs():
    graph_files = os.listdir(model_instances_directory)
    graphs = [os.path.splitext(p) for p in graph_files]
    return [name for name, ext in graphs if ext == ".json"]


@app.route("/graph/<meta_model_name>/", methods=["GET"])
def load_knowledge_graph(meta_model_name: str):
    results_file_path = model_instances_directory / f"{meta_model_name}.json"
    if not os.path.isfile(results_file_path):
        flask.abort(404)
    return kg.Graph.load(results_file_path).to_dict()


@app.route("/graph/<meta_model_name>/", methods=["DELETE"])
def delete_graph(meta_model_name: str):
    results_file_path = model_instances_directory / f"{meta_model_name}.json"
    if os.path.isfile(results_file_path):
        os.replace(
            results_file_path,
            str(results_file_path) + ".bkp",
        )
    return {"success": True}


@app.route("/graph/<meta_model_name>/layout/", methods=["GET"])
def layout_graph(meta_model_name: str):
    results_file_path = model_instances_directory / f"{meta_model_name}.json"
    graph = kg.Graph.load(results_file_path)
    graph = graph.layout()
    graph.save(results_file_path)
    return {"success": True}


@app.route("/graph/extract/", methods=["POST"])
def extract_knowledge_graph():
    file = request.files["file"]

    meta_model_name = request.form.get("metaModel")
    application_model_path = application_models_directory / f"{meta_model_name}.json"

    loading_step = FileLoader()

    with open("file.pdf", "wb") as f:
        file.save(f)
    parsed_files = loading_step.run(["file.pdf"])
    if len(parsed_files) != 1:
        raise AssertionError("Parsing failed")
    file_content = parsed_files[0]

    application_model = ApplicationModel.load(application_model_path)

    prompt_step = PromptCreation()
    graph = prompt_step.run(
        model=Models.GPT_4o_2024_05_13.value,
        application_model=application_model,
        parsed_file=file_content,
    )

    results_file_path = model_instances_directory / f"{meta_model_name}.json"
    if os.path.isfile(results_file_path):
        existing_graph = kg.Graph.load(results_file_path)
        existing_graph.save(str(results_file_path) + ".bkp")
        graph = existing_graph.merge(
            graph,
            match_edge=match.strict_edge_matcher,
            match_node=match.node_similarity_matcher(similarity_threshold=0.8),
        )

    graph = graph.layout()
    graph.save(results_file_path)
    return {"success": True, "graph": graph.to_dict()}


@app.route("/model/extract", methods=["POST"])
def import_meta_model():
    file = request.files["file"]
    data = request.json
    model_name = data["name"]
    application_model_path = application_models_directory / f"{model_name}.json"
    application_model = parse_xml_file(file.stream)
    application_model.layout()
    application_model.save(application_model_path)

    return {"success": True}


@app.route("/model/", methods=["GET"])
def list_meta_models():
    meta_model_files = os.listdir(application_models_directory)
    meta_models = [os.path.splitext(p) for p in meta_model_files]
    return [name for name, ext in meta_models if ext == ".json"]


@app.route("/model/<name>", methods=["GET"])
def load_meta_model(name: str):
    application_model_path = application_models_directory / f"{name}.json"
    if not os.path.isfile(application_model_path):
        flask.abort(404)
    return ApplicationModel.load(application_model_path).to_dict()


@app.route("/model/<name>", methods=["PATCH"])
def patch_meta_model(name: str):
    new_elements = request.json

    application_model_path = application_models_directory / f"{name}.json"
    application_model = ApplicationModel.load(application_model_path)

    for e in new_elements["entities"]:
        entity = Entity.from_dict(e)
        is_new = True
        for other in application_model.entities:
            if other.name == entity.name:
                other.description = entity.description
                other.aspect = entity.aspect
                other.position = entity.position
                is_new = False
                break
        if is_new:
            application_model.entities.append(entity)

    for r in new_elements["relations"]:
        relation = Relation.from_dict(r)
        is_new = True
        for other in application_model.relations:
            if other.name == relation.name:
                other.description = relation.description
                other.source = application_model.get_entity_by_name(
                    relation.source.name
                )
                other.target = application_model.get_entity_by_name(
                    relation.target.name
                )
                is_new = False
                print(f"Patched relation: {other.to_dict()}")
                break
        if is_new:
            print("Added new relation")
            application_model.relations.append(relation)

    application_model.layout()
    application_model.save(application_model_path)

    return {
        "success": True,
    }


@app.route("/model/<name>/aspects", methods=["GET"])
def list_aspects(name: str):
    application_model_path = application_models_directory / f"{name}.json"
    application_model = ApplicationModel.load(application_model_path)
    all_aspects = [e.aspect for e in application_model.entities]
    aspects_by_name = {}
    for a in all_aspects:
        if a.name in aspects_by_name:
            continue
        aspects_by_name[a.name] = a.to_dict()
    return list(aspects_by_name.values())
