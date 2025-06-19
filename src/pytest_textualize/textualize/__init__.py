# Project : pytest-textualize
# File Name : __init__.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations

from enum import IntEnum

from pytest_textualize.settings import locate
from pytest_textualize.textualize.theme.highlighters import ArgparseArgsHighlighter
from pytest_textualize.textualize.theme.highlighters import BuiltInsExceptionsHighlighter
from pytest_textualize.textualize.theme.styles.error_report_styles import ERREP_COLOR_THEMES
from pytest_textualize.textualize.theme.styles.error_report_styles import ERREP_CAUSE
from pytest_textualize.textualize.theme.styles.error_report_styles import ERREP_COLON
from pytest_textualize.textualize.theme.styles.error_report_styles import ERREP_GROUPS
from pytest_textualize.textualize.theme.styles.error_report_styles import ERREP_ARGS
from pytest_textualize.textualize.theme.styles.error_report_styles import ERREP_EXCTYPE
from pytest_textualize.textualize.theme.styles.error_report_styles import STYLE_PREFIX
from pytest_textualize.textualize.theme.syntax import RichTextualizeSyntaxTheme
from pytest_textualize.textualize.theme.terminal_theme import TEXTUALIZE_TERMINAL_THEME

__all__ = (
    "locate",
    "ArgparseArgsHighlighter",
    "BuiltInsExceptionsHighlighter",
    "TEXTUALIZE_TERMINAL_THEME",
    "RichTextualizeSyntaxTheme",
    "TextualizeTheme",
    "ERREP_COLOR_THEMES", "ERREP_CAUSE", "ERREP_COLON", "ERREP_GROUPS", "ERREP_ARGS", "ERREP_EXCTYPE", "STYLE_PREFIX"
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
