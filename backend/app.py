import json
import os
import pathlib

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r'/*': {"origins": '*'}})


@app.route('/graph/', methods=['GET'])
def load_knowledge_graph():
    results_file_path = pathlib.Path(__file__).parent.absolute() / "result" / "extracted_information.json"
    if not os.path.isfile(results_file_path):
        # todo: review this. would an error be better?
        return {}
    with open(results_file_path) as f:
        graph = json.load(f)
        return graph
