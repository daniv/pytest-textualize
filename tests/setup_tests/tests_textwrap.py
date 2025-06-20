# Project : pytest-textualize
# File Name : tests_textwrap.py
# Dir Path : tests/setup_tests

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

import pytest

from rich_tests import LOREM_SHORT

if TYPE_CHECKING:
    from rich.console import Console

parameterize = pytest.mark.parametrize


def test_textwrap_fill(console: Console) -> None:
    fill = textwrap.fill(LOREM_SHORT, width=10)
    if console:
        console.line(2)
        console.print(fill)


def test_textwrap_fill_initial_indent(console: Console) -> None:
    fill = textwrap.fill(
        LOREM_SHORT,
        width=15,
        initial_indent=" - ",
    )
    if console:
        console.line(2)
        console.rule("w=15, initial_indent=' - '")
        console.print(fill)


def test_textwrap_fill_subsequent_indent(console: Console) -> None:
    fill = textwrap.fill(
        LOREM_SHORT,
        width=15,
        subsequent_indent=" - ",
    )
    if console:
        console.line(2)
        console.rule("w=15, subsequent_indent=' - '")
        console.print(fill)


def test_textwrap_fill_subsequent_and_initial(console: Console) -> None:
    fill = textwrap.fill(LOREM_SHORT, width=15, initial_indent=" - ", subsequent_indent="   * ")
    if console:
        console.line(2)
        console.rule("w=15, initial_indent=' - ', subsequent_indent='   * ")
        console.print(fill)


def test_textwrap_fill_subsequent_and_initial_expand_tabs(console: Console) -> None:
    fill = textwrap.fill(
        LOREM_SHORT, width=15, initial_indent=" - ", subsequent_indent="   * ", expand_tabs=False
    )
    if console:
        console.line(2)
        console.rule("w=15, initial_indent=' - ', subsequent_indent='   * ")
        console.print(fill)


def test_textwrap_shorten() -> None:
    pass


def test_textwrap_dedent(console: Console) -> None:
    # end first line with \ to avoid the empty line!
    s = """\
      hello
        world
      """
    if console:
        console.line(2)
        console.rule("no dedent")
        console.print(repr(s))  # prints '    hello\n      world\n    '
        console.rule("with dedent")
        console.print(repr(textwrap.dedent(s)))  # prints 'hello\n  world\n'


def test_textwrap_indent() -> None:
    pass
