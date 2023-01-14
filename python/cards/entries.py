from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace

import pandoc
from cards.data import (
    Entry,
    Mochi,
    Plain,
    PlainIds,
    Reverse,
    ReverseIds,
    Vocab,
    VocabIds,
    update_mochi_in_folder,
)
from pandoc.types import HorizontalRule, Meta, Pandoc  # pyright: ignore


def parse_md(text: str) -> list:
    # TODO very haskell style, pattern matching works on syntax elements :)
    return pandoc.read(text, format="markdown")[1]  # pyright: ignore


def mochi_md(doc: list) -> str:
    return pandoc.write(Pandoc(Meta({}), doc), format="markdown+hard_line_breaks")


def mochi_md_from_md(text: str) -> str:
    return mochi_md(parse_md(text))


@dataclass(frozen=True)
class Card:
    id: str
    content: str
    review_reverse: bool


@dataclass(frozen=True)
class NewCard(ABC):
    content: str
    review_reverse: bool

    @abstractmethod
    def update_on_disk(self, card_id: str):
        pass


# TODO is there a nicer way to handle the 2 returns? a bit verbose
def get_cards_from_entries(entries: list[Entry]) -> tuple[list[NewCard], list[Card]]:
    new_cards, cards = [], []
    for entry in entries:
        nc, c = get_card_from_entry(entry)
        new_cards.extend(nc)
        cards.extend(c)
    return new_cards, cards


def get_card_from_entry(entry: Entry) -> tuple[list[NewCard], list[Card]]:
    if type(entry.meta.cards) is Plain:
        return get_card_from_Plain(entry, entry.meta.cards)
    elif type(entry.meta.cards) is Reverse:
        return get_card_from_Reverse(entry, entry.meta.cards)
    elif type(entry.meta.cards) is Vocab:
        return get_card_from_Vocab(entry, entry.meta.cards)
    else:
        assert False, entry.meta


@dataclass(frozen=True)
class NewCardPlain(NewCard):
    entry: Entry

    def update_on_disk(self, card_id: str):
        update_mochi_in_folder(self.entry.folder, lambda _: Mochi(PlainIds(card_id)))


def get_card_from_Plain(entry: Entry, _: Plain) -> tuple[list[NewCard], list[Card]]:
    if type(entry.mochi.ids) is PlainIds:
        return [], [
            Card(
                id=entry.mochi.ids.id,
                content=mochi_md_from_md(entry.content),
                review_reverse=False,
            )
        ]
    else:
        return [
            NewCardPlain(
                content=mochi_md_from_md(entry.content),
                review_reverse=False,
                entry=entry,
            )
        ], []


@dataclass(frozen=True)
class NewCardReverse(NewCard):
    entry: Entry

    def update_on_disk(self, card_id: str):
        update_mochi_in_folder(self.entry.folder, lambda _: Mochi(ReverseIds(card_id)))


def get_card_from_Reverse(entry: Entry, _: Reverse) -> tuple[list[NewCard], list[Card]]:
    if type(entry.mochi.ids) is ReverseIds:
        return [], [
            Card(
                id=entry.mochi.ids.id,
                content=mochi_md_from_md(entry.content),
                review_reverse=True,
            )
        ]
    else:
        return [
            NewCardReverse(
                content=mochi_md_from_md(entry.content),
                review_reverse=False,
                entry=entry,
            )
        ], []


def split_content(content: str) -> tuple[str, str]:
    parts = content.split("---")
    part1, part2 = parts
    part1 = part1.strip(" \n")
    part2 = part2.strip(" \n")
    return part1, part2


@dataclass(frozen=True)
class NewCardVocabForward(NewCard):
    entry: Entry

    def update_on_disk(self, card_id: str):
        def update(m: Mochi) -> Mochi:
            ids = m.ids
            if type(ids) is not VocabIds:
                ids = VocabIds(None, None)
            ids = replace(ids, forward=card_id)
            return replace(m, ids=ids)

        update_mochi_in_folder(self.entry.folder, update)


@dataclass(frozen=True)
class NewCardVocabBackward(NewCard):
    entry: Entry

    def update_on_disk(self, card_id: str):
        def update(m: Mochi) -> Mochi:
            ids = m.ids
            if type(ids) is not VocabIds:
                ids = VocabIds(None, None)
            ids = replace(ids, backward=card_id)
            return replace(m, ids=ids)

        update_mochi_in_folder(self.entry.folder, update)


def get_card_from_Vocab(entry: Entry, meta: Vocab) -> tuple[list[NewCard], list[Card]]:

    lang1, lang2 = meta.languages

    doc = parse_md(entry.content)

    split_at = doc.index(HorizontalRule())
    forward_doc = (
        parse_md(f"_to {lang2}_")
        + doc[:split_at]
        + [HorizontalRule()]
        + doc[split_at + 1 :]
    )
    backward_doc = (
        parse_md(f"_to {lang1}_")
        + doc[split_at + 1 :]
        + [HorizontalRule()]
        + doc[:split_at]
    )

    forward_content = mochi_md(forward_doc)
    backward_content = mochi_md(backward_doc)

    ids = entry.mochi.ids
    if type(ids) is not VocabIds:
        ids = VocabIds(None, None)

    new_cards, cards = [], []

    if ids.forward is None:
        new_cards.append(
            NewCardVocabForward(
                content=forward_content,
                review_reverse=False,
                entry=entry,
            )
        )
    else:
        cards.append(
            Card(
                id=ids.forward,
                content=forward_content,
                review_reverse=False,
            )
        )

    if ids.backward is None:
        new_cards.append(
            NewCardVocabBackward(
                content=backward_content,
                review_reverse=False,
                entry=entry,
            )
        )
    else:
        cards.append(
            Card(
                id=ids.backward,
                content=backward_content,
                review_reverse=False,
            )
        )

    return new_cards, cards


def test_format():
    print(
        mochi_md_from_md(
            """
satire

---

The use of

- humour
- irony
- exaggeration
- or ridicule

to expose and criticize
people's stupidity or vices,
particularly in the context of contemporary politics
and other topical issues.
"""
        )
    )
    # TODO pandoc supports the extension 'hard_line_breaks'
    # that seems to be what mochi does
    # does it mean we could load as is and output with the extension to transform?
    # then maybe I can ask what lib, or what pandoc settings mochi is using
    # > pandoc content.md --from=markdown --to=markdown+hard_line_breaks
    # works, but then I need to call something, is there a python interface?
    # it also reformats the --- to very many dashes, seems depending on the text width
    # so how do I find pages for reversing, ah nice it has the AST
    # TODO depending on the settings I use might want to update the previewer? so far changes are only on --to=... side


if __name__ == "__main__":
    test_format()
