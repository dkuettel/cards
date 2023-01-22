from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

from cards.mochi.deck import MochiCard, MochiDeck

MochiState = dict[str, MochiCard]


def states_from_apply_diff(
    deck: MochiDeck, state: MochiState, diff: MochiDiff
) -> Iterator[MochiState]:
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

    def __len__(self):
        return len(self.removed) + len(self.changed) + len(self.new_cards)

    def print_summary(self):
        print(
            f"{len(self)} items in diff: "
            f"{len(self.removed)} removed, "
            f"{len(self.changed)} changed, "
            f"{len(self.new_cards)} new cards"
        )


class NewMochiCard(ABC):
    @abstractmethod
    def get_content(self) -> str:
        pass

    @abstractmethod
    def update_on_disk(self, id: str):
        pass
