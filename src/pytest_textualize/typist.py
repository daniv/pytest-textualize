from __future__ import annotations

from pathlib import Path
from typing import AbstractSet
from typing import Any
from typing import Protocol
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Callable as TypingCallable

import pendulum

__all__ = (
    "Comparable",
    "DateLike",
    "PathLike",
    "ToDictable",
    "DictStrAny",
    "TupleGenerator",
    "NoArgAnyCallable",
    "SetStr",
    "ListStr",
    "IntStr",
    "CallableGenerator",
    "MappingIntStrAny",
    "DateLike",
    "PathLike"
)

_T = TypeVar('_T')
Comp_T = TypeVar("Comp_T", bound="Comparable")

AnyCallable = TypingCallable[..., Any]
NoArgAnyCallable = TypingCallable[[], Any]
AnyArgTCallable = TypingCallable[..., _T]

if TYPE_CHECKING:
    from collections.abc import Iterable, Generator, Mapping, Sequence

    NoArgAnyCallable = TypingCallable[[], Any]
    TupleGenerator = Generator[tuple[str, Any], None, None]
    DictStrAny = dict[str, Any]
    DictAny = dict[Any, Any]
    SetStr = set[str]
    ListStr = list[str]
    IntStr = int | str
    AbstractSetIntStr = AbstractSet[IntStr]
    DictIntStrAny = dict[IntStr, Any]
    MappingIntStrAny = Mapping[IntStr, Any]
    CallableGenerator = Generator[AnyCallable, None, None]
    ReprArgs = Sequence[tuple[str | Any]]


    DateLike = str, pendulum.Date | pendulum.DateTime
    PathLike = str, Path




class ToDictable(Protocol):
    """Any object with a to_dict() method."""

    def to_dict(self) -> dict[str, Any]:
        """Converts this object to a dictionary."""

class Comparable(Protocol):
    """A type that can be compared and sorted."""

    def __eq__(self, other: Any) -> bool:  # noqa: D105
        pass

    def __lt__(self: Comp_T, other: Comp_T) -> bool:  # noqa: D105
        pass

    def __gt__(self: Comp_T, other: Comp_T) -> bool:  # noqa: D105
        pass

    def __le__(self: Comp_T, other: Comp_T) -> bool:  # noqa: D105
        pass

    def __ge__(self: Comp_T, other: Comp_T) -> bool:  # noqa: D105
        pass
