# Project : pytest-textualize
# File Name : test_exections_textualize_runtime_error.py
# Dir Path : tests/in_progress

from __future__ import annotations

from subprocess import CalledProcessError
from typing import TYPE_CHECKING
from typing import Sized
from typing import TypeVar
import pytest
from _pytest.config import ExitCode as ec

from hamcrest import instance_of
from pytest import param
from pytest import mark
from hamcrest import assert_that
from hamcrest import equal_to

from pytest_textualize.plugin import ConsoleMessage
from pytest_textualize.plugin.exceptions import TextualizeRuntimeError

if TYPE_CHECKING:
    from rich.console import Console
    from _pytest.fixtures import FixtureRequest

parameterize = pytest.mark.parametrize

@parameterize(
    ("reason", "messages", "exit_code", "expected_reason"),
    [
        ("Error occurred!", None, ec.INTERNAL_ERROR, "Error occurred!"),
        ("Specific error", [ConsoleMessage("Additional details.")], ec.USAGE_ERROR, "Specific error"),
        ("Minimal error", [], ec.TESTS_FAILED, "Minimal error")
    ],
)
def test_poetry_runtime_error_init(
    reason: str,
    messages: list[ConsoleMessage] | None,
    exit_code: pytest.ExitCode,
    expected_reason: str,
) -> None:
    """Test the basic initialization of the TextualizeRuntimeError class."""

    error = TextualizeRuntimeError(reason, messages=messages, exit_code=exit_code)

    assert_that(error.exit_code, equal_to(exit_code), reason="exit_code")
    assert_that(str(error), equal_to(expected_reason), reason="error")
    assert_that(error._messages[0], instance_of(ConsoleMessage), reason="instance of ConsoleMessage")
    assert_that( error._messages[0].text, equal_to(reason), reason="reason")


@pytest.mark.parametrize(
    ("strip", "indent", "messages", "expected_text"),
    [
        param(False, "",
                [
                    ConsoleMessage("Info message"),
                    ConsoleMessage("Debug message"),
                ], "Error\n\nInfo message\n\nDebug message", id="default"
        ),
        param(True, "",
                [
                    ConsoleMessage("[b]Bolded message[/b]"),
                    ConsoleMessage("[i]Debug Italics Message[/i]"),
                ], "Error\n\nBolded message\n\nDebug Italics Message", id="stripped tags"
        ),
        param(False, "",
              [
                  ConsoleMessage("[b]Bolded message[/b]"),
                  ConsoleMessage("[i]Debug Italics Message[/i]"),
              ], "Error\n\n[b]Bolded message[/b]\n\n[i]Debug Italics Message[/i]", id="unstripped tags"
        ),
        param(False, "    ", [ConsoleMessage("Error occurred!")],
                "    Error\n    \n    Error occurred!", id="indented"
        ),  
    ],
)
def test_poetry_runtime_error_get_text(
    request: FixtureRequest,
    strip: bool,
    indent: str,
    messages: list[ConsoleMessage],
    expected_text: str,
) -> None:
    error = TextualizeRuntimeError("Error", messages)
    text = error.get_text(strip=strip, indent=indent)
    assert_that(text, equal_to(expected_text), reason=request.node.callspec.id)


# @mark.xfail("PrettyCalledProcessError not implemented")
@pytest.mark.parametrize(
    ("reason", "exception", "info", "expected_message_texts"),
    [
        (
            "Command failed",
            None,
            None,
            ["Command failed", ""],  # No exception or additional info
        ),
        (
            "Command failure",
            Exception("An exception occurred"),
            None,
            [
                "Command failure",
                "[#9B7EBD]Exception:[/]\n    | [#9B7EBD]An exception occurred[/]",
                "",
            ],  # Exception message included
        ),
        (
            "Subprocess error",
            CalledProcessError(1, ["cmd"], b"stdout", b"stderr"),
            ["Additional info"],
            [
                "Subprocess error",
                "[logging.level.warning][b]Exception:[/]\n"
                "    | Command '['cmd']' returned non-zero exit status 1.[/]",
                "[logging.level.warning][b]Output:[/]\n    | stdout[/]",
                "[logging.level.warning][b]Errors:[/]\n    | stderr[/]",
                "[logging.level.info]Additional info[/]",
                "You can test the failed command by executing:\n\n    [bright_blue]cmd[/]",
            ],
        ),
    ],
)
def test_poetry_runtime_error_create(
    console: Console,
    reason: str,
    exception: Exception,
    info: list[str],
    expected_message_texts: list[str],
) -> None:
    """Test the create class method of TextualizeRuntimeError."""
    error = TextualizeRuntimeError.create(reason, exception, info)
    from pytest_textualize import Verbosity
    error.write(console, Verbosity.VERBOSE)
    pass
    # assert_that(isinstance(error, TextualizeRuntimeError),equal_to(True), reason="instance_of")
    # assert_that(all(isinstance(msg, ConsoleMessage) for msg in error._messages))
    # actual_texts = [msg.text for msg in error._messages]
    # assert_that(actual_texts, equal_to(expected_message_texts))
    

def test_poetry_runtime_error_append(console: Console) -> None:
    """Test the append method of TextualizeRuntimeError."""
    error = TextualizeRuntimeError.create("Error", info=["Hello"]).append("World")
    actual_texts = [msg.text for msg in error._messages]
    console.print(*actual_texts)
    assert_that(actual_texts, equal_to(["Error", "[logging.level.info]Hello[/logging.level.info]", "World"]), reason="texts")


def testa(console: Console) -> None:

    error = TextualizeRuntimeError.create( "Command failure", Exception("An exception occurred"), None)
    from pytest_textualize import Verbosity
    error.write(console, Verbosity.VERBOSE)
    pass
