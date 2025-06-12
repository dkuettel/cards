from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from requests.auth import HTTPBasicAuth

from cards import api
from cards.data import Card, Meta


def states_from_apply_diff(
    auth: HTTPBasicAuth,
    deck_id: str,
    state: dict[str, api.Card],
    diff: MochiDiff,
    meta: dict[Path, Meta],
) -> Iterator[tuple[dict[str, api.Card], dict[Path, Meta]]]:
    for id, card in diff.changed.items():
        # TODO or we want the raw call? because we keep the local state as generic jsons?
        # unless we really make a wrapped layer around a cached kind of api?
        u = api.update_card(
            auth,
            api.Card(
                id=id,
                content=card.content,
                deck_id=deck_id,
            ),
            attachments=card.attachments,
        )
        state[u.id] = u
        yield state, meta

    for card in diff.removed:
        api.delete_card(auth, card.id)
        state.pop(card.id)
        yield state, meta

    for card in diff.new:
        u = api.create_card(auth, deck_id, card.content, card.attachments)
        meta.setdefault(card.path, Meta(None, None)).set_by_direction(
            card.direction, u.id
        )
        state[u.id] = u
        yield state, meta


@dataclass
class MochiDiff:
    changed: dict[str, Card]
    removed: list[api.Card]
    new: list[Card]

    @classmethod
    def from_states(
        cls,
        remote: dict[str, api.Card],
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
