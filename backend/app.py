import os
import pathlib
import typing

import flask
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS

import model.knowledge_graph as kg
import model.meta_model as mm
from model import match
from model.application_model import ApplicationModel
from parser.parse import parse_xml_file
from pipeline.llm_models import Models
from pipeline.steps.file_loader import FileLoader
from pipeline.steps.step import PromptCreation

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

application_models_directory = (
    pathlib.Path(__file__).parent.absolute() / "res" / "result" / "application-models"
)
application_models_directory.mkdir(exist_ok=True, parents=True)

model_instances_directory = (
    pathlib.Path(__file__).parent.absolute() / "res" / "result" / "model-instances"
)
model_instances_directory.mkdir(exist_ok=True, parents=True)

files_directory = pathlib.Path(__file__).parent.absolute() / "res" / "files"
files_directory.mkdir(exist_ok=True, parents=True)


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

    file_path = files_directory / file.filename
    with open(file_path, "wb") as f:
        file.save(f)
    parsed_files = loading_step.run([str(file_path.absolute())])
    if len(parsed_files) != 1:
        raise AssertionError("Parsing failed")
    file_content = parsed_files[0]

    application_model = ApplicationModel.load(application_model_path)

    prompt_step = PromptCreation()

    existing_graph: kg.Graph | None = None
    results_file_path = model_instances_directory / f"{meta_model_name}.json"
    if os.path.isfile(results_file_path):
        existing_graph = kg.Graph.load(results_file_path)
        existing_graph.save(str(results_file_path) + ".bkp")

    graph = prompt_step.run(
        model=Models.GPT_4o_2024_05_13.value,
        application_model=application_model,
        parsed_file=file_content,
        current_graph=existing_graph,
    )
    if existing_graph is not None:
        graph = existing_graph.merge(
            graph,
            match_edge=match.strict_edge_matcher,
            match_node=match.node_matcher(
                text_matcher=match.char_similarity, similarity_threshold=0.8
            ),
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


@app.route("/model/<name>/", methods=["GET"])
def load_meta_model(name: str):
    application_model_path = application_models_directory / f"{name}.json"
    print(application_model_path.absolute().__str__())
    if not os.path.isfile(application_model_path):
        flask.abort(404)
    return ApplicationModel.load(application_model_path).to_dict()


@app.route("/model/<name>/", methods=["PATCH"])
def patch_meta_model(name: str):
    print("....")

    new_elements = request.json

    print(new_elements)

    application_model_path = application_models_directory / f"{name}.json"
    application_model = ApplicationModel.load(application_model_path)

    entities: typing.Dict[str, mm.Entity] = {
        e.name: e for e in application_model.entities
    }
    for e in new_elements["entities"]:
        entity = mm.Entity.from_dict(e)
        entities[entity.name] = entity

    relations: typing.Dict[str, mm.Relation] = {
        r.name: r for r in application_model.relations
    }
    for r in new_elements["relations"]:
        relation = mm.Relation.from_dict(r)
        relations[relation.name] = relation

    application_model = ApplicationModel(
        list(entities.values()), list(relations.values())
    )

    application_model = application_model.layout()
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
