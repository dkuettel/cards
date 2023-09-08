from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, final

import click
from tqdm import tqdm

from cards.data import Direction, Document
from cards.markdown import Markdown
from cards.mochi.api import ApiAttachment
from cards.mochi.deck import MochiCard
from cards.mochi.state import ExistingMochiCard, NewMochiCard
from cards.tools import if_bearable


@final
@dataclass
class ExistingCard(ExistingMochiCard):
    id: str
    doc: PlainDocument
    direction: Direction

    def get_mochi_card(self) -> MochiCard:
        content = self.doc.mochi_content(self.direction)
        return MochiCard(
            id=self.id,
            content=content,
            attachments=[],
        )

    def get_source_path(self) -> Path:
        return self.doc.path


@final
@dataclass
class NewCard(NewMochiCard):
    doc: PlainDocument
    direction: Direction

    def get_content(self) -> tuple[str, list[ApiAttachment]]:
        return self.doc.mochi_content(self.direction), []

    def get_source_path(self) -> Path:
        return self.doc.path

    def update_on_disk(self, id: str):
        self.doc.write_meta_id(self.direction, id)


@dataclass
class MetaHeader:
    id: None | str
    reverse_id: None | str

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "reverse-id": self.reverse_id,
            }
        )

    @classmethod
    def from_json(cls, text: str):
        data = json.loads(text)
        return cls(
            id=if_bearable(data.pop("id"), Optional[str]),
            reverse_id=if_bearable(data.pop("reverse-id"), Optional[str]),
        )

    def with_id(self, id: Optional[str]) -> MetaHeader:
        return MetaHeader(id, self.reverse_id)

    def with_reverse_id(self, reverse_id: Optional[str]) -> MetaHeader:
        return MetaHeader(self.id, reverse_id)


@final
@dataclass(frozen=True)
class PlainDocument(Document):
    path: Path

    def sync_local_meta(self):
        if not (
            not self.content().has_reverse_prompt()
            and self.meta().reverse_id is not None
        ):
            return
        print(f"Remove backward id from {self.path}.")
        click.confirm("Continue?", abort=True)
        self.write_meta_id(Direction.backward, None)

    def get_mochi_cards(self) -> Iterable[ExistingMochiCard | NewMochiCard]:
        md = self.content()
        meta = self.meta()

        if meta.id is None:
            yield NewCard(self, Direction.forward)
        else:
            yield ExistingCard(meta.id, self, Direction.forward)

        if md.has_reverse_prompt():
            if meta.reverse_id is None:
                yield NewCard(self, Direction.backward)
            else:
                yield ExistingCard(meta.reverse_id, self, Direction.backward)

    def write_meta_id(self, direction: Direction, id: None | str):
        meta = self.meta()
        match direction:
            case Direction.forward:
                meta.id = id
            case Direction.backward:
                meta.reverse_id = id
        write_meta_to_disk(meta, self.path)

    def meta(self) -> MetaHeader:
        return read_meta_from_disk(self.path)

    def content(self) -> Markdown:
        _, text = split_content(self.path.read_text())
        return Markdown.from_str(text)

    def mochi_content(self, direction: Direction) -> str:
        return self.content().oriented(direction).maybe_prompted().as_mochi_md_str()


def split_content(content: str) -> tuple[Optional[str], str]:
    data = content.split("\n")
    if (
        len(data) >= 4
        and data[0] == "``` {.json}"
        and data[2] == "```"
        and data[3].strip() == ""
    ):
        return data[1], "\n".join(data[4:])
    return None, content


def merge_content(header: Optional[str], text: str) -> str:
    if header is None:
        return text.lstrip("\n")

    assert "\n" not in header
    return "\n".join(
        [
            "``` {.json}",
            header,
            "```",
            "",
        ]
        + text.lstrip("\n").split("\n")
    )


def read_meta_from_disk(path: Path) -> MetaHeader:
    header, _ = split_content(path.read_text())
    if header is None:
        meta = MetaHeader(None, None)
    else:
        meta = MetaHeader.from_json(header)
    return meta


def write_meta_to_disk(meta: MetaHeader, path: Path):
    _, text = split_content(path.read_text())
    header = meta.to_json()
    assert len(header.split("\n")) == 1, header
    content = merge_content(header, text)
    path.write_text(content)


def get_all_documents(base: Path) -> list[Document]:
    return [
        PlainDocument(p) for p in tqdm(base.rglob("*.md"), desc="get all documents")
    ]
