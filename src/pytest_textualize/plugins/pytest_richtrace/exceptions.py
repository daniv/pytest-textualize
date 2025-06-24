# Project : pytest-textualize
# File Name : exceptions.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

import sys
from dataclasses import dataclass
from subprocess import CalledProcessError
from typing import Self
from typing import TYPE_CHECKING

from rich.text import Text
from pytest_textualize.textualize.stirps_tags import strip_tags

if TYPE_CHECKING:
    from rich.console import Console
    from rich.text import TextType


class PytestTextualizeError(Exception):
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

    text: TextType


    @property
    def stripped(self) -> str:

        return strip_tags(self.text)

    def style(self, tag: str) -> Self:
        if self.text:
            self.text = Text(self.text, style=tag)
        return self

    def indent(self, indent: str) -> ConsoleMessage:
        if self.text:
            self.text = f"\n{indent}".join(self.text.splitlines()).strip()
            self.text = f"{indent}{self.text}"
        return self

    def make_section(self, title: str, indent: str = "") -> Self:
        if not self.text:
            return self

        if self.text:
            section = [f"[b]{title}:[/]"] if title else []
            section.extend(self.text.splitlines())
            self.text = f"\n{indent}".join(section).strip()

        return self


class PytestTextualizeRuntimeError(PytestTextualizeError):
    """
    Represents a runtime error in the pytest-textualize console application.
    """

    def __init__(
        self,
        reason: str,
        messages: list[ConsoleMessage] | None = None
    ) -> None:
        super().__init__(reason)
        self._messages = messages or []
        self._messages.insert(0, ConsoleMessage(reason))

    def write(self, console: Console, verbose: int) -> None:
        """
        Write the error text to the provided IO iff there is any text
        to write.
        """
        if text := self.get_text(debug=verbose > 0, strip=False):
            console.print(text)

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
                f"{indent}You can also run your <c1>pytes</> command with <c1>-v</> to see more information.\n{indent}\n"
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
        Create an instance of this class using the provided reason. If an exception is provided,
        this is also injected as a debug `ConsoleMessage`.

        There is specific handling for known exception types. For example,
        if exception is of type `subprocess.CalledProcessError`, the following
        sections are additionally added when available - stdout, stderr and
        command for testing.
        """
        if isinstance(info, str):
            info = [info]

        messages: list[ConsoleMessage] = [
            ConsoleMessage(
                "\n".join(info or []),
                debug=False,
            ).wrap("info"),
        ]

        if isinstance(exception, CalledProcessError):
            error = "PrettyCalledProcessError"(exception, indent="    | ")
            messages = [
                error.message.wrap("warning"),
                error.output.wrap("warning"),
                error.errors.wrap("warning"),
                *messages,
                error.command_message,
            ]
        elif exception is not None and isinstance(exception, Exception):
            messages.insert(
                0,
                ConsoleMessage(str(exception), debug=True).make_section(
                    "Exception", indent="    | "
                ),
            )

        return cls(reason, messages)

    def append(self, message: str | ConsoleMessage) -> Self:
        if isinstance(message, str):
            message = ConsoleMessage(message)
        self._messages.append(message)
        return self
