from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Iterable

from cards.mochi.state import ExistingMochiCard, NewMochiCard


class Direction(Enum):
    forward = "forward"
    backward = "backward"


class Document(ABC):
    @abstractmethod
    def sync_local_meta(self):
        pass

    @abstractmethod
    def get_mochi_cards(self) -> Iterable[ExistingMochiCard | NewMochiCard]:
        pass


def get_all_documents(path: Path) -> list[Document]:
    from cards.data import plain, rich

    return plain.get_all_documents(path / "plain") + rich.get_all_documents(
        path / "rich"
    )
