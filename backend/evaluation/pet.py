import abc
import collections
import dataclasses
import json
import pathlib
import typing


@dataclasses.dataclass
class DocumentBase:
    id: str
    text: str

    def __add__(self, other):
        raise NotImplementedError()

    def copy(self, clear: typing.List[str]):
        raise NotImplementedError()


TDocument = typing.TypeVar("TDocument", bound=DocumentBase)


class BaseImporter(abc.ABC, typing.Generic[TDocument]):
    def do_import(self) -> typing.List[TDocument]:
        raise NotImplementedError()


@dataclasses.dataclass(frozen=True, eq=True)
class HasType(abc.ABC):
    type: str


class HasCustomMatch:
    def match(self, other: object) -> bool:
        raise NotImplementedError()


TMention = typing.TypeVar("TMention", bound=HasType)


@dataclasses.dataclass
class HasMentions(abc.ABC, typing.Generic[TMention]):
    mentions: typing.List[TMention]


TRelation = typing.TypeVar("TRelation", bound=HasType)


@dataclasses.dataclass
class HasRelations(abc.ABC, typing.Generic[TRelation]):
    relations: typing.List[TRelation]


class SupportsPrettyDump(abc.ABC, typing.Generic[TDocument]):
    def pretty_dump(self, document: TDocument) -> str:
        raise NotImplementedError()


@dataclasses.dataclass
class PetDocument(DocumentBase, HasMentions["PetMention"], HasRelations["PetRelation"]):
    category: str
    name: str
    tokens: typing.List["PetToken"]
    entities: typing.List["PetEntity"]

    def get_mention_for_token(self, token: "PetToken") -> typing.Optional["PetMention"]:
        for m in self.mentions:
            if token.index_in_document in m.token_document_indices:
                return m
        return None

    def token_index_in_sentence(self, token: "PetToken") -> int:
        return self.sentences[token.sentence_index].index(token)

    def tokens_for_character_indices(
        self, start: int, stop: int
    ) -> typing.List["PetToken"]:
        cur_start = 0
        tokens = []
        for t in self.tokens:
            cur_stop = cur_start + len(t.text)
            if cur_start >= start and cur_stop <= stop:
                tokens.append(t)
            # +1 to account for white space
            cur_start = cur_stop + 1
            if cur_start > stop:
                break
        return tokens

    def get_relations_by_mention(
        self, mention_index: int, only_head: bool = False, only_tail: bool = False
    ) -> typing.List["PetRelation"]:
        ret = []
        for r in self.relations:
            if r.head_mention_index == mention_index and not only_tail:
                ret.append(r)
            elif r.tail_mention_index == mention_index and not only_head:
                ret.append(r)
        return ret

    def relation_exists(self, head_index: int, tail_index: int) -> bool:
        for r in self.relations:
            if (
                r.head_mention_index == head_index
                and r.tail_mention_index == tail_index
            ):
                return True
        return False

    @property
    def sentences(self) -> typing.List[typing.List["PetToken"]]:
        ret = []
        last_id = None
        for token in self.tokens:
            if token.sentence_index != last_id:
                last_id = token.sentence_index
                ret.append([])
            ret[-1].append(token)
        return ret

    def copy(self, clear: typing.List[str]) -> "PetDocument":
        assert all(c in ["relations", "mentions", "entities"] for c in clear)
        return PetDocument(
            name=self.name,
            text=self.text,
            id=self.id,
            category=self.category,
            tokens=[t.copy() for t in self.tokens],
            mentions=[] if "mentions" in clear else [m.copy() for m in self.mentions],
            relations=(
                [] if "relations" in clear else [r.copy() for r in self.relations]
            ),
            entities=[] if "entities" in clear else [e.copy() for e in self.entities],
        )

    def merge(self, other: "PetDocument"):
        """
        Merges the document "other" into this document, i.e., concatenating
        texts, tokens, etc.

        Parameters
        ----------
        other: PetDocument the document to merge into this document

        Returns a new instance of PetDocument containing the result of the merge
        -------

        """
        token_offset = len(self.tokens)
        sentence_offset = len(self.sentences)
        mention_offset = len(self.mentions)

        new_tokens = [t.copy() for t in self.tokens]
        for t in other.tokens:
            t = PetToken(
                text=t.text,
                pos_tag=t.pos_tag,
                index_in_document=t.index_in_document + token_offset,
                sentence_index=t.sentence_index + sentence_offset,
            )
            new_tokens.append(t)

        new_mentions = [m.copy() for m in self.mentions]
        for m in other.mentions:
            m = PetMention(
                type=m.type,
                token_document_indices=tuple(
                    i + token_offset for i in m.token_document_indices
                ),
            )
            new_mentions.append(m)

        new_entities = [e.copy() for e in self.entities]
        for e in other.entities:
            e = PetEntity(
                mention_indices=tuple(i + mention_offset for i in e.mention_indices)
            )
            new_entities.append(e)

        new_relations = [r.copy() for r in self.relations]
        for r in other.relations:
            r = PetRelation(
                type=r.type,
                head_mention_index=r.head_mention_index + mention_offset,
                tail_mention_index=r.tail_mention_index + mention_offset,
            )
            new_relations.append(r)

        return PetDocument(
            id=self.id + "_" + other.id,
            name=self.name + "_" + other.name,
            text=self.text + " " + other.text,
            category=self.category + " " + other.category,
            tokens=new_tokens,
            mentions=new_mentions,
            entities=new_entities,
            relations=new_relations,
        )


@dataclasses.dataclass(frozen=True)
class PetMention(HasType, SupportsPrettyDump[PetDocument]):
    token_document_indices: typing.Tuple[int, ...]

    def copy(self) -> "PetMention":
        return PetMention(
            type=self.type.strip().lower(),
            token_document_indices=tuple(i for i in self.token_document_indices),
        )

    def text(self, document: "PetDocument") -> str:
        return " ".join([document.tokens[i].text for i in self.token_document_indices])

    def pretty_dump(self, document: "PetDocument") -> str:
        return f"{self.type}, '{self.text(document)}', {self.token_document_indices}"

    def get_tokens(self, doc: "PetDocument") -> typing.List["PetToken"]:
        return [doc.tokens[i] for i in self.token_document_indices]

    def get_sentence_index(self, doc: "PetDocument") -> int:
        return doc.tokens[self.token_document_indices[0]].sentence_index

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, PetMention):
            return False
        if self.type.lower() != o.type.lower():
            return False
        return sorted(self.token_document_indices) == sorted(o.token_document_indices)

    def __hash__(self) -> int:
        element_counts = collections.Counter(self.token_document_indices)
        cur = hash(frozenset(element_counts.items()))
        cur += hash(self.type.lower())
        return cur

    def match(self, o: object):
        if not isinstance(o, PetMention):
            return False
        if self.type.lower() != o.type.lower():
            return False
        if any([i in o.token_document_indices for i in self.token_document_indices]):
            return True
        return False


@dataclasses.dataclass(frozen=True)
class PetEntity(SupportsPrettyDump[PetDocument]):
    mention_indices: typing.Tuple[int, ...]

    def copy(self) -> "PetEntity":
        return PetEntity(mention_indices=tuple(i for i in self.mention_indices))

    def get_tag(self, document: "PetDocument") -> str:
        tags = set(document.mentions[i].type for i in self.mention_indices)
        if len(tags) > 1:
            print(f"Entity has mentions of mixed ner tags: {tags}")
        return list(tags)[0]

    def pretty_dump(self, document: PetDocument) -> str:
        formatted_mentions = [
            f"{i}: '{m.text(document)}' ({m.token_document_indices})"
            for i, m in [(i, document.mentions[i]) for i in self.mention_indices]
        ]
        return ", ".join(formatted_mentions)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, PetEntity):
            return False
        if len(self.mention_indices) != len(o.mention_indices):
            return False
        return sorted(self.mention_indices) == sorted(o.mention_indices)

    def __hash__(self):
        element_counts = collections.Counter(self.mention_indices)
        return hash(frozenset(element_counts.items()))


@dataclasses.dataclass(frozen=True, eq=True)
class PetRelation(HasType, SupportsPrettyDump[PetDocument]):
    head_mention_index: int
    tail_mention_index: int

    def copy(self) -> "PetRelation":
        return PetRelation(
            head_mention_index=self.head_mention_index,
            tail_mention_index=self.tail_mention_index,
            type=self.type.lower().strip(),
        )

    def pretty_dump(self, document: PetDocument) -> str:
        head = document.mentions[self.head_mention_index].pretty_dump(document)
        tail = document.mentions[self.tail_mention_index].pretty_dump(document)
        return f"{head} -{self.type}-> {tail}"


@dataclasses.dataclass(frozen=True, eq=True)
class PetToken:
    text: str
    index_in_document: int
    pos_tag: str
    sentence_index: int

    def char_indices(self, document: PetDocument) -> typing.Tuple[int, int]:
        start = 0
        for i, other in enumerate(document.tokens):
            if other == self:
                return start, start + len(self.text)
            start += len(other.text) + 1
        raise AssertionError("Token text not found in document")

    def copy(self) -> "PetToken":
        return PetToken(
            text=self.text,
            index_in_document=self.index_in_document,
            pos_tag=self.pos_tag,
            sentence_index=self.sentence_index,
        )


class PetJsonExporter:
    def __init__(self, path: str):
        self._dict_exporter = PetDictExporter()
        self._path = path

    def export(self, documents: typing.List[PetDocument]):
        json_lines = []
        for document in documents:
            document_as_json = json.dumps(self._dict_exporter.export_document(document))
            json_lines.append(document_as_json)
        with open(self._path, "w", encoding="utf8") as f:
            f.write("\n".join(json_lines))


class PetDictExporter:
    def export_document(self, document: PetDocument) -> typing.Dict:
        return {
            "text": document.text,
            "name": document.name,
            "id": document.id,
            "category": document.category,
            "tokens": list(map(self.export_token, document.tokens)),
            "mentions": list(map(self.export_mention, document.mentions)),
            "entities": list(map(self.export_entity, document.entities)),
            "relations": list(map(self.export_relation, document.relations)),
        }

    def export_token(self, token: PetToken) -> typing.Dict:
        return {
            "text": token.text,
            "indexInDocument": token.index_in_document,
            "posTag": token.pos_tag,
            "sentenceIndex": token.sentence_index,
        }

    def export_mention(self, mention: PetMention) -> typing.Dict:
        return {
            "type": mention.type,
            "tokenDocumentIndices": list(mention.token_document_indices),
        }

    def export_relation(self, relation: PetRelation) -> typing.Dict:
        return {
            "headMentionIndex": relation.head_mention_index,
            "tailMentionIndex": relation.tail_mention_index,
            "type": relation.type,
        }

    def export_entity(self, entity: PetEntity) -> typing.Dict:
        return {"mentionIndices": entity.mention_indices}


class NewPetFormatImporter(BaseImporter[PetDocument]):
    class DictImporter:
        @staticmethod
        def read_tokens_from_dict(
            json_tokens: typing.List[typing.Dict],
        ) -> typing.List[PetToken]:
            tokens = []
            for i, json_token in enumerate(json_tokens):
                tokens.append(
                    PetToken(
                        text=json_token["text"],
                        pos_tag=json_token["posTag"],
                        index_in_document=i,
                        sentence_index=json_token["sentenceIndex"],
                    )
                )
            return tokens

        @staticmethod
        def read_mentions_from_dict(
            json_mentions: typing.List[typing.Dict],
        ) -> typing.List[PetMention]:
            mentions = []
            for json_mention in json_mentions:
                mention = NewPetFormatImporter.DictImporter.read_mention_from_dict(
                    json_mention
                )
                mentions.append(mention)
            return mentions

        @staticmethod
        def read_entities_from_dict(
            json_entities: typing.List[typing.Dict],
        ) -> typing.List[PetEntity]:
            entities = []
            for json_entity in json_entities:
                entity = NewPetFormatImporter.DictImporter.read_entity_from_dict(
                    json_entity
                )
                entities.append(entity)
            return entities

        @staticmethod
        def read_mention_from_dict(json_mention: typing.Dict) -> PetMention:
            return PetMention(
                type=json_mention["type"].lower().strip(),
                token_document_indices=tuple(json_mention["tokenDocumentIndices"]),
            )

        @staticmethod
        def read_entity_from_dict(json_entity: typing.Dict) -> PetEntity:
            return PetEntity(json_entity["mentionIndices"])

        @staticmethod
        def read_relations_from_dict(
            json_relations: typing.List[typing.Dict],
        ) -> typing.List[PetRelation]:
            relations = []
            for json_relation in json_relations:
                relations.append(
                    NewPetFormatImporter.DictImporter.read_relation_from_dict(
                        json_relation
                    )
                )
            return relations

        @staticmethod
        def read_relation_from_dict(relation_dict: typing.Dict) -> PetRelation:
            head_mention_index = relation_dict["headMentionIndex"]
            tail_mention_index = relation_dict["tailMentionIndex"]
            return PetRelation(
                head_mention_index=head_mention_index,
                tail_mention_index=tail_mention_index,
                type=relation_dict["type"].lower().strip(),
            )

    def __init__(self, file_path: str | pathlib.Path):
        self._file_path = file_path

    def do_import(self) -> typing.List[PetDocument]:
        documents: typing.List[PetDocument] = []
        with open(self._file_path, "r", encoding="utf8") as f:
            for json_line in f:
                json_data = json.loads(json_line)
                documents.append(self.read_document_from_json(json_data))
        return documents

    @staticmethod
    def read_document_from_json(json_data: typing.Dict) -> PetDocument:
        mentions = NewPetFormatImporter.DictImporter.read_mentions_from_dict(
            json_data["mentions"]
        )
        entities = NewPetFormatImporter.DictImporter.read_entities_from_dict(
            json_data["entities"]
        )
        relations = NewPetFormatImporter.DictImporter.read_relations_from_dict(
            json_data["relations"]
        )
        tokens = NewPetFormatImporter.DictImporter.read_tokens_from_dict(
            json_data["tokens"]
        )
        document = PetDocument(
            name=json_data["name"],
            text=json_data["text"],
            id=json_data["id"],
            category=json_data["category"],
            tokens=tokens,
            mentions=mentions,
            relations=relations,
            entities=entities,
        )
        return document
