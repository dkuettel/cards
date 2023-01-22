from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Generic, Type, TypeVar

from beartype.door import die_if_unbearable

T = TypeVar("T")


class IteratorWithLength(Generic[T], Iterator[T]):
    def __init__(self, it: Iterator[T], length: int):
        self.it = it
        self.length = length

    def __len__(self):
        return self.length

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.it)


def if_bearable(value: Any, ty: Type[T]) -> T:
    die_if_unbearable(value, ty)
    return value
