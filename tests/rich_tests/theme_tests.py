# Project : pytest-textualize
# File Name : theme_tests.py
# Dir Path : tests/rich_tests

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Sized
from typing import TypeVar
import pytest
from pytest import param
from pytest import mark
from hamcrest import assert_that
from hamcrest import equal_to
from rich.color import Color
from rich.style import Style
from rich.theme import Theme

import pytest_textualize._lazy_rich as r

from pytest_textualize.textualize.theme.themes import TextualizeTheme
from rich_tests import LOREM_SHORT

if TYPE_CHECKING:
    from rich.console import Console

parameterize = pytest.mark.parametrize


def test_theme(console: Console) -> None:
    theme = TextualizeTheme.choose_theme("morning_glory")
    console.push_theme(theme)
    for style in ["pytest.args", "pytest.text", "pytest.groups", "pytest.help", "pytest.metavar", "pytest.prog",
                  "pytest.syntax"]:
        console.print(LOREM_SHORT, style=style)


def test_theme_create():
    theme = Theme({
        "pytest.er": Style(color=Color.from_ansi(230)),
        "pytest.22": Style(color=Color.from_ansi(230), bold=True, dim=True)
    }, inherit=False)

    filepath = Path.cwd().parent / f"static/themes/fuck.ini"
    with open(filepath, "wt") as write_theme:
        write_theme.write(theme.config)
