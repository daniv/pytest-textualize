# Project : pytest-textualize
# File Name : exceptions.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

import shlex
import sys
from dataclasses import InitVar
from dataclasses import dataclass
from dataclasses import field
from subprocess import CalledProcessError
from typing import Self
from typing import TYPE_CHECKING
from contextlib import suppress

import pytest
from _pytest.config import ExitCode
from rich.text import Text

from pytest_textualize import Verbosity
from pytest_textualize.helpers import Comparable
from pytest_textualize.textualize.console import is_markup

if TYPE_CHECKING:
    from rich.console import Console
    from rich.text import TextType



def decode(string: bytes | str, encodings: list[str] | None = None) -> str:
    if not isinstance(string, bytes):
        return string

    encodings = encodings or ["utf-8", "latin1", "ascii"]

    for encoding in encodings:
        with suppress(UnicodeEncodeError, UnicodeDecodeError):
            return string.decode(encoding)

    return string.decode(encodings[0], errors="ignore")


class TextualizeError(Exception):
    pass


@dataclass
class ConsoleMessage:
    """
    Representation of a console message, providing utilities for formatting text
    with tags, indentation, and sections.

    The ConsoleMessage class is designed to represent text messages that might be
    displayed in a console or terminal output. It provides features for managing
    formatted text, such as stripping tags, wrapping text with specific tags,
    indenting, and creating structured message sections.
    """
    text: str
    debug: bool = False

    @property
    def stripped(self) -> str:
        if is_markup(self.text):
            txt = Text.from_markup(self.text)
            return txt.plain
        return self.text

    def style(self, tag: str) -> Self:
        if self.text:
            self.text = Text(self.text, style=tag).markup
        return self

    def indent(self, indent: str) -> ConsoleMessage:
        if self.text:
            self.text = f"\n{indent}".join(self.text.splitlines()).strip()
            self.text = f"{indent}{self.text}"
        return self

    def make_section(self, title: str, indent: str = "", style: str | None = None) -> Self:
        if not self.text:
            return self.text

        if self.text:
            section = [f"[b]{title}:[/b]"] if title else []
            if style:
                self.style(style)
            section.extend(self.text.splitlines())
            self.text = f"\n{indent}".join(section).strip()

        return self


@dataclass
class PrettyCalledProcessError:
    """
    Represents a formatted and decorated error object for a subprocess call.

    This class is used to encapsulate information about a `CalledProcessError`,
    providing additional context such as command output, errors, and helpful
    debugging messages. It is particularly useful for wrapping and decorating
    subprocess-related exceptions in a more user-friendly format.

    Attributes:
        message: A string representation of the exception.
        output: A section formatted representation of the exception stdout.
        errors: A section formatted representation of the exception stderr.
        command_message: Formatted message including a hint on retrying the original command.
        command: A `shelex` quoted string representation of the original command.
        exception: The original `CalledProcessError` instance.
        indent: Indent prefix to use for inner content per section.
    """

    message: ConsoleMessage = field(init=False)
    output: ConsoleMessage = field(init=False)
    errors: ConsoleMessage = field(init=False)
    command_message: ConsoleMessage = field(init=False)
    command: str = field(init=False)
    exception: InitVar[CalledProcessError] = field(init=True)
    indent: InitVar[str] = field(default="")

    def __post_init__(self, exception: CalledProcessError, indent: str) -> None:
        self.message = ConsoleMessage(str(exception).strip(), debug=True).make_section("Exception", indent)
        self.output = ConsoleMessage(decode(exception.stdout), debug=True).make_section("Output", indent)
        self.errors = ConsoleMessage(decode(exception.stderr), debug=True).make_section("Errors", indent)
        self.command = (
            shlex.join(exception.cmd)
            if isinstance(exception.cmd, list)
            else exception.cmd
        )
        self.command_message = ConsoleMessage(
            f"You can test the failed command by executing:\n\n    <c1>{self.command}</c1>",
            debug=False,
        )
        
class TextualizeRuntimeError(TextualizeError):
    """
    Represents a runtime error in the pytest-textualize console application.
    """
    """
    Represents a runtime error in the Poetry console application.
    """

    def __init__(
        self,
        reason: str,
        messages: list[ConsoleMessage] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(reason)
        self.exit_code = exit_code
        self._messages = messages or []
        self._messages.insert(0, ConsoleMessage(reason))

    def write(self, error_console: Console, verbose: Verbosity) -> None:
        """
        Write the error text to the provided IO iff there is any text to write.
        """
        debug = verbose > Verbosity.NORMAL
        if text := self.get_text(debug=debug, strip=False):
            error_console.print(text)

    def get_text(
        self, debug: bool = False, indent: str = "", strip: bool = False
    ) -> str:
        """
        Convert the error messages to a formatted string. All empty messages
        are ignored along with debug level messages if `debug` is `False`.
        """
        text = ""
        has_skipped_debug = False

        for message in self._messages:
            if message.debug and not debug:
                has_skipped_debug = True
                continue

            message_text = message.stripped if strip else message.text
            if not message_text:
                continue

            if indent:
                message_text = f"\n{indent}".join(message_text.splitlines())

            text += f"{indent}{message_text}\n{indent}\n"

        if has_skipped_debug:
            message = ConsoleMessage(
                f"{indent}You can also run your [#9EC6F3]pytest[/] command with [#9EC6F3]-v|-vv|-vvv[/] to see more information.\n{indent}\n"
            )
            text += message.stripped if strip else message.text

        return text.rstrip(f"{indent}\n")

    def __str__(self) -> str:
        return self._messages[0].stripped.strip()

    @classmethod
    def create(
        cls,
        reason: str,
        exception: CalledProcessError | Exception | None = None,
        info: list[str] | str | None = None,
    ) -> Self:
        """
        Create an instance of this class using the provided reason. If
        an exception is provided, this is also injected as a debug
        `ConsoleMessage`.

        There is specific handling for known exception types. For example,
        if exception is of type `subprocess.CalledProcessError`, the following
        sections are additionally added when available - stdout, stderr and
        command for testing.
        """
        if isinstance(info, str):
            info = [info]

        messages: list[ConsoleMessage] = [
            ConsoleMessage( "\n".join(info or []), debug=False).style("logging.level.info")
        ]

        if isinstance(exception, CalledProcessError):
            error = PrettyCalledProcessError(exception, indent="    | ")
            messages = [
                error.message.style("logging.level.warning"),
                error.output.style("logging.level.warning"),
                error.errors.style("logging.level.warning"),
                *messages,
                error.command_message,
            ]
        elif exception is not None and isinstance(exception, Exception):

            messages.insert(
                0,
                ConsoleMessage(
                    f"[scope.key]description: [/][#c6c688]{exception.__doc__}[/]\n[scope.key]message: [/]{str(exception)}", debug=True
                ).make_section(f"[#8888C6]{type(exception).__name__}[/]", indent="    | "),
            )

        return cls(reason, messages)

    def append(self, message: str | ConsoleMessage) -> Self:
        if isinstance(message, str):
            message = ConsoleMessage(message)
        self._messages.append(message)
        return self
