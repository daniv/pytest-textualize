# Project : pytest-textualize
# File Name : hook_message.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING
# from typing import Any
#
# from typing import NoReturn
# from typing import Type
from typing import assert_never

#
from pydantic import TypeAdapter

from rich.table import Table
from rich.text import Text

# from pygments import highlight
# from typing_extensions import deprecated

if TYPE_CHECKING:
    from typing import Any
    from typing import Type
    from collections.abc import Iterable
    from rich.text import TextType
    from rich.console import Console, ConsoleRenderable
    from rich.containers import RenderableType
    from rich.style import StyleType


class PrefixEnum(StrEnum):
    PREFIX_SQUARE = "▪"
    PREFIX_BULLET = "•"
    PREFIX_DASH = "-"
    PREFIX_BIG_SQUARE = "■"
    PREFIX_BIG_CIRCLE = "⬤"
    BLACK_CIRCLE = "●"
    LARGE_CIRCLE = "○"
    CIRCLED_BULLET = "⦿"
    CIRCLED_WHITE_BULLET = "⦾"
    NARY_BULLET = "⨀"


@dataclass(repr=False, frozen=True)
class ReportItem:
    name: str
    type: Type[Any]
    value: Any

    def __repr__(self) -> str:
        return f"ReportItem({self.name!r}, type={self.type!r})"


def tracer_message(
    hookname: str,
    *,
    prefix: PrefixEnum = PrefixEnum.PREFIX_SQUARE,
    info: TextType | None = None,
    escape: bool = False,
    highlight: bool = False,
) -> TracerMessage:
    return TracerMessage(hookname, prefix=prefix, info=info, highlight=highlight, escape=escape)



def is_markup(string: str) -> bool:
    if string:
        text = Text.from_markup(string)
        return len(text.spans) > 0
    return False

class TracerMessage:
    def __init__(
        self,
        hookname: str,
        *,
        prefix: PrefixEnum = PrefixEnum.PREFIX_SQUARE,
        info: TextType | None = None,
        escape: bool = False,
        highlight: bool = False,
    ) -> None:

        self.hookname =  hookname
        self.prefix = prefix
        self.info = info
        self.escape = escape
        self.highlight = highlight

        self.info = info
        if isinstance(info, str):
            self._info_str = info
        else:
            self._info_text = info

    def __call__(self, console: Console | None) -> Table:
        from rich.highlighter import ReprHighlighter
        from rich.containers import Renderables

        renderables: Iterable[ConsoleRenderable] = []
        output = Table.grid(padding=(0, 0))
        output.expand = True

        hook_name = self.hookname.ljust(30)
        len_name = len(hook_name)
        output.add_column(style="pytest.prefix", justify="right", width=2, max_width=2)
        output.add_column(style="pytest.hook", justify="left", width=6, max_width=6)
        output.add_column(style="pytest.hookname", width=len_name)
        output.add_column(ratio=1, style="log.message", overflow="fold", highlight=self.highlight)

        row: list[RenderableType] = [self.prefix, " hook: ", self.hookname]

        if self.info:
            from rich.markup import escape as markup_escape

            info = Text()
            if hasattr(self, "_info_str"):
                if self.escape:
                    self._info_str = markup_escape(self._info_str)
                if is_markup(self._info_str):
                    markup = Text.from_markup(self._info_str)
                    info.append(markup)
                        # info.append(rh(markup))
                    # info.append(rh(Text(self._info_str)))
                else:
                    info.append(Text(self._info_str))
            elif self._info_text:
                info.append(self._info_text)
            else:
                assert_never(self.info)
            renderables = [info]

        row.append(Renderables(renderables))
        output.add_row(*row)
        if console is not None:
            console.print(output, new_line_start=True)
        return output


class KeyValueMessage:
    def __init__(
            self,
            key_name: str,
            key_value: TextType,
            *,
            prefix: PrefixEnum = PrefixEnum.PREFIX_BULLET,
            value_style: StyleType | None = "",
            escape: bool = False,
            highlight: bool = False,
    ) -> None:
        self.key_name = key_name
        self.key_value = key_value
        self.value_style = value_style
        self.escape = escape
        self.highlight = highlight
        self.prefix = prefix

        if isinstance(key_value, str):
            self._value_str = key_value
        else:
            self._value_text = key_value

    def __call__(self, console: Console | None) -> Table:
        from rich.containers import Renderables
        from rich.markup import escape as markup_escape

        renderables: Iterable[ConsoleRenderable] = []
        output = Table.grid(padding=(0, 1))
        output.expand = True

        #output.add_column(style="pytest.prefix", justify="right", width=2, max_width=2)
        output.add_column(style="pytest.keyname", justify="right", width=3, max_width=2)
        output.add_column(style="pytest.keyname", justify="left")
        output.add_column(ratio=1, style="log.message", overflow="fold", highlight=self.highlight)
        row: list[RenderableType] = [self.prefix, f"{self.key_name}.  "]

        value_text = Text()
        if hasattr(self, "_value_str"):
            if self.escape:
                self._value_str = markup_escape(self._value_str)
            if is_markup(self._value_str):
                markup = Text.from_markup(self._value_str)
                value_text.append(markup)
            else:
                value_text.append(Text(self._value_str))
        else:
            value_text.append(self._value_text)
        renderables = [value_text]
        row.append(Renderables(renderables))
        output.add_row(*row)
        if console is not None:
            console.print(output, new_line_start=True)
        return output
