from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterator, Optional

from cards.documents import Document, read_meta_from_disk, write_meta_to_disk


@dataclass
class NewCard(ABC):
    content: str

    @abstractmethod
    def update_on_disk(self, card_id: str):
        pass


@dataclass
class NewCardForward(NewCard):
    path: Path

    def update_on_disk(self, card_id: str):
        meta = read_meta_from_disk(self.path)
        meta = replace(meta, id=card_id)
        write_meta_to_disk(meta, self.path)


@dataclass
class NewCardBackward(NewCard):
    path: Path

    def update_on_disk(self, card_id: str):
        meta = read_meta_from_disk(self.path)
        meta = replace(meta, reverse_id=card_id)
        write_meta_to_disk(meta, self.path)


@dataclass
class Card:
    id: str
    content: str


def get_cards_from_documents(docs: list[Document]) -> tuple[list[NewCard], list[Card]]:
    return list(_get_new_cards(docs)), list(_get_cards(docs))


def _get_new_cards(docs: list[Document]) -> Iterator[NewCard]:
    for doc in docs:
        if doc.meta.id is None:
            yield NewCardForward(as_mochi_md(doc.md, doc.prompt), doc.path)
        if doc.meta.reverse_id is None and doc.reverse_md is not None:
            yield NewCardBackward(
                as_mochi_md(doc.reverse_md, doc.reverse_prompt), doc.path
            )


def _get_cards(docs: list[Document]) -> Iterator[Card]:
    for doc in docs:
        if doc.meta.id is not None:
            yield Card(doc.meta.id, as_mochi_md(doc.md, doc.prompt))
        if doc.meta.reverse_id is not None and doc.reverse_md is not None:
            yield Card(
                doc.meta.reverse_id, as_mochi_md(doc.reverse_md, doc.reverse_prompt)
            )
        if doc.meta.reverse_id is not None and doc.reverse_md is None:
            # TODO what if we remove a prompt, and reverse disappears
            # will we ever update meta? sync might now, but disk might not update
            # maybe that should be part of Document? it's the abstraction there when things go
            meta = read_meta_from_disk(doc.path)
            meta = replace(meta, reverse_id=None)
            write_meta_to_disk(meta, doc.path)


def as_mochi_md(body: list, prompt: Optional[list]) -> str:
    import pandoc
    from pandoc.types import Emph, Meta, Pandoc  # pyright: ignore

    if prompt is None:
        prefix = []
    else:
        prefix = Emph(prompt)

    return pandoc.write(
        Pandoc(Meta({}), prefix + body), format="markdown+hard_line_breaks"
    )
