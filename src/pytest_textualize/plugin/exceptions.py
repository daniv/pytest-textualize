from __future__ import annotations

import shlex
import sys
from contextlib import suppress
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any
from typing import Self
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from rich.padding import Padding
from rich.panel import Panel
from rich.text import Text

from pytest_textualize import ConsoleMessage
from pytest_textualize import TS_BASE_PATH
from pytest_textualize import Textualize
from pytest_textualize import Verbosity
from pytest_textualize.factories.theme_factory import ThemeFactory
from pytest_textualize.textualize.tracebacks import TextualizeTracebacks

if TYPE_CHECKING:
    from rich.console import Console
    from pytest_textualize.typist import PanelType
    from pytest_textualize.typist import ListStr


def decode(string: bytes | str, encodings: ListStr | None = None) -> str:
    if not isinstance(string, bytes):
        return string

    encodings = encodings or ["utf-8", "latin1", "ascii"]

    for encoding in encodings:
        with suppress(UnicodeEncodeError, UnicodeDecodeError):
            return string.decode(encoding)

    return string.decode(encodings[0], errors="ignore")


class TextualizeError(Exception):
    pass


class PrettyException(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    doc: ConsoleMessage | None = Field(
        default=None, description="The docstring of the exception.", repr=False
    )
    message: ConsoleMessage | None = Field(
        default=None, description="A string representation of the exception"
    )
    indent: str = Field(
        default="", description="Indent prefix to use for inner content per section.", repr=False
    )
    exception: BaseException = Field(
        init=True, description="The original `CalledProcessError` instance."
    )
    location: ConsoleMessage | None = Field(
        default=None, description="A string representation of the location"
    )

    def model_post_init(self, context: Any, /) -> None:
        repr_h = ThemeFactory.repr_highlighter()
        path_h = ThemeFactory.path_highlighter()

        self.doc = ConsoleMessage(text=self.exception.__doc__, debug=True).make_section(
            "Exception doc", indent=self.indent
        )

        self.message = ConsoleMessage(
            text=repr_h(str(self.exception).strip()).markup, debug=True
        ).make_section("Exception", indent=self.indent)

        if type(self).__name__ == "PrettyCalledProcessError":
            return None

        if isinstance(self.exception, SyntaxError):
            frame_summary = self.exception
            path = Path(frame_summary.filename).relative_to(TS_BASE_PATH)
            loc = (
                f"file: {path_h(path.as_posix()).markup}\n"
                f"lineno: [repr.number]{frame_summary.lineno}[/]\n"
                f"text: [python.string]{frame_summary.text.strip()}[/]\n"
            )
        else:
            exc_info = TextualizeTracebacks.from_exception(self.exception)
            traceback_entry = exc_info.traceback[-1]
            relative = Textualize.relative_path(traceback_entry.path)
            link = Textualize.create_link(
                str(traceback_entry.path),
                traceback_entry.lineno,
                sys.stdout.isatty(),
                use_click=True,
            )
            statement = "\n".join(traceback_entry.statement.lines).strip()
            statement = repr_h(statement).markup
            loc = (
                f"file = {path_h(relative.as_posix()).markup}\n"
                f"function = [python.function]{traceback_entry.name}[/]\n"
                f"lineno = [repr.number]{traceback_entry.lineno}[/]\n"
                f"statement = [#67A37C]{statement}[/]\n"
                f"{link.markup}[reset] [/]"
            )
        self.location = ConsoleMessage(text=loc, debug=True).make_section(
            "Crash Location", indent=self.indent
        )

        return None


class PrettyCalledProcessError(PrettyException):
    """
    Represents a formatted and decorated error object for a subprocess call.

    This class is used to encapsulate information about a `CalledProcessError`,
    providing additional context such as command output, errors, and helpful
    debugging messages. It is particularly useful for wrapping and decorating
    subprocess-related exceptions in a more user-friendly format.
    """

    output: ConsoleMessage | None = Field(
        default=None, description="A section formatted representation of the exception stdout."
    )
    errors: ConsoleMessage | None = Field(
        default=None, description="A section formatted representation of the exception stderr."
    )
    command_message: ConsoleMessage | None = Field(
        default=None,
        description="Formatted message including a hint on retrying the original command.",
    )
    command: str = Field(default="", description="A string representation of the original command.")
    exception: CalledProcessError = Field(
        init=True, description="The original `CalledProcessError` instance."
    )

    def model_post_init(self, context: Any, /) -> None:
        super().model_post_init(context)
        self.output = ConsoleMessage(text=decode(self.exception.stdout), debug=True).make_section(
            "Output", indent=self.indent
        )
        self.errors = ConsoleMessage(text=decode(self.exception.stderr), debug=True).make_section(
            "Errors", indent=self.indent
        )
        self.command = (
            shlex.join(self.exception.cmd)
            if isinstance(self.exception.cmd, list)
            else self.exception.cmd
        )


class TextualizeRuntimeError(TextualizeError):
    """Represents a runtime error in the pytest-textualize console application."""

    def __init__(
        self,
        reason: str,
        exc_typename: str,
        messages: list[ConsoleMessage] | None = None,
        exit_code: int = 1,
        ctx: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(reason)
        self.exc_typename = exc_typename
        self.exit_code = exit_code
        self._messages = messages or []
        self._messages.insert(0, ConsoleMessage(text=reason.strip()))

        # self._messages.insert(0, ConsoleMessage(text=reason))
        self.ctx = ctx or {}

    def write(self, error_console: Console, verbose: Verbosity) -> None:
        """
        Write the error text to the provided IO iff there is any text to write.
        """
        panel = self.render(verbose=verbose)
        if panel:
            error_console.print(Padding(panel, pad=(0, 0, 0, 1), style="bright_red"))

    def render(self, verbose: Verbosity) -> PanelType | None:
        """
        Write the error text to the provided IO if there is any text to write.
        """
        debug = verbose >= Verbosity.NORMAL
        if text := self.get_text(debug=debug, strip=False):

            return Panel(
                Text.from_markup(text), expand=False, title=f"[b]{self.exc_typename}[/b]", padding=1
            )
        return None

    def get_text(self, debug: bool = False, indent: str = "", strip: bool = False) -> str:
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
                text=f"{indent}You can also run your [#9EC6F3]pytest[/] command with [#9EC6F3]-v|-vv|-vvv[/] to see more information.\n{indent}\n"
            )
            text += message.stripped if strip else message.text

        return text.rstrip(f"{indent}\n")

    def __str__(self) -> str:
        return self._messages[0].stripped.strip()

    @classmethod
    def create(
        cls,
        reason: str,
        exception: CalledProcessError | BaseException | None = None,
        *,
        info: list[str] | str | ConsoleMessage | list[ConsoleMessage] | None = None,
        ctx: dict[str, Any] | None = None,
    ) -> Self:
        """Create an instance of this class using the provided reason. If
        an exception is provided, this is also injected as a debug `ConsoleMessage`.

        There is specific handling for known exception types. For example,
        if exception is of type `subprocess.CalledProcessError`, the following
        sections are additionally added when available - stdout, stderr and command for testing.
        """
        if isinstance(info, str):
            info = [info]

        messages: list[ConsoleMessage] = [
            ConsoleMessage(text="\n".join(info or []), debug=False).style("#B4B4B8")
        ]

        indent = f"    | "
        # indent = f"    {chr(0x2022)} "
        if isinstance(exception, CalledProcessError):
            error = PrettyCalledProcessError(exception=exception, indent=indent)
            messages = [
                error.doc.style("white"),
                error.message,
                error.errors,
                *messages,
                # error.command_message,
            ]
        elif isinstance(exception, Exception):
            error = PrettyException(exception=exception, indent=indent)
            # ctx = {"link": error.link}
            messages = [error.doc.style("white"), error.message, error.location, *messages]
        return cls(reason, repr(type(exception)), messages, ctx=ctx)

    def append(self, message: str | ConsoleMessage) -> Self:
        if isinstance(message, str):
            message = ConsoleMessage(text=message)
        self._messages.append(message)
        return self
