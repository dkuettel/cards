from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from cards.mochi.deck import MochiCard, MochiDeck
from cards.tools import IteratorWithLength

MochiState = dict[str, MochiCard]


def states_from_apply_diff(
    deck: MochiDeck, state: MochiState, diff: MochiDiff
) -> IteratorWithLength[MochiState]:
    def g():
        nonlocal state
        for id in diff.removed:
            deck.delete_card(id)
            state.pop(id)
            yield state
        for c in diff.changed:
            u = deck.update_card(c)
            state[u.id] = u
            yield state
        for c in diff.new_cards:
            u = deck.create_card(c.get_content())
            c.update_on_disk(u.id)
            state[u.id] = u
            yield state

    return IteratorWithLength(
        g(),
        len(diff.removed) + len(diff.changed) + len(diff.new_cards),
    )


@dataclass(frozen=True)
class MochiDiff:
    removed: list[str]
    changed: list[MochiCard]
    new_cards: list[NewMochiCard]

    @classmethod
    def from_targets(
        cls, state: MochiState, target: MochiState, new_cards: list[NewMochiCard]
    ):
        removed = [c.id for c in state.values() if c.id not in target]
        changed = [c for c in target.values() if c != state[c.id]]
        assert set(target) <= set(state)
        return cls(removed, changed, new_cards)


class NewMochiCard(ABC):
    @abstractmethod
    def get_content(self) -> str:
        pass

    @abstractmethod
    def update_on_disk(self, id: str):
        pass
