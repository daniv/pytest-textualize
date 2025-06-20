# Project : pytest-textualize
# File Name : rich_utils_tests.py
# Dir Path : tests/rich_tests

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from hamcrest import assert_that
from hamcrest import equal_to

try:
    from interegular import logger as interegular_logger

    has_interegular = True
except ImportError:
    has_interegular = False

import pytest_textualize._lazy_rich as r
from pytest_textualize.rich_utils import rich_strip
from pytest_textualize.rich_utils import rich_wrap
from pytest_textualize.textualize.theme.themes import TextualizeTheme
from rich_tests import LOREM_SHORT

if TYPE_CHECKING:
    pass

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


def test_argparse(pytestconfig: pytest.Config) -> None:
    import argparse

    parser = pytestconfig._parser
    groups = parser._groups
    parser = pytestconfig.getoption("--pytest-textualize")

    arg_parser = argparse.ArgumentParser(
        prog="python -m lark.tools.serialize",
        description="Lark Serialization Tool - Stores Lark's internal state & LALR analysis as a JSON file",
        epilog="Look at the Lark documentation for more info on the options",
    )
    new_parser = argparse.ArgumentParser(add_help=False)
    # for option in self.definition.options:
    #     parser.add_argument(
    #         f"--{option.name}",
    #         *([f"-{option.shortcut}"] if option.shortcut else []),
    #         action="store_true" if option.is_flag() else "store",
    #     )
