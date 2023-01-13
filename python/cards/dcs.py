from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, Union

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
    forward: str
    backward: str


@serde(type_check=Strict)
@dataclass(frozen=True)
class VocabIds:
    forward: str
    backward: str


@serde(type_check=Strict)
@dataclass(frozen=True)
class Mochi:
    ids: Optional[Union[PlainIds, ReverseIds, VocabIds]] = None


@dataclass
class Entry:
    folder: Path
    meta: Meta
    mochi: Mochi
    content: str  # TODO markdown lib for processing?

    @classmethod
    def from_folder(cls, folder: Path):
        return cls(
            folder=folder,
            meta=from_toml(Meta, (folder / "meta.toml").read_text()),
            mochi=from_json(Mochi, (folder / "mochi.json").read_text()),
            content=(folder / "content.md").read_text(),
        )

    def write(self):
        (self.folder / "mochi.json").write_text(to_json(self.mochi))