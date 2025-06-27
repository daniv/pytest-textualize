from __future__ import annotations
from __future__ import annotations

import logging
import sys
import threading
from enum import IntEnum
from types import TracebackType
from typing import Annotated
from typing import Any
from typing import Literal
from typing import Mapping
from typing import MutableMapping
from typing import NoReturn
from typing import TYPE_CHECKING
from typing import Type
from typing import overload

from annotated_types import Ge
from annotated_types import Le
from boltons.dictutils import OneToOne
from pydantic import TypeAdapter
from rich.console import Console

from pytest_textualize import literal_to_list

if TYPE_CHECKING:
    from pytest_textualize.typist import IntStr
    from rich.console import JustifyMethod
    from rich.style import Style
    from pytest_textualize.settings import TextualizeSettings


class Verbosity(IntEnum):
    QUIET = -1  # --quiet
    NORMAL = 0
    VERBOSE = 1  # -v
    VERY_VERBOSE = 2  # -vv
    DEBUG = 3  # -vvv


VerbosityNames = Literal[
    Verbosity.QUIET, Verbosity.NORMAL, Verbosity.VERBOSE, Verbosity.VERY_VERBOSE, Verbosity.DEBUG
]

_m2m = OneToOne(
    {
        Verbosity.QUIET: Verbosity.QUIET.name,
        Verbosity.NORMAL: Verbosity.NORMAL.name,
        Verbosity.VERBOSE: Verbosity.VERBOSE.name,
        Verbosity.VERY_VERBOSE: Verbosity.VERY_VERBOSE.name,
        Verbosity.DEBUG: Verbosity.DEBUG.name,
    }
)


@overload
def get_verbosity(value: VerbosityNames) -> Verbosity: ...


@overload
def get_verbosity(value: int) -> Verbosity: ...


def get_verbosity(value: IntStr) -> Verbosity | NoReturn:
    if isinstance(value, int):
        valid = Annotated[int, Ge(Verbosity.QUIET), Le(Verbosity.DEBUG)]
        level = TypeAdapter(valid).validate_python(value)
        return Verbosity(level)
    elif isinstance(value, str):
        level_name = TypeAdapter(VerbosityNames).validate_python(value.upper())
        return _m2m.inv.get(level_name)
    valid_values = (
        f"Error value type: valid values are: '[{", ".join(literal_to_list(VerbosityNames))}]'"
        f" or a number between {Verbosity.QUIET} and {Verbosity.DEBUG}"
    )
    raise TypeError(valid_values)


def get_logging_level(verbosity: Verbosity) -> int:
    match verbosity:
        case Verbosity.QUIET:
            return logging.NOTSET
        case Verbosity.NORMAL:
            return logging.ERROR
        case Verbosity.VERBOSE:
            return logging.WARNING
        case Verbosity.VERY_VERBOSE:
            return logging.INFO
        case _:
            return logging.DEBUG


class ConsoleLogger:
    def __init__(self, verbose: Verbosity | str | int = Verbosity.NORMAL, showlocals: bool = False):
        """Initialize the logger with a name and an optional level."""

        self.verbosity = get_verbosity(verbose)
        self.disabled = False
        self.show_locals: bool = showlocals
        self._consoles: dict[str, Console] = dict[str, Console]()
        self.lock = threading.Lock()
        self._settings: TextualizeSettings | None = None

    def __repr__(self):
        verbose = self.verbosity.name
        return "<%s %s (showlocals=%s)>" % (self.__class__.__name__, verbose, self.show_locals)

    def add_console(self, console: Console) -> None:
        assert isinstance(console, Console)
        if console.stderr:
            self._consoles["stderr"] = console
        else:
            self._consoles["stdout"] = console

    @property
    def consoles(self) -> Mapping[str, Console]:
        return self._consoles

    def settings(self, settings: TextualizeSettings) -> None:
        self._settings = settings

    def set_show_locals(self, show_locals: bool) -> None:
        self.show_locals = show_locals

    def set_disabled(self, disabled: bool) -> None:
        self.disabled = disabled

    def set_verbose(self, verbose: int | str | Verbosity) -> None:
        if isinstance(verbose, Verbosity):
            self.verbosity = verbose
        else:
            get_verbosity(verbose)

    def debug(self, *messages: Any, **kwargs) -> None:
        if self.is_enabled_for(Verbosity.DEBUG):
            kwargs["prefix"] = "[logging.level.debug]▪ [/]"
            self._log(*messages, level=logging.DEBUG, **kwargs)

    def info(self, *messages: Any, **kwargs) -> None:
        if self.is_enabled_for(Verbosity.VERY_VERBOSE):
            kwargs["prefix"] = "[logging.level.info]▪ [/]"
            self._log(*messages, level=logging.INFO, **kwargs)

    def warning(self, *messages: Any, **kwargs) -> None:
        if self.is_enabled_for(Verbosity.VERBOSE):
            kwargs["prefix"] = "[logging.level.warning]▪ [/]"
            self._log(*messages, level=logging.WARNING, **kwargs)

    def error(self, *messages: Any, **kwargs) -> None:
        if self.is_enabled_for(Verbosity.NORMAL):
            kwargs["prefix"] = "[logging.level.error]▪ [/]"
            self._log(*messages, level=logging.ERROR, **kwargs)

    def critical(self, *messages: Any, **kwargs) -> None:
        if self.is_enabled_for(Verbosity.QUIET):
            kwargs["prefix"] = "[logging.level.critical]▪ [/]"
            self._log(*messages, level=logging.CRITICAL, **kwargs)

    def log(self, *messages: Any, verbosity: Verbosity, **kwargs) -> None:
        if not isinstance(verbosity, Verbosity):
            raise TypeError("level must be an integer")
        if self.is_enabled_for(verbosity):
            self._log(*messages, level=get_logging_level(verbosity), **kwargs)

    def exception(self, *messages: Any, exc_info=True, **kwargs):
        """
        Convenience method for logging an ERROR with exception information.
        """
        if exc_info:
            exc_type, exc_value, traceback = sys.exc_info()
            self.from_exception(
                *messages, exc_type=exc_type, exc_value=exc_value, traceback=traceback, **kwargs
            )
        else:
            self.error(*messages, exc_info=exc_info, **kwargs)

    def from_exception(
        self,
        *messages: Any,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        tb: TracebackType | None,
        **kwargs,
    ):
        """Convenience method for logging an ERROR with exception information."""

        self.error(*messages, exc_info=False, **kwargs)

    def is_enabled_for(self, verbose: Verbosity) -> bool:
        """Is this logger enabled for level 'level'?"""
        if self.disabled:
            return False
        return self.verbosity >= verbose

    def _log(
        self,
        *objects: Any,
        level: int,
        exc_info: bool = False,
        prefix: str | None = None,
        sep: str = " ",
        end: str = "\n",
        style: str | Style | None = None,
        justify: JustifyMethod | None = None,
        emoji: bool | None = None,
        markup: bool | None = None,
        highlight: bool | None = None,
    ) -> None:
        if exc_info:
            if isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        if prefix:
            objects = (prefix, *objects)

        if level >= logging.ERROR:
            console = self._consoles.get("stderr")
        else:
            console = self._consoles.get("stdout")

        with self.lock:
            console.log(
                *objects,
                sep=sep,
                end=end,
                justify=justify,
                emoji=emoji,
                markup=markup,
                highlight=highlight,
                log_locals=self.show_locals,
                _stack_offset=3,
            )
