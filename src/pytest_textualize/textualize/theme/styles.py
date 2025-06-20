# Project : "pytest-textualize
# File Name : styles.py
# Dir Path : src/"pytest_textualize/textualize/theme
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal
from typing import TYPE_CHECKING

from pydantic import NewPath
from pydantic import TypeAdapter
from rich.color import ANSI_COLOR_NAMES
from rich.color import Color
from rich.style import Style
from rich.theme import Theme

if TYPE_CHECKING:
    from pytest_textualize import TextualizeSettings
    from rich.console import Console

    SystemColorLiteral = Literal["auto", "standard", "256", "truecolor", "windows"]

COLOR_NAMES = ANSI_COLOR_NAMES

# noinspection DuplicatedCode
HOOK = "pytest.hook"
HOOK_NAME = "pytest.hookname"
KEY_NAME = "pytest.keyname"
KEY_ITEM = "pytest.item"
KEY_PASSED = "pytest.passed"
KEY_FAILED = "pytest.failed"
KEY_SKIPPED = "pytest.skipped"
KEY_ERROR = "pytest.error"
KEY_SEPARATOR = "pytest.separator"
KEY_XFAILED = "pytest.xfailed"
KEY_XPASSED = "pytest.xpassed"
KEY_DESELECTED = "pytest.deselected"
# noinspection DuplicatedCode


# noinspection DuplicatedCode


# noinspection DuplicatedCode


TEXTUALIZE: dict[str, Style] = {
    HOOK: Style(color="bright_green"),
    HOOK_NAME: Style(color="bright_yellow"),
    KEY_NAME: Style(color="bright_blue"),
    KEY_ITEM: Style(color="bright_white"),
    KEY_PASSED: Style(color="bright_green"),
    KEY_FAILED: Style(color="bright_red"),
    KEY_SKIPPED: Style(color="orange3"),
    KEY_ERROR: Style(color="bright_red"),
    KEY_SEPARATOR: Style(color="bright_green"),
    KEY_XFAILED: Style(color="dark_orange"),
    KEY_XPASSED: Style(color="orange1"),
    KEY_DESELECTED: Style(color="bright_white", dim=True),
}

# -- https://colorhunt.co/
VIOLETTE: dict[str, Style] = {
    "L1": Style(color=Color.parse("#B33791")),
    "L2": Style(color=Color.parse("#C562AF")),
    "L3": Style(color=Color.parse("#DB8DD0")),
    "L4": Style(color=Color.parse("#FEC5F6")),
}

# -- https://www.canva.com/colors/color-palettes/
BRIGHT_LIGHTS: dict[str, Style] = {
    "L1": Style(color=Color.from_rgb(191, 215, 237)),
    "L2": Style(color=Color.from_rgb(96, 163, 217)),
    "L3": Style(color=Color.from_rgb(0, 116, 183)),
    "L4": Style(color=Color.from_rgb(0, 59, 115)),
}

TEXTUALIZE_THEMES: Mapping[str, Theme] = {
    "truecolor": Theme(
        {
            "BLUE5": Style(color=Color.parse("#B3C8CF")),
            "pytest.line_comment": Style(color=Color.parse("#51829B")),
            "BLUE7": Style(color=Color.parse("#F2F2F2")),
            "BLUE8": Style(color=Color.parse("#C2D0E9")),
            "pytest.hookname": Style(color=Color.parse("#91ACDF")),
            "BLUE10": Style(color=Color.parse("#EEE9DA")),
            "pytest.info": Style(color=Color.parse("#BDCDD6")),
            "BLUE12": Style(color=Color.parse("#93BFCF")),
            "pytest.hook": Style(color=Color.parse("#6096B4")),
            "pytest.panel.border": Style(color=Color.parse("#94DAFF"), bold=False),
            "pytest.prefix": Style(color=Color.parse("#4DA8DA"), bold=True),
            "pytest.eeee.dim": Style(color=Color.parse("#3674B5"), dim=True),
            "comment33": Style(color=Color.parse("#3674b5")),
            "pink1": Style(color=Color.parse("#FEC5F6")),
            "pink1_dim": Style(color=Color.parse("#FEC5F6"), dim=True),
            "pink2": Style(color=Color.parse("#DB8DD0")),
            "pink3": Style(color=Color.parse("#C562AF")),
            "pink4": Style(color=Color.parse("#B33791")),
            "comment2": Style(color=Color.parse("#DBDBDB"), dim=True),
            "pytest.comment": Style(color=Color.parse("#7A7E85"), dim=True),
        },
        inherit=False,
    )
}


def save_style(group_name: str, styles: dict[str, Style]) -> None:
    theme = Theme(styles)
    filepath = Path.cwd().parent / "static/styles" / f"{group_name}.ini"
    with open(filepath, "wt") as write_theme:
        write_theme.write(theme.config)


def create_styles_file(settings: TextualizeSettings, color_system: SystemColorLiteral) -> Path:
    theme = TEXTUALIZE_THEMES.get(color_system)
    dest_path = TypeAdapter(NewPath).validate_python(settings.style_files.get(color_system, None))
    with open(dest_path, "wt") as write_theme:
        write_theme.write(theme.config)
    return dest_path


def print_styles(console: Console, color_system: SystemColorLiteral) -> None:
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit"
    theme = TEXTUALIZE_THEMES.get(color_system)
    for n, s in theme.styles.items():
        console.print(repr(s), style="dim")
        console.print(f"style name: '{n}'", lorem, style=s)
        console.line()
    return
