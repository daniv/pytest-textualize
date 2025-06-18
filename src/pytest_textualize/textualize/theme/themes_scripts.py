# Project : pytest-textualize
# File Name : themes_scripts.py
# Dir Path : src/pytest_textualize/textualize/theme
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest_textualize._lazy_rich as r
from rich.color import ANSI_COLOR_NAMES

from pytest_textualize.textualize.theme.testing import ARGPARSE_COLOR_THEMES

if TYPE_CHECKING:
    from rich.console import Console


def show_themes(console: Console) -> None:
    for theme_name in ARGPARSE_COLOR_THEMES.keys():
        RichHelpFormatterPlus.choose_theme(theme_name)
        console.line(3)
        title_panel = r.Panel(f" {theme_name}    ", width=50, expand=False, style='bright_white')
        console.print(title_panel, justify='center')
        console.line()
        _print_help_text()
