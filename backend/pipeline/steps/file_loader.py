import os
import traceback
import typing

import pypdf
import pypdf.errors

from pipeline.steps.step import BasePipelineStep
from pipeline.steps.utils import ParsedFile


class FileLoader(BasePipelineStep):
    SUPPORTED_FILE_ENDINGS = [".pdf"]

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
    def parse_pdf_file(file_path: str) -> typing.Optional[ParsedFile]:
        try:
            reader = pypdf.PdfReader(file_path, strict=False)
        except pypdf.errors.PdfReadError:
            print(traceback.format_exc())
            print(f'The file {file_path} is not a PDF."')
            return None
        number_of_pages = len(reader.pages)
        text = "\n".join(p.extract_text() for p in reader.pages)
        return ParsedFile(
            name=FileLoader.extract_filename(file_path),
            number_of_pages=number_of_pages,
            content=text,
        )

    def run(self, files: typing.List[str]) -> typing.List[ParsedFile]:
        parsed_files = []
        for file in files:
            assert os.path.isfile(file), f"The required file {file} does not exist"
            parsed = self.parse_pdf_file(file)
            if parsed is None:
                continue
            parsed_files.append(parsed)

        return parsed_files

    @staticmethod
    def get_name() -> str:
        return "FileLoader"
