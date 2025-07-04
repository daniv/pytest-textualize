from __future__ import annotations

import logging
from abc import ABC
from collections.abc import Iterable
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from typing import Literal
from typing import TYPE_CHECKING

import pytest
from glom import glom
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import FilePath
from pydantic import PositiveInt
from pydantic import PrivateAttr
from pydantic import TypeAdapter
from pydantic_settings import BaseSettings
from pydantic_settings import PydanticBaseSettingsSource
from pydantic_settings import PyprojectTomlConfigSettingsSource
from pydantic_settings import SettingsConfigDict
from pydantic_settings import TomlConfigSettingsSource
from rich.syntax import ANSISyntaxTheme
from rich.syntax import Syntax
from rich.theme import Theme
from rich_argparse_plus.themes import ARGPARSE_COLOR_THEMES

from pytest_textualize import TS_BASE_PATH

if TYPE_CHECKING:
    from pytest_textualize.typist import SyntaxThemeType
    from pytest_textualize.typist import ThemeType


EmojiVariant = Literal["emoji", "text"]
ColorSystemVariant = Literal["auto", "standard", "256", "truecolor", "windows"]
_ENV_FILE_INI_KEY = "env_file"

STYLE_INI_FILES: Mapping[str, Path] = {
    "truecolor": Path("static/styles") / "truecolor_styles.cfg",
    "standard": Path("static/styles") / "standard_styles.cfg",
    "eight_bit": Path("static/styles") / "eight_bit_styles.cfg",
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


class ConsolePyProjectSettingsModel(BaseModel):
    model_config = ConfigDict(
        title="Console Settings", validate_default=True, validate_assignment=True
    )
    color_system: ColorSystemVariant = Field(
        default="auto",
        description="he color system supported by your terminal, 'standard', '256' or 'truecolor'. Leave as 'auto' to autodetect.",
    )
    force_terminal: bool | None = Field(
        default=None,
        description="Enable/disable terminal control codes, or None to auto-detect terminal, default to None",
    )
    force_jupyter: bool | None = Field(
        default=None,
        description="Enable/disable Jupyter rendering, or None to auto-detect Jupyter. Defaults to None.",
    )
    force_interactive: bool | None = Field(
        default=None,
        description="Enable/disable interactive mode, or None to auto detect. Defaults to None.",
    )
    soft_wrap: bool = Field(
        default=False, description="Set soft wrap default on print method. Defaults to False."
    )
    no_color: bool | None = Field(
        default=None, description="Enabled no color mode, or None to auto detect. Defaults to None."
    )
    tab_size: int = Field(
        default=8,
        ge=4,
        description="Number of spaces used to replace a tab character. Defaults to 8.",
    )
    markup: bool = Field(True, description="Enable/disable markup mode. Defaults to True.")
    emoji: bool = Field(True, description="Enable/disable emoji mode. Defaults to True.")
    emoji_variant: EmojiVariant | None = Field(
        default=None,
        description="Optional emoji variant, either 'text' or 'emoji'. Defaults to None.",
    )
    highlight: bool = Field(
        default=True, description="Enable/disable automatic highlight mode. Defaults to True."
    )
    log_time: bool = Field(
        default=True,
        description="Boolean to enable logging of time by <method: log> methods. Defaults to True.",
    )
    log_path: bool = Field(
        default=True, description="the logging of the caller by <method: log>. Defaults to True."
    )
    highlighter: str | None = Field(
        default=None, description="Default highlighter is rich.highlighter.ReprHighlighter."
    )
    theme: str | None = Field(
        default=None, description=" An optional style theme object, or None for default theme."
    )
    legacy_windows: bool | None = Field(
        default=None,
        description="Enable legacy Windows mode, or None to auto detect. Defaults to None",
    )
    safe_box: bool | None = Field(
        default=None, description="Restrict box options that don't render on legacy Windows."
    )

    @property
    def argparse_theme(self) -> str:
        return "mother_earth"

    @property
    def environ(self) -> Mapping[str, str]:
        return {"COLUMNS": "200", "LINES": "25"}

    def get_theme(self, color_system: ColorSystemVariant) -> ThemeType:

        if color_system == "truecolor":
            path = STYLE_INI_FILES.get("truecolor")
        elif color_system in ["standard", "256"]:
            path = STYLE_INI_FILES.get("standard")
        else:
            path = STYLE_INI_FILES.get("eight_bit")

        filepath = locate(str(path))
        argparse_theme = Theme(ARGPARSE_COLOR_THEMES.get(self.argparse_theme), inherit=False)
        filepath = TypeAdapter(FilePath).validate_python(filepath)
        theme = Theme.read(str(filepath))
        theme.styles.update(argparse_theme.styles)
        return theme


class TracebacksAbstractModel(BaseModel, ABC):
    locals_max_string: PositiveInt = Field(
        default=80, description="Maximum length of string before truncating.", ge=20
    )

    locals_max_length: PositiveInt = Field(
        default=10, description="Maximum length of containers before abbreviating.", ge=1, le=20
    )


class TracebacksPyProjectSettingsModel(TracebacksAbstractModel):
    model_config = ConfigDict(
        title="Tracebacks Configuration Settings",
        arbitrary_types_allowed=True,
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
    )
    width: PositiveInt = Field(
        default=100, description="Number of characters used to traceback. Defaults to 100."
    )
    code_width: PositiveInt = Field(
        default=88, description="Number of code characters used to render tracebacks.", gt=80
    )
    extra_lines: PositiveInt = Field(
        default=3, description="Additional lines of code to render tracebacks.", ge=0
    )
    theme: str = Field(
        "ansi_dark",
        alias="theme",
        title="Tracebacks Theme",
        description="Override pygments theme used in traceback.",
    )
    word_wrap: bool = Field(
        default=True, description="Enable word wrapping of long tracebacks lines."
    )
    show_locals: bool = Field(default=False, description="Enable display of locals in tracebacks.")
    locals_hide_dunder: bool = Field(
        default=True, description="Hide locals prefixed with double underscore."
    )
    locals_hide_sunder: bool = Field(
        default=False, description="Hide locals prefixed with single underscore."
    )
    indent_guides: bool = Field(True, description="Enable indent guides in code and locals.")
    suppress: Iterable[str] = (
        Field(
            default=(),
            description="Optional sequence of modules or paths to exclude from traceback.",
        ),
    )
    max_frames: PositiveInt = Field(
        default=100,
        title="Max Frames",
        description="Maximum number of frames returned by traceback.",
        ge=1,
    )

    _syntax_theme: SyntaxThemeType | None = PrivateAttr(default=None)

    def model_post_init(self, context: Any, /) -> None:
        if self.theme == "pycharm_dark":

            from pytest_textualize.textualize.theme.syntax import PYCHARM_DARK

            self._syntax_theme = ANSISyntaxTheme(PYCHARM_DARK)
        else:
            self._syntax_theme = Syntax.get_theme(self._syntax_theme)


class LoggingPyProjectSettingsModel(TracebacksAbstractModel):
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

    enable_link_path: bool = Field(
        default=True, description="Enable terminal link of path column to file. Defaults to True."
    )

    highlighter: str | None = Field(
        default=None,
        description="Highlighter to style log messages, or None to use ReprHighlighter",
    )

    markup: bool = Field(
        default=False, description="Enable console markup in log messages. Defaults to False."
    )

    rich_tracebacks: bool = Field(
        default=False,
        description="Enable rich tracebacks with syntax highlighting and formatting. Defaults to False.",
    )
    tracebacks_width: int | None = Field(
        default=None,
        description="Number of characters used to render tracebacks, or None for full width. Defaults to None.",
    )

    tracebacks_code_width: int = Field(
        default=88,
        description="Number of code characters used to render tracebacks, or None for full width. Defaults to 88.",
    )

    tracebacks_extra_lines: int = Field(
        default=3,
        description="Additional lines of code to render tracebacks, or None for full width. Defaults to None.",
    )

    tracebacks_theme: str = Field(
        default="ansi_dark",
        title="Tracebacks Theme",
        description="Override pygments theme used in traceback.",
    )
    tracebacks_word_wrap: bool = Field(
        default=True, description="Enable word wrapping of long tracebacks lines. Defaults to True."
    )

    tracebacks_show_locals: bool | None = Field(
        default=False, description="Enable display of locals in tracebacks. Defaults to False."
    )

    tracebacks_suppress: Iterable[str] = Field(
        default=(), description="Optional sequence of modules or paths to exclude from traceback."
    )

    tracebacks_max_frames: int = Field(
        default=100,
        description="Optional maximum number of frames returned by traceback. Default to 100",
    )

    log_time_format: str = Field(
        default="[%x %X]",
        description="If log_time is enabled, a string for strftime Defaults to '[%x %X]'",
    )

    log_format: str | None = Field(
        default="%(message)s", description="The logging.formatter template"
    )

    keywords: list[str] | None = Field(
        default_factory=list,
        description="List of words to highlight instead of ``RichHandler.KEYWORDS``.",
    )

    def get_field_value(self, field: FieldInfo, field_name: str) -> Any:
        return glom(self.model_fields, f"{field_name}.{field}")


class TextualizeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        title="Pytest Textualize Settings",
        pyproject_toml_depth=3,
        pyproject_toml_table_header=("tool", "textualize-settings"),
        toml_file=TS_BASE_PATH / "pyproject.toml",
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        env_parse_none_str="None",
        extra="forbid",
    )
    py_colors: int | None = Field(
        default=0,
        title="PY_COLORS",
        alias="PY_COLORS",
        description="This environment variable used for pytest to enforce terminal colors (location .env), see PY_COLORS",
        frozen=True,
        ge=0,
        le=1,
    )
    pytestconfig: pytest.Config = Field(
        ...,
        description=(
            "This settings class must be initiated with pytestconfig, since there are configuration dependencies"
        ),
        title="pytest.config",
    )

    tracebacks_settings: TracebacksPyProjectSettingsModel = Field(
        default_factory=TracebacksPyProjectSettingsModel, alias="tracebacks"
    )
    logging_settings: LoggingPyProjectSettingsModel = Field(
        default_factory=LoggingPyProjectSettingsModel, alias="logging"
    )
    console_settings: ConsolePyProjectSettingsModel = Field(
        default_factory=ConsolePyProjectSettingsModel, alias="console"
    )

    project: Mapping[str, Any] = Field(default_factory=dict, alias="project")
    pyproject: Mapping[str, Any] = Field(default_factory=dict, alias="project")
    tool: Mapping[str, Any] = Field(default_factory=dict)
    toml_file: Path | None = Field(default=None)
    build_system: Mapping[str, Any] = Field(default_factory=dict, alias="build-system")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            env_settings,
            init_settings,
            PyprojectTomlConfigSettingsSource(settings_cls),
            TomlConfigSettingsSource(settings_cls),
        )

    def model_post_init(self, context: Any, /) -> None:
        from _pytest.logging import get_option_ini

        # self.toml_file = self.model_config.get("toml_file")
        # from boltons.fileutils import iter_find_files
        # filenames = sorted(iter_find_files(str(self.pytestconfig.rootpath), '*.lock'))
        # if filenames:
        #     self.lock_file = Path(filenames[-1])
        #     self.pyproject = {"project": self.project, "tool": self.tool, "build-system": self.build_system}
        self.logging_settings.log_format = get_option_ini(self.pytestconfig, "log_format")
        self.logging_settings.level = get_option_ini(self.pytestconfig, "log_level")
        self.logging_settings.tracebacks_show_locals = self.pytestconfig.getoption("--showlocals")
        self.logging_settings.log_time_format = get_option_ini(self.pytestconfig, "log_date_format")
        self.tracebacks_settings.show_locals = self.pytestconfig.getoption("--showlocals")
