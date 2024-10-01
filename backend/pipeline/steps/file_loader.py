import typing
import os

from pypdf import PdfReader
from pipeline.steps.step import BasePipelineStep
from pipeline.steps.utils import ParsedFile


class FileLoader(BasePipelineStep):
    SUPPORTED_FILE_ENDINGS = [
        '.pdf'
    ]

    @staticmethod
    def is_of_type(file_path, file_ending: str):
        """
        This function checks if the file is of a particular type.

        Args:
            file_path (str): The path to the file.
            file_ending (str): Type of the file

        Returns:
            bool: True if it's of the given type, False otherwise.
        """
        _, file_extension = os.path.splitext(file_path)
        return file_extension.lower() == file_ending

    @staticmethod
    def extract_filename(file_path):
        """
        This function extracts the file name without the extension from the path.

        Args:
            file_path (str): The path to the file.

        Returns:
            str: The file name without the extension.
        """
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        return file_name

    @staticmethod
    def parse_pdf_file(file_path: str) -> ParsedFile:
        assert FileLoader.is_of_type(file_path, '.pdf') is True, f'The file {file_path} is not a PDF."'

        reader = PdfReader(file_path)
        number_of_pages = len(reader.pages)
        text = ''
        for i, _ in enumerate(reader.pages):
            text = text + reader.pages[i].extract_text()
        return ParsedFile(name=FileLoader.extract_filename(file_path), number_of_pages=number_of_pages, content=text)

    def run(self, files: typing.List[str]) -> typing.List[ParsedFile]:
        parsed_files = []
        for file in files:
            assert os.path.isfile(file), f'The required file {file} does not exist'
            parsed_files.append(self.parse_pdf_file(file))

        return parsed_files

    @staticmethod
    def get_name() -> str:
        return 'FileLoader'
