# Project : pytest-textualize
# File Name : highlighters.py
# Dir Path : src/pytest_textualize/textualize/theme
from __future__ import annotations

from typing import TYPE_CHECKING

from rich.highlighter import RegexHighlighter

if TYPE_CHECKING:
    pass


class ArgparseArgsHighlighter(RegexHighlighter):
    base_style = "argparse."
    highlights: list[str] = [
        r"(?:^|\s)(?P<args>-{1,2}[\w]+[\w-]*)",  # highlight --words-with-dashes as args
        r"`(?P<syntax>[^`]*)`",  # highlight text in backquotes as syntax
    ]


class BuiltInsExceptionsHighlighter(RegexHighlighter):
    base_style = "exc."

    highlights: list[str] = []

    # noinspection PyUnresolvedReferences
    @classmethod
    def add_highlights(cls) -> None:
        from pygments.lexers.python import Python2Lexer
        from glom import glom

        tokens = Python2Lexer.tokens
        prefix = glom(tokens, "builtins.2.0.prefix")
        suffix = glom(tokens, "builtins.2.0.suffix")
        words = glom(tokens, "builtins.2.0.words")
        for word in words:
            cls.highlights.append(f"r'{prefix}{word}{suffix}'")
