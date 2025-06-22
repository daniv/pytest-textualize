from __future__ import annotations

from importlib import metadata
import logging
from typing import TYPE_CHECKING

from rich.console import Console
from rich.logging import RichHandler

__version__ = metadata.version("pytest_textualize")

from pytest_textualize.console_factory import ConsoleFactory
from pytest_textualize.helpers import get_bool_opt
from pytest_textualize.settings import ConsolePyProjectSettingsModel
from pytest_textualize.settings import TextualizeSettings
from pytest_textualize.settings import TracebacksPyProjectSettingsModel
from pytest_textualize.settings import LoggingPyProjectSettingsModel

__all__ = [
    "TextualizeSettings",
    "ConsoleFactory",
    "ConsolePyProjectSettingsModel",
    "TracebacksPyProjectSettingsModel",
    "LoggingPyProjectSettingsModel",
    "get_bool_opt",
    "reset_logging",
    "configure_logging",
    "__version__",
]

if TYPE_CHECKING:
    from pytest import Config


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

def tracer_message(
    hookname: str,
    *,
    console: Console | None = None,
    prefix: PrefixEnum = PrefixEnum.PREFIX_SQUARE,
    info: TextType | None = None,
    escape: bool = False,
    highlight: bool = False,
) -> TracerMessage:

    from pytest_textualize.textualize.console import TracerMessage
    trm = TracerMessage(hookname, prefix=prefix, info=info, highlight=highlight, escape=escape)
    if console is not None:
        trm(console)
    return trm
