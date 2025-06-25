# Project : pytest-textualize
# File Name : hook_message.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations

from enum import StrEnum
from typing import Literal
from typing import TYPE_CHECKING
# from typing import Any
#
# from typing import NoReturn
# from typing import Type
from typing import assert_never

import pytest
from rich import box

from rich.padding import Padding
from rich.panel import Panel
from rich.table import Column
from rich.table import Table
from rich.text import Text


if TYPE_CHECKING:
    from collections.abc import Iterable
    from rich.text import TextType
    from rich.console import Console, ConsoleRenderable
    from rich.containers import RenderableType
    from rich.style import StyleType


def is_markup(string: str) -> bool:
    if string:
        text = Text.from_markup(string)
        return len(text.spans) > 0
    return False


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

        self.hookname = hookname
        self.prefix = prefix
        self.info = info
        self.escape = escape
        self.highlight = highlight

        self.info = info
        if isinstance(info, str):
            self._info_str = info
        else:
            self._info_text = info

    def __call__(self, console: Console | None) -> Table | None:
        from rich.containers import Renderables

        renderables: Iterable[ConsoleRenderable] = []
        output = Table.grid(padding=(0, 1))
        output.expand = True

        hook_name = self.hookname.ljust(30)
        len_name = len(hook_name)
        output.add_column(style="pyest.hook.prefix", justify="right", width=1, max_width=1)
        output.add_column(style="pyest.hook.tag", justify="left", width=5, max_width=5)
        output.add_column(style="pyest.hook.name", width=len_name)
        output.add_column(ratio=1, style="pyest.hook.info", overflow="fold", highlight=self.highlight)

        row: list[RenderableType] = [self.prefix, "hook:".ljust(6), self.hookname]

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
        key_value: TextType | ConsoleRenderable,
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

    def __call__(self, console: Console | None) -> Table | None:
        from rich.containers import Renderables
        from rich.markup import escape as markup_escape

        output = Table.grid(padding=(0, 1))
        output.expand = True

        output.add_column(style="#B0D9B1", justify="right", width=7, max_width=7)
        output.add_column(style="#CBFFA9", justify="left")
        # output.add_column(style="#FDFFAE", justify="left")
        output.add_column(ratio=1, style=self.value_style, overflow="fold", highlight=self.highlight)
        key_name = self.key_name.ljust(30)
        row: list[RenderableType] = [self.prefix, key_name]

        value_text = Text()
        if hasattr(self, "_value_str"):
            if self.escape:
                self._value_str = markup_escape(self._value_str)
            if is_markup(self._value_str):
                markup = Text.from_markup(self._value_str)
                value_text.append(markup)
            else:
                value_text.append(Text(self._value_str))
        elif isinstance(self._value_text, Text):
            value_text.append(self._value_text)
        else:
            value_text = self._value_text
        renderables: Iterable[ConsoleRenderable] = [value_text]
        row.append(Renderables(renderables))
        output.add_row(*row)
        if console is not None:
            console.print(output)
        return output


def pytest_textualize_header(console: Console) -> None:
    from importlib import metadata

    version = metadata.version("pytest_textualize")
    panel = Panel(
        Text(
            "A pytest plugin using Rich for beautiful test result formatting.",  # noqa: E501
            justify="center",
            style="txt.header.version",
        ),
        title="[txt.header.title]pytest-textualize plugin[/]",
        title_align="center",
        subtitle=f"[txt.header.content]v{version}[/]",
        subtitle_align="center",
        box=box.DOUBLE,
        style="txt.header.border",
        padding=2,
        expand=True,
        highlight=False,
    )

    console.print(panel, new_line_start=True)


def stage_rule(
        console: Console,
        stage: Literal["session", "collection", "error", "execution"],
        time_str: str,
        start: bool = True
) -> None:
    msg = "started" if start else "ended"
    title = f"[txt.stage_title][b]{stage.capitalize()}[/] {msg} at[/] [txt.stage_time]{time_str}[/]"

    console.line()
    console.rule(title, characters="=", style="#c562af")
    console.line()


def highlighted_nodeid(item: pytest.Item) -> Text:
    from pytest_textualize import NodeItemHighlighter

    text = Text()
    node_highlighter = NodeItemHighlighter()
    text.append_text(node_highlighter(item.nodeid.partition("::")[0])).append("::", style="pytest.node_separator")
    if hasattr(item, "originalname"):
        text.append(item.originalname, style="pytest.node_originalname")
    else:
        text.append(item.name.partition("[")[0])
    if hasattr(item, "callspec"):
        text.append_text(Text(f"[{item.callspec.id}]", style="pytest.node_id"))
    return text

def key_value_scope(items: Iterable[tuple[str, RenderableType]]) -> RenderableType:
    table = Table.grid(
        Column("name", style="#8DECB4 i", width=15),
        Column("value", style="#F6F0F0", width=61),
        padding=(0, 1),
        expand=True,
    )
    # a2e2f8
    table.box = box.HEAVY_HEAD
    table.style = "#BDB395 dim"
    for item in items:
        k, v = item

        table.add_row(f" - {k}", v)
    return Padding(table, (0, 0, 0, 6))
