import json

from model.application_model import get_dummy_application_model
from pipeline.llm_models import Models
from pipeline.steps.file_loader import FileLoader
from pipeline.steps.step import PromptCreation

if __name__ == '__main__':
    test_file = r'D:\Workspace\risk-aware-bpm\backend\files\SMT-09-1003_revA2_(Industrial_Vacuum_Chamber_Manual).pdf'
    result_file = r'result/extracted_information.json'
    loading_step = FileLoader()
    file_content = loading_step.run([test_file])[0]

    prompt_step = PromptCreation()
    entities, relations = prompt_step.run(model=Models.GPT_3_5.value,
                                          application_model=get_dummy_application_model(),
                                          parsed_file=file_content)

    results = {
        "nodes": [e.to_dict() for e in entities],
        "edges": [r.to_dict() for r in relations],
    }

    with open(result_file, 'w', encoding='utf8') as f:
        json.dump(results, f, indent=4)

    exit(-1)
