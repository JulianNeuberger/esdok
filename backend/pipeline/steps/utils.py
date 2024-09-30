import dataclasses


@dataclasses.dataclass
class ParsedFile:
    name: str
    number_of_pages: int
    content: str
