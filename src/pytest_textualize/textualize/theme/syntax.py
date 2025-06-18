# Project : pytest-textualize
# File Name : syntax.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations

from rich.color import Color
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Name,
    Number,
    Operator,
    String,
    Token,
    Whitespace,
)
from rich.style import Style
from rich.syntax import ANSISyntaxTheme
from rich.syntax import TokenType

PYCHARM_DARK: dict[TokenType, Style] = {
    Token: Style(),
    Whitespace: Style(color="bright_black"),
    Comment: Style(dim=True),
    Comment.Preproc: Style(color="bright_cyan"),
    Keyword: Style(color=Color.from_rgb(207, 142, 109)),
    Keyword.Type: Style(color="bright_cyan"),
    Operator.Word: Style(color="bright_magenta"),
    Name.Builtin: Style(color="bright_cyan"),
    Name.Function: Style(color="bright_green"),
    Name.Namespace: Style(color="bright_cyan"),
    Name.Class: Style(color=Color.from_rgb(207, 142, 109)),
    Name.Exception: Style(color=Color.parse("#8888C6"), bold=True),
    Name.Decorator: Style(color=Color.parse("#B3AE60"), bold=True),
    Name.Variable: Style(color="bright_red"),
    Name.Funcion.Magic: Style(color=Color.parse("#B200B2")),
    Name.Constant: Style(color="bright_red"),
    Name.Attribute: Style(color="bright_cyan"),
    Name.Tag: Style(color="bright_blue"),
    String: Style(color=Color.parse("#6AAB73")),
    Number: Style(color=Color.from_rgb(42, 172, 184)),
    Generic.Deleted: Style(color="bright_red"),
    Generic.Inserted: Style(color="bright_green"),
    Generic.Heading: Style(bold=True),
    Generic.Subheading: Style(color="bright_magenta", bold=True),
    Generic.Prompt: Style(bold=True),
    Generic.Error: Style(color="bright_red"),
    Error: Style(color="red"),
}


class RichTextualizeSyntaxTheme(ANSISyntaxTheme):
    def __init__(self) -> None:
        super().__init__(PYCHARM_DARK)
