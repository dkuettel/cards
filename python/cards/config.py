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
    def from_default_file(cls):
        return from_toml(cls, Path("config.toml").read_text())

    @classmethod
    def from_test_file(cls):
        return from_toml(cls, Path("test-config.toml").read_text())


@serde
@dataclass
class Mochi:
    token: str


@serde
@dataclass
class Credentials:
    mochi: Mochi

    @classmethod
    def from_default_file(cls):
        return from_toml(cls, Path("credentials.toml").read_text())
