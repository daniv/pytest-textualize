# Project : pytest-textualize
# File Name : settings.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations

import logging
from abc import ABC
from collections.abc import Iterable
from collections.abc import Mapping
from enum import IntEnum
from pathlib import Path
from typing import Any
from typing import Literal
from typing import TYPE_CHECKING

import pytest
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from rich.syntax import ANSISyntaxTheme
from rich.syntax import SyntaxTheme

if TYPE_CHECKING:
    from rich.console import Console
    from rich.theme import Theme

EmojiVariant = Literal["emoji", "text"]
ColorSystemVariant = Literal["auto", "standard", "256", "truecolor", "windows"]

STYLE_INI_FILES: Mapping[str, Path] = {
    "truecolor": Path("static/styles") / "truecolor_styles.ini",
    "standard": Path("static/styles") / "standard_styles.ini",
    "eight_bit": Path("static/styles") / "eight_bit_styles.ini",
}


def locate(filename: str, cwd: Path | None = None) -> Path:
    """locates a specific file or directory starting by default on Path.cwd

    :param filename: The file name, or directory to search
    :param cwd: An additional candidate working directory to search
    :return: The Path object
    """
    __tracebackhide__ = True

    cwd = Path(cwd or Path.cwd())
    candidates = [cwd]
    candidates.extend(cwd.parents)

    for path in candidates:
        requested_file = path / filename

        if requested_file.is_file():
            return requested_file

    raise FileNotFoundError(f"Could not located the file '{filename}'")


class Verbosity(IntEnum):
    QUIET = -1  # --quiet
    NORMAL = 0
    VERBOSE = 1  # -v
    VERY_VERBOSE = 2  # -vv
    DEBUG = 3  # -vvv


class DotEnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        title="Pytest-Textualize DotEnv Settings Source",
        env_file=locate(".env", Path.cwd()),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_ignore_empty=False,
        env_nested_delimiter="--",
        env_parse_none_str="None",
        env_parse_enums=False,
    )
    py_colors: int


class ConsolePyProjectSettings(BaseModel):
    model_config = ConfigDict(
        title="Console Settings", validate_default=True, validate_assignment=True
    )
    color_system: ColorSystemVariant = Field(
        default="auto",
        description="he color system supported by your terminal, 'standard', '256' or 'truecolor'. Leave as 'auto' to autodetect.",
    )
    force_terminal: bool | None = Field(
        None,
        description="Enable/disable terminal control codes, or None to auto-detect terminal, default to None",
    )
    force_jupyter: bool | None = Field(
        None,
        description="Enable/disable Jupyter rendering, or None to auto-detect Jupyter. Defaults to None.",
    )
    force_interactive: bool | None = Field(
        None,
        description="Enable/disable interactive mode, or None to auto detect. Defaults to None.",
    )
    soft_wrap: bool = Field(
        False, description="Set soft wrap default on print method. Defaults to False."
    )
    no_color: bool | None = Field(
        None, description="Enabled no color mode, or None to auto detect. Defaults to None."
    )
    tab_size: int = Field(
        8, ge=4, description="Number of spaces used to replace a tab character. Defaults to 8."
    )
    markup: bool = Field(True, description="Enable/disable markup mode. Defaults to True.")
    emoji: bool = Field(True, description="Enable/disable emoji mode. Defaults to True.")
    emoji_variant: EmojiVariant | None = Field(
        None, description="Optional emoji variant, either 'text' or 'emoji'. Defaults to None."
    )
    highlight: bool = Field(
        True, description="Enable/disable automatic highlight mode. Defaults to True."
    )
    log_time: bool = Field(
        True,
        description="Boolean to enable logging of time by <method: log> methods. Defaults to True.",
    )
    log_path: bool = Field(
        True, description="the logging of the caller by <method: log>. Defaults to True."
    )
    highlighter: str | None = Field(
        None, description="Default highlighter is rich.highlighter.ReprHighlighter."
    )
    theme: str | None = Field(
        None, description=" An optional style theme object, or None for default theme."
    )
    legacy_windows: bool | None = Field(
        None, description="Enable legacy Windows mode, or None to auto detect. Defaults to None"
    )
    safe_box: bool | None = Field(
        None, description="Restrict box options that don't render on legacy Windows."
    )

    argparse_theme: str = Field("mother_earth")

    @property
    def terminal_size_fallback(self) -> dict[str, str]:
        return {"COLUMNS": "190", "LINES": "25"}

    def get_theme(self, color_system: ColorSystemVariant) -> Theme:
        from pydantic import TypeAdapter
        from pydantic import FilePath

        from rich.theme import Theme

        if color_system == "truecolor":
            path = STYLE_INI_FILES.get("truecolor")
        elif color_system == "falsecolor":
            path = STYLE_INI_FILES.get("standard")
        else:
            path = STYLE_INI_FILES.get("eight_bit")

        from rich_argparse_plus.themes import ARGPARSE_COLOR_THEMES

        filepath = locate(str(path))
        argparse_theme = Theme(ARGPARSE_COLOR_THEMES.get(self.argparse_theme), inherit=False)
        filepath = TypeAdapter(FilePath).validate_python(filepath)
        theme = Theme.read(str(filepath))
        theme.styles.update(argparse_theme.styles)
        return theme

    def model_post_init(self, context: Any, /) -> None:
        from pydantic_settings import PyprojectTomlConfigSettingsSource

        class Settings(BaseSettings):
            model_config = SettingsConfigDict(
                pyproject_toml_table_header=("tool", "textualize-settings", "console"),
                pyproject_toml_depth=4
            )

        s = PyprojectTomlConfigSettingsSource(Settings)
        for k, v in s.toml_data.items():
            setattr(self, k, v)


class PyprojectModel(BaseModel):
    path: Path | None = None
    data: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, context: Any, /) -> None:
        from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource

        class Settings(BaseSettings):
            model_config = SettingsConfigDict(toml_file=locate("pyproject.toml"))

        toml = TomlConfigSettingsSource(Settings)
        self.data = toml.toml_data
        self.path = Path(toml.toml_file_path).resolve()


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        pyproject_toml_table_header=("tool", "textualize-settings", "logging"),
        pyproject_toml_depth=4
    )


class _TracebacksAbstractModel(BaseModel, ABC):
    locals_max_string: int = Field(
        80, description="Maximum length of string before truncating.", ge=20
    )

    locals_max_length: int = Field(
        10, description="Maximum length of containers before abbreviating.", ge=1, le=20
    )


class TracebacksPyProjectSettings(_TracebacksAbstractModel):
    model_config = ConfigDict(
        title="Tracebacks Configuration Settings",
        arbitrary_types_allowed=True,
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
    )
    width: int = Field(100, description="Number of characters used to traceback. Defaults to 100.")
    code_width: int = Field(
        88, description="Number of code characters used to render tracebacks.", gt=80
    )
    extra_lines: int = Field(3, description="Additional lines of code to render tracebacks.", ge=0)
    theme: str = Field(
        "ansi_dark",
        alias="theme",
        title="Tracebacks Theme",
        description="Override pygments theme used in traceback.",
    )
    word_wrap: bool = Field(True, description="Enable word wrapping of long tracebacks lines.")
    show_locals: bool = Field(False, description="Enable display of locals in tracebacks.")
    locals_hide_dunder: bool = Field(
        True, description="Hide locals prefixed with double underscore."
    )
    locals_hide_sunder: bool = Field(
        False, description="Hide locals prefixed with single underscore."
    )
    indent_guides: bool = Field(True, description="Enable indent guides in code and locals.")
    suppress: Iterable[str] = (
        Field((), description="Optional sequence of modules or paths to exclude from traceback."),
    )
    max_frames: int = Field(
        100, title="Max Frames", description="Maximum number of frames returned by traceback.", ge=1
    )

    syntax_theme: SyntaxTheme | None = None

    def model_post_init(self, context: Any, /) -> None:
        from pydantic_settings import PyprojectTomlConfigSettingsSource

        class Settings(BaseSettings):
            model_config = SettingsConfigDict(
                pyproject_toml_table_header=("tool", "textualize-settings", "tracebacks"),
                pyproject_toml_depth=4
            )

        s = PyprojectTomlConfigSettingsSource(Settings)
        for k, v in s.toml_data.items():
            setattr(self, k, v)

        if self.theme == "pycharm_dark":
            from pytest_textualize.textualize.theme.syntax import PYCHARM_DARK
            self.syntax_theme = ANSISyntaxTheme(PYCHARM_DARK)
        else:
            from rich.syntax import Syntax
            self.syntax_theme = Syntax.get_theme(self.syntax_theme)


class LoggingPyProjectSettings(_TracebacksAbstractModel):
    model_config = ConfigDict(
        title="Logging Configuration Settings",
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
    )

    level: int | str = Field(logging.NOTSET, description="Log level. Defaults to logging.NOTSET.")

    show_time: bool = Field(True, description="Show a column for the time. Defaults to True.")

    omit_repeated_times: bool = Field(
        True, description="Omit repetition of the same time. Defaults to True."
    )

    show_level: bool = Field(True, description="Show a column for the level. Defaults to True.")

    show_path: bool = Field(
        True, description="Show the path to the original log call. Defaults to True."
    )

    enable_link_path: bool = Field(True, description="Enable terminal link of path column to file. Defaults to True.")

    highlighter: str | None = Field(
        None, description="Highlighter to style log messages, or None to use ReprHighlighter"
    )

    markup: bool = Field(
        False, description="Enable console markup in log messages. Defaults to False."
    )

    rich_tracebacks: bool = Field(
        False,
        description="Enable rich tracebacks with syntax highlighting and formatting. Defaults to False.",
    )
    tracebacks_width: int | None = Field(
        None,
        description="Number of characters used to render tracebacks, or None for full width. Defaults to None.",
    )

    tracebacks_code_width: int = Field(
        88,
        description="Number of code characters used to render tracebacks, or None for full width. Defaults to 88.",
    )
    tracebacks_extra_lines: int = Field(
        3,
        description="Additional lines of code to render tracebacks, or None for full width. Defaults to None.",
    )

    tracebacks_theme: str = Field(
        "ansi_dark",
        alias="theme",
        title="Tracebacks Theme",
        description="Override pygments theme used in traceback.",
    )
    tracebacks_word_wrap: bool = Field(
        True, description="Enable word wrapping of long tracebacks lines. Defaults to True."
    )

    tracebacks_show_locals: bool | None = Field(
        False, description="Enable display of locals in tracebacks. Defaults to False."
    )

    tracebacks_suppress: Iterable[str] = Field(
        (), description="Optional sequence of modules or paths to exclude from traceback."
    )

    tracebacks_max_frames: int = Field(
        100,
        description="Optional maximum number of frames returned by traceback. Default to 100"
    )

    log_time_format: str | None = Field(
        "[%x %X]",
        description="If log_time is enabled, a string for strftime or callable that formats the time. Defaults to '[%x %X]'",
    )

    keywords: list[str] | None = Field(
        [], description="List of words to highlight instead of ``RichHandler.KEYWORDS``."
    )

    def model_post_init(self, context: Any, /) -> None:
        from pydantic_settings import PyprojectTomlConfigSettingsSource

        class Settings(BaseSettings):
            model_config = SettingsConfigDict(
                pyproject_toml_table_header=("tool", "textualize-settings", "logging"),
                pyproject_toml_depth=4
            )

        s = PyprojectTomlConfigSettingsSource(Settings)
        for k, v in s.toml_data.items():
            setattr(self, k, v)


class TextualizeSettings(BaseSettings):
    model_config = SettingsConfigDict(title="Pytest Textualize Settings")
    env: DotEnvSettings = Field(default_factory=DotEnvSettings)
    pyproject: PyprojectModel = Field(default_factory=PyprojectModel)
    tracebacks_settings: TracebacksPyProjectSettings | None = Field(
        default_factory=TracebacksPyProjectSettings,
        description="The rich tracebacks settings",
    )
    logging_settings: LoggingPyProjectSettings = Field(
        default_factory=LoggingPyProjectSettings,
        description="The rich logging settings",
    )
    console_settings: ConsolePyProjectSettings = Field(default_factory=ConsolePyProjectSettings)
    verbosity: Verbosity = Field(Verbosity.NORMAL)
    log_format: str | None = Field("%(message)s", description="The logging.formatter template")
    pytest_config: pytest.Config

    def model_post_init(self, context: Any, /) -> None:
        from _pytest.logging import get_option_ini

        self.verbosity = self.pytest_config.getoption("--verbose")
        self.log_format = get_option_ini(self.pytest_config, "log_file_format", "log_format")
        self.logging_settings.level = get_option_ini(self.pytest_config, "log_level")
        self.logging_settings.tracebacks_show_locals = self.pytest_config.getoption("--showlocals")
        self.logging_settings.log_time_format = get_option_ini(self.pytest_config, "log_date_format")
        self.tracebacks_settings.show_locals = self.pytest_config.getoption("--showlocals")
        # "dotenv_path"


settings_key = pytest.StashKey[TextualizeSettings]()
