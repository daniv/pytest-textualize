from __future__ import annotations

import logging
from enum import StrEnum
from importlib import metadata
from pathlib import Path
from typing import Final
from typing import TYPE_CHECKING
from typing import assert_never

import pytest

__all__ = (
    "console_factory", "__version__", "configure_logging",
    "get_bool_opt", "get_int_opt", "get_list_opt", "literal_to_list",
    "is_list_of_strings", "TextualizePlugins", "TS_BASE_PATH",
    "PYPROJECT_PATH", "STYLES_PATH", "STATIC_PATH", "TESTS_PATH", "DOT_ENV_PATH", "trace_logger",
    "config_trace_logger"

)

__version__ = metadata.version("pytest_textualize")


from pytest_textualize.helpers import get_bool_opt
from pytest_textualize.helpers import get_int_opt
from pytest_textualize.helpers import get_list_opt
from pytest_textualize.helpers import literal_to_list
from pytest_textualize.helpers import is_list_of_strings

if TYPE_CHECKING:
    from pytest_textualize.textualize.verbose_log import Verbosity
    from typing import Literal
    from rich.console import Console
    from pytest_textualize.settings import TextualizeSettings
    from pytest_textualize.plugin.model import Error
    from pytest_textualize.textualize.verbose_log import ConsoleLogger


class TextualizePlugins(StrEnum):
    PLUGIN = "pytest-textualize-plugin"
    TRACER = "textualize-tracer"
    ERROR_TRACER = "textualize-error-tracer"
    COLLECTOR_TRACER = "textualize-collector-tracer"
    RUNTEST_TRACER = "textualize-runtest-tracer"
    REGISTRATION_SERVICE = "textualize-registration-service"
    REPORTER = "textualize-reporter"
    PLUGGY_COLLECTOR_SERVICE = "pluggy-collector-service"
    PYTEST_COLLECTOR_SERVICE = "pytest-collector-service"
    POETRY_COLLECTOR_SERVICE = "poetry-collector-service"
    PYTHON_COLLECTOR_SERVICE = "python-collector-service"
    HOOKS_COLLECTOR_SERVICE = "hooks-collector-service"
    COLLECTOR_WRAPPER = "collector-wrapper"
    SUMMARY_SERVICE = "summary-service"


TS_BASE_PATH: Final = Path().resolve()
PYPROJECT_PATH: Final = TS_BASE_PATH / "pyproject.toml"
TESTS_PATH = TS_BASE_PATH / "tests"
DOT_ENV_PATH = TS_BASE_PATH / ".env"
STATIC_PATH = TS_BASE_PATH / "static"
STYLES_PATH = STATIC_PATH / "styles"

def reset_logging() -> None:
    # -- Remove all handlers from the root logger
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    # -- Reset logger hierarchy, this clears the internal dict of loggers
    logging.Logger.manager.loggerDict.clear()

def configure_logging(console: Console, txt_settings: TextualizeSettings) -> None:
    log_file_handler: logging.FileHandler | None = None

    log_level = txt_settings.logging.level
    if isinstance(log_level, str):
        log_level = logging.getLevelName(log_level)
    try:
        from rich.logging import RichHandler
        from .textualize.logging import TextualizeConsoleLogRender, TextualizeConsoleHandler
        logging_options = txt_settings.logging.model_dump(exclude_unset=True, exclude={"level"})
        rich_handler = TextualizeConsoleHandler(log_level, console, **logging_options)
    except ValueError as e:
        if str(e).startswith("Unknown level"):
            from pytest import UsageError
            raise UsageError(
                f"'{log_level}' is not recognized as a logging level name for "
                f"'log_level'. Please consider passing the logging level num instead."
            ) from e
        raise e from e

    reset_logging()
    logging.basicConfig(
        level=logging.NOTSET,
        format=txt_settings.log_format,
        datefmt=txt_settings.logging.log_time_format,
        handlers=[rich_handler],
    )
    logging.captureWarnings(True)

def console_factory(config: pytest.Config, instance: Literal["stdout", "stderr", "buffer", "null"]) -> Console:
    from pytest_textualize.console_factory import ConsoleFactory

    match instance:
        case "stdout":
            return ConsoleFactory.console_stdout(config)
        case "stderr":
            return ConsoleFactory.console_stderr(config)
        case "buffer":
            return ConsoleFactory.console_buffer(config)
        case "null":
            return ConsoleFactory.console_null(config)
        case _:
            assert_never(instance)


from pytest_textualize.textualize.verbose_log import ConsoleLogger
_LOGGER: ConsoleLogger | None = None

def trace_logger() -> ConsoleLogger:
    return _LOGGER


def config_trace_logger(*, verbosity: int | str | Verbosity, showlocals: bool = False) -> ConsoleLogger:
    global _LOGGER

    if _LOGGER is None:
        _LOGGER = ConsoleLogger(verbosity, showlocals)
    return _LOGGER
