from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from serde import serde
from serde.json import from_json, to_json
from tqdm import tqdm

from cards.data import Direction
from cards.markdown import Markdown
from cards.mochi.api import ApiAttachment
from cards.mochi.deck import MochiCard
from cards.mochi.state import ExistingMochiCard, NewMochiCard


# TODO could that be the interface between data sources (on disk) and mochi state / cards ?
# (the returns have a callback for writing meta data)
class Document(ABC):
    @abstractmethod
    def get_mochi_cards(self) -> Iterable[ExistingMochiCard | NewMochiCard]:
        pass


@dataclass
class ExistingCard(ExistingMochiCard):
    id: str
    doc: RichDocument
    direction: Direction

    def get_mochi_card(self) -> MochiCard:
        content, attachments = self.doc.mochi_content(self.direction)
        return MochiCard(
            id=self.id,
            content=content,
            attachments=attachments,
        )

    def get_source_path(self) -> Path:
        return self.doc.base


@dataclass
class NewCard(NewMochiCard):
    doc: RichDocument
    direction: Direction

    def get_content(self) -> tuple[str, list[ApiAttachment]]:
        return self.doc.mochi_content(self.direction)

    def get_source_path(self) -> Path:
        return self.doc.base

    # TODO naming
    def update_on_disk(self, id: str):
        self.doc.write_meta_id(self.direction, id)


@dataclass
class RichDocument(Document):
    base: Path

    def get_mochi_cards(self) -> Iterable[ExistingMochiCard | NewMochiCard]:
        doc = self.content()
        meta = self.meta()

        if meta.forward is None:
            yield NewCard(self, Direction.forward)
        else:
            yield ExistingCard(meta.forward, self, Direction.forward)

        if doc.has_reverse_prompt():
            if meta.backward is None:
                yield NewCard(self, Direction.backward)
            else:
                yield ExistingCard(meta.backward, self, Direction.backward)

    def content(self) -> Markdown:
        return Markdown.from_path(self.base / "content.md")

    def meta(self) -> Meta:
        meta_path = self.base / "meta.json"
        if meta_path.exists():
            return from_json(Meta, meta_path.read_text())
        return Meta()

    def mochi_content(self, direction: Direction) -> tuple[str, list[ApiAttachment]]:
        content = self.content().oriented(direction).maybe_prompted()

        # TODO might not have to be local class
        @dataclass
        class Images:
            base: Path
            next_index: int = 0
            data: dict[str, Path] = field(default_factory=dict)

            def collect(self, path: str) -> tuple[str, str]:
                local = self.base / path
                assert local.exists(), local
                assert local.suffix in {".png", ".jpg", ".jpeg"}, local
                # TODO mochis requirements on names here a bit arbitrary, and not correctly documented too
                name = f"i{self.next_index:08}{local.suffix}"
                remote = f"@media/{name}"
                self.data[name] = local
                self.next_index += 1
                hash = sha256()
                hash.update(local.read_bytes())
                return remote, hash.hexdigest()

            def as_api_attachments(self) -> list[ApiAttachment]:
                # TODO we might also consider scaling the images?
                return [ApiAttachment.from_file(k, v) for k, v in self.data.items()]

        # TODO this will also have to collect the binary data
        # we need a good carrier for the complex return then
        # TODO maybe mochi only accepts ![desc](link), without (link something)?
        # TODO hopefully attachments are a namespace per card
        images = Images(self.base)
        content = content.with_rewritten_images(images.collect)
        return content.as_mochi_md_str(), images.as_api_attachments()

    def write_meta_id(self, direction: Direction, id: str):
        meta = self.meta()
        match direction:
            case Direction.forward:
                meta.forward = id
            case Direction.backward:
                meta.backward = id
        meta_path = self.base / "meta.json"
        meta_path.write_text(to_json(meta))


@serde
@dataclass
class Meta:
    forward: None | str = None
    backward: None | str = None


def get_all_rich_documents(base: Path) -> list[Document]:
    return [
        RichDocument(p.parent)
        for p in tqdm(base.glob("*/content.md"), desc="get all rich documents")
    ]
