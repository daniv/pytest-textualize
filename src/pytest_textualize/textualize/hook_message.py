# Project : pytest-textualize
# File Name : hook_message.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum
from typing import Any
from typing import Self
from typing import TYPE_CHECKING
from typing import Type

from rich.text import Text

if TYPE_CHECKING:
    from rich.console import HighlighterType
    from rich.text import TextType
    from rich.console import RenderResult, Console, ConsoleOptions


class PrefixEnum(StrEnum):
    PREFIX_SQUARE = " ▪ "
    PREFIX_BULLET = " • "
    PREFIX_DASH = " - "
    PREFIX_BIG_SQUARE = " ■ "
    PREFIX_BIG_CIRCLE = " ⬤ "
    BLACK_CIRCLE = " ● "
    LARGE_CIRCLE = " ○ "
    MEDIUM_SMALL_WHITE_CIRCLE = " ⚬ "
    CIRCLED_BULLET = " ⦿ "
    CIRCLED_WHITE_BULLET = " ⦾ "
    NARY_BULLET = " ⨀ "


@dataclass(repr=False, frozen=True)
class ReportItem:
    name: str
    type: Type[Any]
    value: Any

    def __repr__(self) -> str:
        return f"ReportItem({self.name!r}, type={self.type!r})"


@dataclass
class ReportItemGroup:
    name: str
    group_tems: list[ReportItem] = field(default_factory=list)

    def add_report_item(self, item: ReportItem) -> Self:
        self.group_tems.append(item)
        return self


class HookMessage:
    def __init__(
            self,
            hookname: str,
            *,
            info: TextType | None = None,
            prefix: PrefixEnum = PrefixEnum.PREFIX_SQUARE,
            highlighter: HighlighterType | None = None,
            escape: bool = False,
    ) -> None:
        self.hookname = hookname
        self.prefix = prefix
        self.info = info
        self.highlighter = highlighter
        self.escape = escape

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Text.assemble(
            (f"{self.prefix}", "pytest.prefix"),
            ("hook", "pytest.hook"),
            (": ", "pytest.colon"),
            (self.hookname.ljust(30), "pytest.hookname"),
            end=" ",
        )
        if self.info and isinstance(self.info, str):
            info = self.info
            if self.escape:
                from rich.markup import escape

                yield escape(info)

            elif self.highlighter:
                yield Text.assemble(self.highlighter(info))
            else:
                yield Text.assemble(info, style="pytest.info")
