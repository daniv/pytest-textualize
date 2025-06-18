# Project : pytest-textualize
# File Name : formatter.py
# Dir Path : src/pytest_textualize/textualize/theme
from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path
from rich.theme import Theme

if TYPE_CHECKING:
    pass

COLOR_THEMES = [
    "default", "morning_glory"
]


class TextualizeTheme(Theme):
    theme_name: str = 'default'
    themes_path = Path.cwd().parent / "static/themes"

    def __init__(self, filepath: str) -> None:
        theme_from_file = Theme.read(str(filepath))
        super().__init__(theme_from_file.styles, False)

    @classmethod
    def choose_theme(cls, theme_name: str | None = None) -> TextualizeTheme:
        if theme_name is None:
            theme_name = cls.theme_name

        if theme_name not in COLOR_THEMES:
            raise ValueError(f"{theme_name} is not a theme. (Themes: {COLOR_THEMES})")

        cls.theme_name = theme_name
        filename = cls.themes_path / f"{theme_name}.ini"
        return cls(filename)

    @classmethod
    def save_theme(cls, theme: Theme, name: str) -> None:
        filepath = cls.themes_path / f"{name}.ini"
        with open(filepath, "wt") as write_theme:
            write_theme.write(theme.config)
