from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from cards.data.plain.documents import Document, read_meta_from_disk, write_meta_to_disk
from cards.mochi.deck import MochiCard
from cards.mochi.state import NewMochiCard, ExistingMochiCard


@dataclass(frozen=True)
class NewCardForward(NewMochiCard):
    content: str
    path: Path

    def get_content(self) -> str:
        return self.content

    def get_source_path(self) -> Path:
        return self.path

    def update_on_disk(self, card_id: str):
        meta = read_meta_from_disk(self.path)
        meta = meta.with_id(card_id)
        write_meta_to_disk(meta, self.path)


@dataclass(frozen=True)
class NewCardBackward(NewMochiCard):
    content: str
    path: Path

    def get_content(self) -> str:
        return self.content

    def get_source_path(self) -> Path:
        return self.path

    def update_on_disk(self, card_id: str):
        meta = read_meta_from_disk(self.path)
        meta = meta.with_reverse_id(card_id)
        write_meta_to_disk(meta, self.path)


@dataclass(frozen=True)
class TargetCard(ExistingMochiCard):
    card: MochiCard
    source: Path

    def get_card(self) -> MochiCard:
        return self.card

    def get_source_path(self) -> Path:
        return self.source


def get_new_cards_from_documents(docs: list[Document]) -> list[NewMochiCard]:
    return [c for doc in docs for c in get_new_cards_from_document(doc)]


def get_new_cards_from_document(doc: Document) -> Iterator[NewMochiCard]:
    if doc.meta.id is None:
        yield NewCardForward(as_mochi_md(doc.md, doc.prompt), doc.path)
    if doc.meta.reverse_id is None and doc.reverse_md is not None:
        yield NewCardBackward(as_mochi_md(doc.reverse_md, doc.reverse_prompt), doc.path)


# def get_cards_from_documents(docs: list[Document]) -> list[TargetMochiCard]:
#     return [
#         c
#         for doc in tqdm(docs, desc="cards from documents")
#         for c in get_cards_from_document(doc)
#     ]


# def get_cards_from_document(doc: Document) -> Iterator[TargetMochiCard]:
#     if doc.meta.id is not None:
#         yield TargetCard(
#             MochiCard(doc.meta.id, as_mochi_md(doc.md, doc.prompt)), doc.path
#         )
#     if doc.meta.reverse_id is not None and doc.reverse_md is not None:
#         yield TargetCard(
#             MochiCard(
#                 doc.meta.reverse_id, as_mochi_md(doc.reverse_md, doc.reverse_prompt)
#             ),
#             doc.path,
#         )


def as_mochi_md(body: list, prompt: Optional[list]) -> str:
    import pandoc
    from pandoc.types import Emph, Meta, Pandoc, Para  # pyright: ignore

    if prompt is None:
        prefix = []
    else:
        prefix = [Para([Emph(prompt)])]

    return pandoc.write(
        Pandoc(Meta({}), prefix + body),
        format="markdown+hard_line_breaks",
        # NOTE columns=3 and wrap=none forces rulers to be exactly 3 dashes (---)
        # mochi accepts only exactly 3 dashes (---) as a new page
        options=["--columns=3", "--wrap=none"],
    )
