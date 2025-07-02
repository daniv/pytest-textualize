from __future__ import annotations

from pygments.token import Comment
from pygments.token import Error
from pygments.token import Generic
from pygments.token import Keyword
from pygments.token import Name
from pygments.token import Number
from pygments.token import Operator
from pygments.token import String
from pygments.token import Token
from pygments.token import Whitespace
from rich.color import Color
from rich.style import Style
from rich.syntax import ANSISyntaxTheme
from rich.syntax import TokenType
from rich.console import Console


PYCHARM_DARK: dict[TokenType, Style] = {
    Token: Style(),
    Whitespace: Style(color=Color.parse("#FFB8E0")),
    Comment: Style(dim=True),
    Comment.Preproc: Style(color=Color.parse("#ffb8e0")),
    Keyword: Style(color=Color.parse("#CF8E6D")),  # def, if , raise, else
    Keyword.Type: Style(color=Color.parse("#ffb8e0")),
    Operator.Word: Style(color=Color.parse("#CF8E6D"), bold=True),  # and or, not
    Name.Builtin: Style(color=Color.parse("#8888C6")),  # bool, int , float, str
    Name.Function: Style(color=Color.parse("#56A8F5")),  # function names
    Name.Namespace: Style(color=Color.parse("#BCBEC4")),
    Name.Class: Style(color=Color.parse("#BCBEC4")),
    Name.Exception: Style(color=Color.parse("#8888C6"), bold=True),  # exceptions
    Name.Decorator: Style(color=Color.parse("#B3AE60"), bold=False),
    Name.Funcion.Magic: Style(color=Color.parse("#B200B2")),
    Name.Variable: Style(color=Color.parse("#B200B2")),  # __class__, __name___
    Name.Constant: Style(color=Color.parse("bright_green")),
    Name.Attribute: Style(color=Color.parse("#ffb8e0")),
    Name.Tag: Style(color=Color.parse("bright_green")),
    String: Style(color=Color.parse("#6AAB73")),  # strings
    Number: Style(color=Color.parse("#2AACB8")),  # numbers
    Generic.Deleted: Style(color=Color.parse("#11b8e0")),
    Generic.Inserted: Style(color=Color.parse("#ffb8e0")),
    Generic.Heading: Style(bold=True),
    Generic.Subheading: Style(color=Color.parse("#ffb8e0"), bold=True),
    Generic.Prompt: Style(bold=True),
    Generic.Error: Style(color=Color.parse("#ffb8e0")),
    Error: Style(color=Color.parse("bright_green"), underline=True),
}


class RichTextualizeSyntaxTheme(ANSISyntaxTheme):
    def __init__(self) -> None:
        super().__init__(PYCHARM_DARK)


def syntax_compare(file: str, console: Console) -> None:
    import linecache
    from rich.syntax import Syntax

    code_lines = linecache.getlines(file)
    code = "".join(code_lines)
    syntax = Syntax(
        code,
        lexer="python",
        code_width=console.width - 20,
        line_numbers=True,
        theme=Syntax.get_theme("ansi_dark"),
        indent_guides=True,
        highlight_lines={3},
        padding=1,
        start_line=1,
        dedent=False,
    )
    # console.print(syntax)
    syntax = Syntax(
        code,
        lexer="python",
        code_width=console.width - 20,
        line_numbers=True,
        theme=Syntax.get_theme("pycharm_dark"),
        indent_guides=True,
        highlight_lines={3},
        padding=1,
        start_line=1,
        dedent=True,
    )
    console.print(syntax)
