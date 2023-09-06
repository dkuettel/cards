from typing import Any, Type, TypeVar

from beartype.door import die_if_unbearable

T = TypeVar("T")


def if_bearable(value: Any, ty: Type[T]) -> T:
    die_if_unbearable(value, ty)
    return value
