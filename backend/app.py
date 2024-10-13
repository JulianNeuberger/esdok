import os
import pathlib

import flask
from flask import Flask, request
from flask_cors import CORS, cross_origin

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

application_model_path = (
    pathlib.Path(__file__).parent.absolute() / "result" / "metamodel.json"
)
results_file_path = (
    pathlib.Path(__file__).parent.absolute() / "result" / "extracted_information.json"
)


@app.route("/graph/", methods=["GET"])
def load_knowledge_graph():
    if not os.path.isfile(results_file_path):
        flask.abort(404)
    return kg.Graph.load(results_file_path).to_dict()


@app.route("/graph/", methods=["DELETE"])
def delete_graph():
    if os.path.isfile(results_file_path):
        os.replace(
            results_file_path,
            str(results_file_path) + ".bkp",
        )
    return {"success": True}


@app.route("/graph/layout/", methods=["GET"])
def layout_graph():
    graph = kg.Graph.load(results_file_path)
    graph = graph.layout()
    graph.save(results_file_path)
    return {"success": True}


@app.route("/graph/extract/", methods=["POST"])
def extract_knowledge_graph():
    file = request.files["file"]
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
    application_model = parse_xml_file(file.stream)
    application_model.layout()
    application_model.save(application_model_path)

    return {"success": True}


@app.route("/model/", methods=["GET"])
def load_meta_model():
    # todo: load from database / file
    if not os.path.isfile(application_model_path):
        flask.abort(404)
    return ApplicationModel.load(application_model_path).to_dict()


@app.route("/model/", methods=["PATCH"])
def patch_meta_model():
    new_elements = request.json

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


@app.route("/model/aspect", methods=["GET"])
def get_aspects():
    application_model = ApplicationModel.load(application_model_path)
    all_aspects = [e.aspect for e in application_model.entities]
    aspects_by_name = {}
    for a in all_aspects:
        if a.name in aspects_by_name:
            continue
        aspects_by_name[a.name] = a.to_dict()
    return list(aspects_by_name.values())
