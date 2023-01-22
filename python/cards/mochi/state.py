from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cards.mochi.deck import MochiCard, MochiDeck
from cards.tools import IteratorWithLength

MochiState = dict[str, MochiCard]


def states_from_apply_diff(
    deck: MochiDeck, state: MochiState, diff: MochiDiff
) -> IteratorWithLength[tuple[MochiState, Optional[str]]]:
    def g():
        nonlocal state
        for id in diff.removed:
            deck.delete_card(id)
            state.pop(id)
            yield state, None
        for c in diff.changed:
            u = deck.update_card(c)
            state[u.id] = u
            yield state, None
        for content in diff.created:
            c = deck.create_card(content)
            state[c.id] = c
            yield state, c.id

    return IteratorWithLength(
        g(),
        len(diff.removed) + len(diff.changed) + len(diff.created),
    )


@dataclass
class MochiDiff:
    removed: list[str]
    changed: list[MochiCard]
    created: list[str]

    @classmethod
    def from_targets(cls, state: MochiState, target: MochiState, new_cards: list[str]):
        removed = [c.id for c in state.values() if c.id not in target]
        changed = [c for c in target.values() if c != state[c.id]]
        assert set(target) <= set(state)
        return cls(removed, changed, new_cards)
