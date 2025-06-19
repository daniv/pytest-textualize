# Project : "pytest-textualize
# File Name : styles.py
# Dir Path : src/"pytest_textualize/textualize/theme
from __future__ import annotations

from pathlib import Path

from rich.color import ANSI_COLOR_NAMES
from rich.style import Style
from rich.color import Color
from rich.theme import Theme

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


def save_style(group_name: str, styles: dict[str, Style]) -> None:
    theme = Theme(styles)
    filepath = Path.cwd().parent / "static/styles" / f"{group_name}.ini"
    with open(filepath, "wt") as write_theme:
        write_theme.write(theme.config)
