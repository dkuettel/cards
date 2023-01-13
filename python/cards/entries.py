from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace

from cards.data import Entry, Plain, PlainIds, Reverse, ReverseIds, Vocab, VocabIds


@dataclass
class Card:
    id: str
    content: str
    review_reverse: bool


@dataclass
class NewCard(ABC):
    content: str
    review_reverse: bool

    # TODO bites a bit with immutability
    # what would be the more functional approach here?
    # it would give us back a mutated entry?
    # takes one, returns one (for when more than one callback will happen)
    # and it's the other side's responsibility to make it sync, call write, if it wants?
    # but the other side might not know the associated Entry
    # unless we bring it along anyway
    # its mainly about persisting it to the disk, not so much about changing things in memory?
    # after all it could be the old snapshot, so why not
    # maybe there is a nicer/easier approach
    # one that has data, and operations, and new data
    # the original Items list is just how/where we got it, at that time
    # so we make this more like "sync to disk"?
    # the data itself stays, understood to be an old immutable snapshot
    # we can instead reload from disk after that, if we need to

    @abstractmethod
    def when_added(self, card_id: str):
        pass


# TODO is there a nicer way to handle the 2 returns? a bit verbose
def get_cards_from_entries(entries: list[Entry]) -> tuple[list[NewCard], list[Card]]:
    new_cards, cards = [], []
    for entry in entries:
        c = get_card_from_entry(entry)
        if isinstance(c, NewCard):
            new_cards.append(c)
        elif isinstance(c, Card):
            cards.append(c)
        else:
            assert False, c
    return new_cards, cards


def get_card_from_entry(entry: Entry) -> tuple[list[NewCard], list[Card]]:
    if type(entry.meta) is Plain:
        return get_card_from_Plain(entry, entry.meta)
    elif type(entry.meta) is Reverse:
        return get_card_from_Reverse(entry, entry.meta)
    elif type(entry.meta) is Vocab:
        return get_card_from_Vocab(entry, entry.meta)
    else:
        assert False, entry.meta


@dataclass
class NewCardPlain(NewCard):
    entry: Entry

    def when_added(self, card_id: str):
        self.entry.mochi.ids = PlainIds(card_id)
        self.entry.write()


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


@dataclass
class NewCardReverse(NewCard):
    entry: Entry

    def when_added(self, card_id: str):
        self.entry.mochi.ids = ReverseIds(card_id)
        self.entry.write()


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


@dataclass
class NewCardVocabForward(NewCard):
    entry: Entry

    def when_added(self, card_id: str):
        assert type(self.entry.mochi.ids) is VocabIds
        self.entry.mochi.ids = replace(self.entry.mochi.ids, forward=card_id)
        self.entry.write()


@dataclass
class NewCardVocabBackward(NewCard):
    entry: Entry

    def when_added(self, card_id: str):
        assert type(self.entry.mochi.ids) is VocabIds
        self.entry.mochi.ids = replace(self.entry.mochi.ids, backward=card_id)
        self.entry.write()


def get_card_from_Vocab(entry: Entry, meta: Vocab) -> tuple[list[NewCard], list[Card]]:

    lang1, lang2 = meta.languages
    part1, part2 = split_content(entry.content)
    forward_content = f"\n{part1}\n\n_to {lang2}_\n\n---\n\n{part2}\n"
    backward_content = f"\n{part2}\n\n_to {lang1}_\n\n---\n\n{part1}\n"

    if type(entry.mochi.ids) is not VocabIds:
        entry.mochi.ids = VocabIds(None, None)

    new_cards, cards = [], []

    if entry.mochi.ids.forward is None:
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
                id=entry.mochi.ids.forward,
                content=forward_content,
                review_reverse=False,
            )
        )

    if entry.mochi.ids.backward is None:
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
                id=entry.mochi.ids.backward,
                content=backward_content,
                review_reverse=False,
            )
        )

    return new_cards, cards
