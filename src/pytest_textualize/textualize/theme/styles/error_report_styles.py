# Project : errep-textualize
# File Name : error_report_styles.py
# Dir Path : src/errep_textualize/textualize/theme/styles
from __future__ import annotations

from typing import TYPE_CHECKING

from black.lines import Callable
from rich.color import Color
from rich.style import Style

if TYPE_CHECKING:
    from rich.style import StyleType

PANEL_PADDING = (2, 1)
STYLE_PREFIX = "errep."
build_style_name: Callable[[str], str] = lambda _type: f"{STYLE_PREFIX}{_type}"

ERREP_ARGS = build_style_name("args")
ERREP_COLON = build_style_name("colon")
ERREP_DEFAULT = build_style_name("default")
ERREP_ADDENDUM = build_style_name("default_string")
ERREP_NUMBER = build_style_name("default_number")
ERREP_TEXT = build_style_name("text")
ERREP_GROUPS = build_style_name("groups")
ERREP_HELP = build_style_name("help")
ERREP_EXCTYPE = build_style_name("metavar")
ERREP_PANEL: str = build_style_name("panel")
ERREP_CAUSE: str = build_style_name("prog")
ERREP_SYNTAX = build_style_name("syntax")
ERRREP_DESCRIPTION = build_style_name("description")

ERREP_COLOR_THEMES: dict[str, dict[str, StyleType]] = {
    'default': {
        ERREP_ARGS: Style(color="cyan"),
        ERREP_DEFAULT: Style(color=Color.from_ansi(245)),
        ERREP_TEXT: Style(color="default"),
        ERREP_GROUPS: Style(color="dark_orange"),
        ERREP_HELP: Style(color="default"),
        ERREP_EXCTYPE: Style(color="dark_cyan"),
        ERREP_NUMBER: Style(color="bright_cyan"),
        ERREP_CAUSE: Style(color=Color.from_ansi(123)),
        ERREP_SYNTAX: Style(bold=True),
    },
    "the_matrix": {
        ERREP_ARGS: Style(color=Color.from_ansi(120), bold=True, dim=True),
        ERREP_TEXT: Style(color=Color.from_ansi(136), dim=True),
        ERREP_GROUPS: Style(color=Color.from_ansi(239)),
        ERREP_HELP: Style(color=Color.from_ansi(114), italic=True),
        ERREP_EXCTYPE: Style(color=Color.from_ansi(83)),
        ERREP_CAUSE: Style(color=Color.from_ansi(235), bold=True),
        ERREP_SYNTAX: Style(color=Color.from_ansi(156), bold=True)
    },
    "morning_glory": {
        ERREP_ARGS: Style(color=Color.from_ansi(230), bold=True, dim=True),
        ERREP_TEXT: Style(color=Color.from_ansi(231), dim=True),
        ERREP_GROUPS: Style(color=Color.from_ansi(231)),
        ERREP_HELP: Style(color=Color.from_ansi(230), italic=True),
        ERREP_EXCTYPE: Style(color=Color.from_ansi(184)),
        ERREP_CAUSE: Style(color=Color.from_ansi(208), bold=True),
        ERREP_SYNTAX: Style(color=Color.from_ansi(190), bold=True),
    }
}

for theme in ERREP_COLOR_THEMES.values():
    if ERREP_ADDENDUM not in theme:
        theme[ERREP_ADDENDUM] = f"{theme[ERREP_EXCTYPE]} bold"
    if ERREP_NUMBER not in theme:
        theme[ERREP_NUMBER] = theme[ERREP_ADDENDUM]

ANTI_THEMES: dict[str, dict[str, StyleType]] = {}

for theme_name, style_dict in ERREP_COLOR_THEMES.items():
    anti_theme = ANTI_THEMES[f"anti_{theme_name}"] = {}

    for element, style in style_dict.items():
        anti_theme[element] = f"{style} reverse"

# def choose_styles(cls, theme_name: str | None = None)
#     if theme_name is None:
#         theme_name = cls.theme_name
#
#     if theme_name not in COLOR_THEMES:
#         raise ValueError(f"{theme_name} is not a theme. (Themes: {COLOR_THEMES})")
#
#     cls.theme_name = theme_name
#     filename = cls.themes_path / f"{theme_name}.ini"
#     return cls(filename)
