from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Optional, Union

from serde import serde
from serde.core import Strict, Untagged
from serde.json import from_json, to_json
from serde.toml import from_toml

# TODO problems with serde
# @serde(type_check=Strict) is still experimental, it doesnt always fail when it should
# a tuple[str, str] doesnt complain when reading a file with more than 2 entries


@serde(type_check=Strict)
@dataclass(frozen=True)
class Plain:
    type: Literal["plain"]

    @classmethod
    def new(cls):
        return cls("plain")


@serde(type_check=Strict)
@dataclass(frozen=True)
class Reverse:
    type: Literal["reverse"]


@serde(type_check=Strict)
@dataclass(frozen=True)
class Vocab:
    type: Literal["vocab"]
    languages: tuple[str, str]


@serde(type_check=Strict, tagging=Untagged)
@dataclass(frozen=True)
class Meta:
    cards: Union[Plain, Reverse, Vocab] = field(default_factory=Plain.new)


@serde(type_check=Strict)
@dataclass(frozen=True)
class PlainIds:
    id: str


@serde(type_check=Strict)
@dataclass(frozen=True)
class ReverseIds:
    # NOTE using mochi's own reverse functionality?
    id: str


@serde(type_check=Strict)
@dataclass(frozen=True)
class VocabIds:
    forward: Optional[str]
    backward: Optional[str]


@serde(type_check=Strict)
@dataclass(frozen=True)
class Mochi:
    ids: Optional[Union[PlainIds, ReverseIds, VocabIds]] = None


# TODO sadly not a very specific name here
@dataclass(frozen=True)
class Entry:
    folder: Path
    meta: Meta
    mochi: Mochi
    content: str  # TODO markdown lib for processing?

    @classmethod
    def from_folder(cls, folder: Path):
        mochi_path = folder / "mochi.json"
        if mochi_path.exists():
            mochi = from_json(Mochi, mochi_path.read_text())
        else:
            mochi = Mochi()
        return cls(
            folder=folder,
            meta=from_toml(Meta, (folder / "meta.toml").read_text()),
            mochi=mochi,
            content=(folder / "content.md").read_text(),
        )

    def write(self):
        (self.folder / "mochi.json").write_text(to_json(self.mochi))


def get_all_entries(base: Path) -> list[Entry]:
    # NOTE we only consider folders with a meta.toml a valid entry
    # meta.toml however can be empty
    meta_paths = base.rglob("meta.toml")
    return [Entry.from_folder(p.parent) for p in meta_paths]


def update_mochi_in_folder(folder: Path, update: Callable[[Mochi], Mochi]):
    # TODO curious, from_json does return type generic, but from_dict doesnt?
    path = folder / "mochi.json"
    if path.exists():
        m = from_json(Mochi, path.read_text())
    else:
        m = Mochi()
    m = update(m)
    # TODO careful race condition, if we do threading especially
    # at least local to the python process we should lock the file?
    path.write_text(to_json(m))
