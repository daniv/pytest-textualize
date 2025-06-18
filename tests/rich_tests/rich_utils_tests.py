# Project : pytest-textualize
# File Name : rich_utils_tests.py
# Dir Path : tests/rich_tests

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from hamcrest import assert_that
from hamcrest import equal_to

import pytest_textualize._lazy_rich as r
from pytest_textualize.rich_utils import rich_strip
from pytest_textualize.rich_utils import rich_wrap
from pytest_textualize.textualize.theme.themes import TextualizeTheme
from rich_tests import LOREM_SHORT

if TYPE_CHECKING:
    from rich.console import Console

parameterize = pytest.mark.parametrize


@parameterize(
    "string, expected",
    [("   Pycharm  ", "Pycharm"), ("   using [red]pytest[/]   ", "using pytest")],
)
def test_rich_strip(console: r.Console, string: str, expected: str) -> None:
    text = r.Text(string)
    strip = rich_strip(text)
    assert_that(strip.plain, equal_to(expected), "rich_strip")
    if console:
        console.line(1)
        console.print(strip)


def test_rich_wrap(console: r.Console) -> None:
    text = r.Text(LOREM_SHORT)
    text.wrap(console, 20)

    wrapped = rich_wrap(console, text, 20)
    if console:
        console.line(1)
        console.print(wrapped)
