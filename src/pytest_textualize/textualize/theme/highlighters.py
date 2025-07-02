from __future__ import annotations

from rich.highlighter import RegexHighlighter
from glom import glom


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

        tokens = Python2Lexer.tokens
        prefix = glom(tokens, "builtins.2.0.prefix")
        suffix = glom(tokens, "builtins.2.0.suffix")
        words = glom(tokens, "builtins.2.0.words")
        for word in words:
            cls.highlights.append(f"r'{prefix}{word}{suffix}'")
