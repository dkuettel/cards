from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from cards.data import Card, Meta
from cards.mochi.deck import MochiCard, MochiDeck


def states_from_apply_diff(
    deck: MochiDeck,
    state: dict[str, MochiCard],
    diff: MochiDiff,
    meta: dict[Path, Meta],
) -> Iterator[tuple[dict[str, MochiCard], dict[Path, Meta]]]:
    for id, card in diff.changed.items():
        u = deck.update_card(MochiCard(id, card.content, card.attachments))
        state[u.id] = u
        yield state, meta

    for card in diff.removed:
        deck.delete_card(card.id)
        state.pop(card.id)
        yield state, meta

    for card in diff.new:
        u = deck.create_card(card.content, card.attachments)
        meta[card.path].set_by_direction(card.direction, u.id)
        state[u.id] = u
        yield state, meta


@dataclass
class MochiDiff:
    changed: dict[str, Card]
    removed: list[MochiCard]
    new: list[Card]

    @classmethod
    def from_states(
        cls,
        remote: dict[str, MochiCard],
        existing: dict[str, Card],
        new: list[Card],
    ):
        assert set(existing) <= set(remote), "Remote deletion is not supported."
        changed = {
            id: card
            for id, card in existing.items()
            # TODO not very happy here with how we compare == and !=
            # this logic is "deep" because of how we create content and images
            # and it's a bit disconnected to have it here
            if remote[id].content != card.content
        }
        removed = [c for c in remote.values() if c.id not in existing]
        return cls(changed, removed, new)

    def count(self) -> int:
        return len(self.changed) + len(self.removed) + len(self.new)

    def print_summary(self):
        # TODO no info yet for "removed" until it happens
        # no local path, so we might add the query content?
        for c in self.changed.values():
            print(f"changed from {c.path}")
        for c in self.new:
            print(f"new from {c.path}")
        print(
            f"{self.count()} items in diff: "
            f"{len(self.removed)} removed, "
            f"{len(self.changed)} changed, "
            f"{len(self.new)} new cards"
        )
