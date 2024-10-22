import pathlib

from model.application_model import get_biffls_application_model

if __name__ == "__main__":
    application_models_directory = (
        pathlib.Path(__file__).parent.absolute() / "result" / "application-models"
    )
    application_models_directory.mkdir(exist_ok=True)
    application_model = get_biffls_application_model()
    application_model.save(application_models_directory / "simple.json")
