from __future__ import annotations

from pathlib import Path
from typing import AbstractSet
from typing import Any
from typing import Callable as TypingCallable
from typing import NewType
from typing import Protocol
from typing import TYPE_CHECKING
from typing import TypeVar

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
    "PathLike",
    "ListAny",
    "PytestPluginType",
    # -------------------------------- Rich Types -----------------------------
    "RuleType",
    "PanelType",
    "TableType",
    "SpanType",
    "TextAlias",
    "RenderablesType",
    "ColumnType",
    "SyntaxThemeType",
    "ThemeType",
    # -------------------------------Textualize Types --------------------------
    "TextualizeSettingsType",
    "VerboseLoggerType",
    "PyProjectSettingsModelType",
    "WarningReportType",
    "TestRunResultsType",
)


_T = TypeVar("_T")
Comp_T = TypeVar("Comp_T", bound="Comparable")


AnyCallable = TypingCallable[..., Any]
NoArgAnyCallable = TypingCallable[[], Any]
AnyArgTCallable = TypingCallable[..., _T]
PytestPluginType = NewType("PytestPluginType", object)

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping, Sequence

    NoArgAnyCallable = TypingCallable[[], Any]
    TupleGenerator = Generator[tuple[str, Any], None, None]
    DictStrAny = dict[str, Any]
    DictAny = dict[Any, Any]
    SetStr = set[str]
    ListStr = list[str]
    ListAny = list[Any]
    IntStr = int | str
    AbstractSetIntStr = AbstractSet[IntStr]
    DictIntStrAny = dict[IntStr, Any]
    MappingIntStrAny = Mapping[IntStr, Any]
    CallableGenerator = Generator[AnyCallable, None, None]
    ReprArgs = Sequence[tuple[str | Any]]

    DateLike = str, pendulum.Date | pendulum.DateTime
    PathLike = str | Path

# ----------------------- RICH TYPES -----------------------------
if TYPE_CHECKING:
    from rich.rule import Rule
    from rich.panel import Panel
    from rich.table import Table, Column
    from rich.text import Span
    from rich.text import Text
    from rich.containers import Renderables
    from rich.syntax import SyntaxTheme
    from rich.theme import Theme

    type RuleType = Rule
    type PanelType = Panel
    type TableType = Table
    type SpanType = Span
    type TextAlias = Text
    type RenderablesType = Renderables
    type ColumnType = Column | str
    type SyntaxThemeType = SyntaxTheme
    type ThemeType = Theme


if TYPE_CHECKING:
    from pytest_textualize.settings import TextualizeSettings
    from pytest_textualize.textualize.logging import VerboseLogger
    from pytest_textualize.settings import ConsolePyProjectSettingsModel
    from pytest_textualize.model import WarningReport
    from pytest_textualize.model import TestRunResults

    type TextualizeSettingsType = TextualizeSettings
    type VerboseLoggerType = VerboseLogger
    type PyProjectSettingsModelType = ConsolePyProjectSettingsModel
    type WarningReportType = WarningReport
    type TestRunResultsType = TestRunResults


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
