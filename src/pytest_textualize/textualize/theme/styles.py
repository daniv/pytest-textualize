from __future__ import annotations

from typing import Literal
from typing import TYPE_CHECKING

from rich.color import ANSI_COLOR_NAMES

if TYPE_CHECKING:
    from rich.console import Console

SystemColorLiteral = Literal["auto", "standard", "256", "truecolor", "windows"]


def print_styles(console: Console, color_system: SystemColorLiteral) -> None:
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit"
    theme = ANSI_COLOR_NAMES.get(color_system)
    for n, s in theme.styles.items():
        console.print(repr(s), style="dim")
        console.print(f"style name: '{n}'", lorem, style=s)
        console.line()
    return
