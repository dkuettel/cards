from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from tqdm import tqdm

from cards.mochi.api import ApiAttachment
from cards.mochi.deck import MochiCard, MochiDeck


# TODO the idea was that we have a local state
# that should mirror what is on mochi, as best as we can
# so that eventually we might even cache it
# maybe ultimately it's easier to have the MochiState behind an interface
# for now we just used a dict[id, ...], currently mocked a bit
# (MochiDeck is a bit that interface maybe)
def states_from_apply_diff(
    deck: MochiDeck, state: list[MochiCard], diff: MochiDiff
) -> Iterator[list[MochiCard]]:
    state_by_id = {c.id: c for c in state}
    for card in diff.changed:
        u = deck.update_card(card.get_mochi_card())
        state_by_id[u.id] = u
        yield list(state_by_id.values())
    for card in diff.removed:
        deck.delete_card(card.id)
        state_by_id.pop(card.id)
        yield list(state_by_id.values())
    for card in diff.new:
        # TODO ok create_card id weird, just acts on a str?
        u = deck.create_card(*card.get_content())
        card.update_on_disk(u.id)
        state_by_id[u.id] = u
        yield list(state_by_id.values())


@dataclass(frozen=True)
class MochiDiff:
    unchanged: list[ExistingMochiCard]
    changed: list[ExistingMochiCard]
    removed: list[MochiCard]
    new: list[NewMochiCard]

    @classmethod
    def from_states(
        cls,
        remote: list[MochiCard],
        local: list[ExistingMochiCard | NewMochiCard],
    ):
        # TODO let's first write it correct
        # but eventually we have to see about card creation
        # right now we create it many times, use cached property?
        remote_by_id = {c.id: c for c in remote}
        local_by_id = {
            # TODO match here is proably cleaner in the end? for later mistakes
            c.get_mochi_card().id: c
            for c in tqdm(local, "diff")
            if isinstance(c, ExistingMochiCard)
        }
        assert set(local_by_id) <= set(
            remote_by_id
        ), "We don't support remote deletion."
        unchanged = []
        changed = []
        removed = []
        new = []
        for card in remote:
            if card.id not in local_by_id:
                removed.append(card)
        for card in tqdm(local, desc="diff"):
            match card:
                case ExistingMochiCard():
                    # TODO we already have it in this function, but even more globaly we could think about speed here
                    mc = card.get_mochi_card()
                    # TODO not very happy here with how we compare == and !=
                    # this logic is "deep" because of how we create content and images
                    # and it's a bit disconnected to have it here
                    if mc.content == remote_by_id[mc.id].content:
                        unchanged.append(card)
                    else:
                        changed.append(card)
                case NewMochiCard():
                    new.append(card)
                case _:
                    assert False
        return cls(unchanged, changed, removed, new)

    def count(self) -> int:
        return len(self.changed) + len(self.removed) + len(self.new)

    def print_summary(self):
        # cwd = Path.cwd()
        # TODO no info yet for "removed" until it happens
        for t in self.changed:
            print(f"changed from {t.get_source_path()}")
        for c in self.new:
            # print(f"new from {c.get_source_path().relative_to(cwd)}")
            print(f"new from {c.get_source_path()}")
        print(
            f"{self.count()} items in diff: "
            f"{len(self.removed)} removed, "
            f"{len(self.changed)} changed, "
            f"{len(self.new)} new cards"
        )


class ExistingMochiCard(ABC):
    @abstractmethod
    def get_mochi_card(self) -> MochiCard:
        pass

    @abstractmethod
    def get_source_path(self) -> Path:
        pass


class NewMochiCard(ABC):
    # TODO soon there will also be attachments
    # so MochiCard and MochiCardWithId to share things?
    @abstractmethod
    def get_content(self) -> tuple[str, list[ApiAttachment]]:
        pass

    @abstractmethod
    def get_source_path(self) -> Path:
        pass

    @abstractmethod
    def update_on_disk(self, id: str):
        pass
