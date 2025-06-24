from __future__ import annotations

import logging
from enum import StrEnum
from importlib import metadata
from typing import TYPE_CHECKING
from typing import assert_never

import pytest

__all__ = (
    "console_factory", "__version__", "configure_logging", "PrefixEnum", "keyval_msg",
    "get_bool_opt", "get_int_opt", "get_list_opt", "literal_to_list", "hook_msg", "report_pytest_textualize_header",
    "ArgparseArgsHighlighter", "RichTextualizeSyntaxTheme", "Verbosity", "stage_rule",
    "highlighted_nodeid", "NodeItemHighlighter", "key_value_scope", "TextualizePlugins"

)
# "ConsoleMessage", "PytestTextualizeRuntimeError"

__version__ = metadata.version("pytest_textualize")


from pytest_textualize.helpers import get_bool_opt
from pytest_textualize.helpers import get_int_opt
from pytest_textualize.helpers import get_list_opt
from pytest_textualize.helpers import literal_to_list
from pytest_textualize.settings import Verbosity
from pytest_textualize.textualize.console import PrefixEnum
from pytest_textualize.textualize.console import pytest_textualize_header as report_pytest_textualize_header
from pytest_textualize.textualize.console import stage_rule
from pytest_textualize.textualize.console import highlighted_nodeid
from pytest_textualize.textualize.console import key_value_scope
from pytest_textualize.textualize.theme.highlighters import ArgparseArgsHighlighter
from pytest_textualize.textualize.theme.highlighters import NodeItemHighlighter
from pytest_textualize.textualize.theme.syntax import RichTextualizeSyntaxTheme
# from pytest_textualize.plugins.pytest_richtrace.exceptions import PytestTextualizeRuntimeError
# from pytest_textualize.plugins.pytest_richtrace.exceptions import ConsoleMessage

if TYPE_CHECKING:
    from collections.abc import Sequence
    from rich.style import StyleType
    from rich.text import TextType
    from rich.table import Table
    from typing import Literal
    from rich.console import Console, ConsoleRenderable
    from pytest_textualize.settings import TextualizeSettings
    from pytest_textualize.textualize.console import TracerMessage
    from pytest_textualize.textualize.console import KeyValueMessage

class TextualizePlugins(StrEnum):
    PLUGIN = "pytest-textualize-plugin"
    TRACER = "textualize-tracer"
    ERROR_TRACER = "textualize-error-tracer"
    COLLECTOR_TRACER = "textualize-collector-tracer"
    RUNTEST_TRACER = "textualize-runtest-tracer"
    REGISTRATION_SERVICE = "textualize-registration-service"
    REPORTER = "textualize-reporter"




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

def hook_msg(
    hookname: str,
    *,
    console: Console | None = None,
    prefix: PrefixEnum = PrefixEnum.PREFIX_SQUARE,
    info: TextType | None = None,
    escape: bool = False,
    highlight: bool = False,
) -> Table | None:

    from pytest_textualize.textualize.console import TracerMessage
    trm = TracerMessage(hookname, prefix=prefix, info=info, highlight=highlight, escape=escape)
    if console is not None:
        trm(console)
    return trm(None)

def keyval_msg(
        key: str,
        value: TextType | ConsoleRenderable,
        *,
        console: Console | None = None,
        prefix: PrefixEnum = PrefixEnum.PREFIX_BULLET,
        value_style: StyleType | None = "",
        escape: bool = False,
        highlight: bool = False,
) -> Table | None:
    from pytest_textualize.textualize.console import KeyValueMessage
    kvm = KeyValueMessage(key, value, prefix=prefix, value_style=value_style, highlight=highlight, escape=escape)
    if console is not None:
        kvm(console)
    return kvm(None)
