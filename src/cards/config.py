from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from serde import serde
from serde.toml import from_toml


@serde
@dataclass
class Sync:
    path: Path
    deck_id: str


@serde
@dataclass
class Config:
    sync: Sync

    @classmethod
    def from_base(cls, base: Path):
        return from_toml(cls, (base / "config.toml").read_text())


@serde
@dataclass
class Mochi:
    token: str


@serde
@dataclass
class Credentials:
    mochi: Mochi

    @classmethod
    def from_base(cls, base: Path):
        return from_toml(cls, (base / "credentials.toml").read_text())
