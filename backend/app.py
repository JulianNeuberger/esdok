import os
import pathlib

import flask
from flask import Flask, request
from flask_cors import CORS

import model.knowledge_graph as kg
from model.application_model import get_dummy_application_model
from model.meta_model import Entity, Relation
from pipeline.llm_models import Models
from pipeline.steps.file_loader import FileLoader
from pipeline.steps.step import PromptCreation

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

application_model = get_dummy_application_model()
results_file_path = (
    pathlib.Path(__file__).parent.absolute() / "result" / "extracted_information.json"
)


@app.route("/graph/", methods=["GET"])
def load_knowledge_graph():
    if not os.path.isfile(results_file_path):
        flask.abort(404)
    return kg.Graph.load(results_file_path)


@app.route("/graph/", methods=["DELETE"])
def delete_graph():
    if os.path.isfile(results_file_path):
        os.replace(
            results_file_path,
            str(results_file_path) + ".bkp",
        )


@app.route("/graph/extract", methods=["POST"])
def extract_knowledge_graph():
    file = request.files["file"]
    loading_step = FileLoader()

    with open("file.pdf", "wb") as f:
        file.save(f)
        parsed_files = loading_step.run([f.name])
        if len(parsed_files) != 1:
            raise AssertionError("Parsing failed")
        file_content = parsed_files[0]

    prompt_step = PromptCreation()
    graph = prompt_step.run(
        model=Models.GPT_4o_2024_05_13.value,
        application_model=application_model,
        parsed_file=file_content,
    )

    if os.path.isfile(results_file_path):
        existing_graph = kg.Graph.load(results_file_path)
        existing_graph.save(str(results_file_path) + ".bkp")
        graph = existing_graph.merge(graph)

    graph.save(results_file_path)
    return {"success": True, "graph": graph}


@app.route("/model/", methods=["GET"])
def load_meta_model():
    # todo: load from database / file
    return application_model.to_dict()


@app.route("/model/", methods=["PATCH"])
def patch_meta_model():
    print(request)
    new_elements = request.json
    print(new_elements)
    new_entities = [Entity.from_dict(e) for e in new_elements["entities"]]
    new_relations = [Relation.from_dict(e) for e in new_elements["relations"]]
    application_model.entities.extend(new_entities)
    application_model.relations.extend(new_relations)
    return {
        "success": True,
        "newRelations": len(new_relations),
        "newEntities": len(new_entities),
    }


@app.route("/model/aspect", methods=["GET"])
def get_aspects():
    all_aspects = [e.aspect for e in application_model.entities]
    aspects_by_name = {}
    for a in all_aspects:
        if a.name in aspects_by_name:
            continue
        aspects_by_name[a.name] = a
    return list(aspects_by_name.values())
