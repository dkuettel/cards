from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace

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
                content=entry.content,
                review_reverse=False,
            )
        ]
    else:
        return [
            NewCardPlain(
                content=entry.content,
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
                content=entry.content,
                review_reverse=True,
            )
        ]
    else:
        return [
            NewCardReverse(
                content=entry.content,
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
    part1, part2 = split_content(entry.content)
    forward_content = f"\n{part1}\n\n_to {lang2}_\n\n---\n\n{part2}\n"
    backward_content = f"\n{part2}\n\n_to {lang1}_\n\n---\n\n{part1}\n"

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
