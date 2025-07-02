from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.highlighter import Highlighter
    from pytest_textualize.typist import SyntaxThemeType


# https://textual.textualize.io/widgets/progress_bar/
# https://waylonwalker.com/rich-syntax-range-style/
# https://oleksis.github.io/awesome-textualize-projects/#third-party-applications
class ThemeFactory:
    @staticmethod
    def rich_ansi_color_names() -> None: ...

    @staticmethod
    def save_style() -> None: ...

    @staticmethod
    def create_styles_file() -> None: ...

    @staticmethod
    def print_styles() -> None: ...

    @staticmethod
    def argparse_highlighter() -> Highlighter:
        from pytest_textualize.textualize.theme.highlighters import ArgparseArgsHighlighter

        return ArgparseArgsHighlighter()

    @staticmethod
    def path_highlighter() -> Highlighter:
        from rich.traceback import PathHighlighter

        return PathHighlighter()

    @staticmethod
    def builtins_highlighter() -> Highlighter:
        from pytest_textualize.textualize.theme.highlighters import BuiltInsExceptionsHighlighter

        return BuiltInsExceptionsHighlighter()

    @staticmethod
    def repr_highlighter() -> Highlighter:
        from rich.highlighter import ReprHighlighter

        return ReprHighlighter()

    @staticmethod
    def syntax_theme() -> SyntaxThemeType:
        from pytest_textualize.textualize.theme.syntax import RichTextualizeSyntaxTheme

        return RichTextualizeSyntaxTheme()
