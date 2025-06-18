# Project : pytest-textualize
# File Name : __init__.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations

from enum import IntEnum

from pytest_textualize.settings import locate
from pytest_textualize.textualize.theme.highlighters import ArgparseArgsHighlighter
from pytest_textualize.textualize.theme.highlighters import BuiltInsExceptionsHighlighter
from pytest_textualize.textualize.theme.syntax import RichTextualizeSyntaxTheme
from pytest_textualize.textualize.theme.terminal_theme import TEXTUALIZE_TERMINAL_THEME

__all__ = (
    "locate",
    "ArgparseArgsHighlighter",
    "BuiltInsExceptionsHighlighter",
    "TEXTUALIZE_TERMINAL_THEME",
    "RichTextualizeSyntaxTheme",
    "TextualizeTheme",
)

from pytest_textualize.textualize.theme.themes import TextualizeTheme


class Verbosity(IntEnum):
    QUIET = -1  # --quiet
    NORMAL = 0
    VERBOSE = 1  # -v
    VERY_VERBOSE = 2  # -vv
    DEBUG = 3  # -vvv


class OutputType(IntEnum):
    NORMAL = 1
    RAW = 2
