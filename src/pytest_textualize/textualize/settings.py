# Project : pytest-textualize
# File Name : settings.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from pathlib import Path
from typing import Any
from typing import Literal
from collections.abc import Iterable
from collections.abc import Callable
from types import ModuleType
from rich.highlighter import Highlighter
import rich.text

if TYPE_CHECKING:
    import rich.style

    ColorSystemVariant = Literal["auto", "standard", "256", "truecolor", "windows"]


def locate(filename: str, cwd: Path | None = None) -> Path:
    """locates a specific file or directory starting by default on Path.cwd

    :param filename: The file name, or directory to search
    :param cwd: An additional candidate working directory to search
    :return: The Path object
    """
    cwd = Path(cwd or Path.cwd())
    candidates = [cwd]
    candidates.extend(cwd.parents)

    for path in candidates:
        requested_file = path / filename

        if requested_file.is_file():
            return requested_file

    raise FileNotFoundError(f"Could not located the file '{filename}'")


class DotEnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        title="Pytest-Textualize DotEnv Settings Source",
        env_file=locate(".env", Path.cwd().parent),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_ignore_empty=False,
        env_nested_delimiter="--",
        env_parse_none_str="None",
        env_parse_enums=False,
    )
    py_colors: int


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


class TextualizePyProjectSettings(BaseSettings):
    model_config = SettingsConfigDict(
        pyproject_toml_table_header=("tool", "textualize-settings"),
    )


class TracebacksSettingsModel(BaseModel):
    model_config = ConfigDict(
        title="Tracebacks Configuration Settings",
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
    )
    code_width: int = Field(
        88, description="Number of code characters used to render tracebacks.", gt=80
    )
    extra_lines: int = Field(3, description="Additional lines of code to render tracebacks.", ge=0)
    syntax_theme: str | None = Field(
        "ansi_dark",
        title="Tracebacks Theme",
        description="Override pygments theme used in traceback.",
    )
    word_wrap: bool = Field(True, description="Enable word wrapping of long tracebacks lines.")
    show_locals: bool = Field(False, description="Enable display of locals in tracebacks.")
    max_frames: int = Field(
        100, title="Max Frames", description="Maximum number of frames returned by traceback.", ge=1
    )
    max_length: int = Field(
        10, description="Maximum length of containers before abbreviating.", ge=1, le=20
    )
    max_string: int = Field(80, description="Maximum length of string before truncating.", ge=20)
    enable_link_path: bool = Field(
        True, strict=True, description="Enable terminal link of path column to file."
    )
    hide_dunder: bool = Field(True, description="Hide locals prefixed with double underscore.")
    hide_sunder: bool = Field(False, description="Hide locals prefixed with single underscore.")
    indent_guides: bool = Field(True, description="Enable indent guides in code and locals.")
    suppress: Iterable[str] = Field(
        (), description=" Optional sequence of modules or paths to exclude from traceback."
    )

    def model_post_init(self, context: Any, /) -> None:
        from pydantic_settings import PyprojectTomlConfigSettingsSource

        obj = PyprojectTomlConfigSettingsSource(
            TextualizePyProjectSettings, locate("pyproject.toml")
        )
        for k, v in obj.toml_data.get("tracebacks", {}).items():
            setattr(self, k, v)


class LoggingSettingsModel(TracebacksSettingsModel):
    model_config = ConfigDict(
        title="Logging Configuration Settings",
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
    )
    log_level: int | str = Field(True, description="Log level. Defaults to logging.NOTSET.")
    show_locals: bool = Field(False, description="Enable display of locals in tracebacks.")
    show_time: bool = Field(True, description="Show a column for the time. Defaults to True.")
    show_level: bool = Field(True, description="Show a column for the level. Defaults to True.")
    show_path: bool = Field(
        True, description="Show the path to the original log call. Defaults to True."
    )
    omit_repeated_times: bool = Field(
        True, description="Omit repetition of the same time. Defaults to True."
    )
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
    log_time_format: str | None = Field(
        "[%X]",
        description="If ``log_time`` is enabled, a string for strftime or callable that formats the time. Defaults to '[%X]'",
    )
    log_format: str | None = Field("%(message)s", description="The logging.formatter template")
    keywords: list[str] | None = Field(
        [], description="List of words to highlight instead of ``RichHandler.KEYWORDS``."
    )

    def model_post_init(self, context: Any, /) -> None:
        from pydantic_settings import PyprojectTomlConfigSettingsSource

        obj = PyprojectTomlConfigSettingsSource(
            TextualizePyProjectSettings, locate("pyproject.toml")
        )
        for k, v in obj.toml_data.get("logging", {}).items():
            setattr(self, k, v)


class TextualizeSettings(BaseSettings):
    model_config = SettingsConfigDict(title="Pytest Textualize Settings")
    env: DotEnvSettings = Field(default_factory=DotEnvSettings)
    pyproject: PyprojectModel = Field(default_factory=PyprojectModel)
    tracebacks: TracebacksSettingsModel | None = Field(
        default_factory=TracebacksSettingsModel,
        description="The rich tracebacks settings",
    )
    logging: LoggingSettingsModel = Field(
        default_factory=LoggingSettingsModel,
        description="The rich logging settings",
    )


try:
    _TEXTUALIZE_SETTINGS = TextualizeSettings()
except ValidationError as e:
    for err in e.errors():
        pass

# _TEXTUALIZE_SETTINGS = TextualizeSettings()


def get_textualize_settings() -> TextualizeSettings:
    global _TEXTUALIZE_SETTINGS
    return _TEXTUALIZE_SETTINGS
