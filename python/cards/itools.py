from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType as idict
from typing import Generic, TypeVar

iset = frozenset
# NOTE this works with pyright, but doesnt allow more options yet
idataclass = dataclass(frozen=True)


T = TypeVar("T")


class ilist(Generic[T], tuple[T, ...]):
    pass


# TODO except for ilist, pyright doesnt complete any of them
__all__ = ["idict", "iset", "ilist", "idataclass"]
