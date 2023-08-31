from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from cards.mochi.deck import MochiCard, MochiDeck


def states_from_apply_diff(
    deck: MochiDeck, state: dict[str, MochiCard], diff: MochiDiff
) -> Iterator[dict[str, MochiCard]]:
    for id in diff.removed:
        deck.delete_card(id)
        state.pop(id)
        yield state
    for t in diff.changed:
        u = deck.update_card(t.get_card())
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
    changed: list[TargetMochiCard]
    new_cards: list[NewMochiCard]

    @classmethod
    def from_targets(
        cls,
        # TODO kinda redundant since MochiCard has an id as well
        state: dict[str, MochiCard],
        target: dict[str, TargetMochiCard],
        new_cards: list[NewMochiCard],
    ):
        removed = [c.id for c in state.values() if c.id not in target]
        # TODO not very happy here with how we compare == and !=
        changed = [t for t in target.values() if t.get_card() != state[t.get_card().id]]
        assert set(target) <= set(state)
        return cls(removed, changed, new_cards)

    # TODO its a useful operation, but not sure it makes sense to map it to len(.)
    def __len__(self):
        return len(self.removed) + len(self.changed) + len(self.new_cards)

    def print_summary(self):
        cwd = Path.cwd()
        # TODO no info yet for "removed" until it happens
        for t in self.changed:
            print(f"changed from {t.get_source_path()}")
        for c in self.new_cards:
            print(f"new from {c.get_source_path().relative_to(cwd)}")
        print(
            f"{len(self)} items in diff: "
            f"{len(self.removed)} removed, "
            f"{len(self.changed)} changed, "
            f"{len(self.new_cards)} new cards"
        )


class TargetMochiCard(ABC):
    @abstractmethod
    def get_card(self) -> MochiCard:
        pass

    @abstractmethod
    def get_source_path(self) -> Path:
        pass


class NewMochiCard(ABC):
    @abstractmethod
    def get_content(self) -> str:
        pass

    @abstractmethod
    def get_source_path(self) -> Path:
        pass

    @abstractmethod
    def update_on_disk(self, id: str):
        pass
