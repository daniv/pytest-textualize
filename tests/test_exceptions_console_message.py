from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import equal_to
from hamcrest import starts_with
from rich.text import Text

from pytest_textualize.plugin import ConsoleMessage
from pytest_textualize.plugin import skipif_no_console
from tests.helpers.lorem import get_word
from pytest import param

if TYPE_CHECKING:
    from rich.console import Console

parameterize = pytest.mark.parametrize


def test__init__console_message_str() -> None:
    """Test a default message of type str"""
    words = get_word(2)
    cm = ConsoleMessage(text=words)
    assert_that(cm.text, equal_to(words), "str __init__")

def test_console_message_style(console: Console) -> None:
    words = get_word(2)
    cm = ConsoleMessage(text=words).style("yellow")
    assert_that(cm.text, equal_to(f"[yellow]{words}[/yellow]"), reason="style")
    if console:
        console.line()
        console.print(cm.text)

def test_console_message_stripped() -> None:
    words = get_word(2)
    text = ConsoleMessage(text=words).stripped
    assert_that(text, equal_to(words), reason="stripped")

    text = ConsoleMessage(text=words).style("yellow").stripped
    assert_that(text, equal_to(words), reason="stripped")

def test_console_message_multi_line(capsys: pytest.CaptureFixture[str]) -> None:
    """Validates multiline messages are displayed correctly
    :param capsys: The pytest capsys fixture
    """
    lines = get_word(5, sep="\n")
    cm = ConsoleMessage(text=lines)
    assert_that(cm.text, equal_to(lines), "multi-line text")
    print(cm.text)
    captured = capsys.readouterr().out
    assert_that(captured, equal_to(lines + "\n"), reason="captured multi-line")

@skipif_no_console
def test_console_message_multi_line_style(console: Console, capsys: pytest.CaptureFixture[str]) -> None:

    lines = get_word(5, sep="\n")
    cm = ConsoleMessage(text=lines).style("violet b")
    assert_that(cm.text, equal_to(f"[violet b]{lines}[/violet b]"), reason="multi-line text")
    if console:
        console.print(cm.text)
        captured = capsys.readouterr().out
        captured_non_ansi = Text.from_ansi(captured).plain
        assert_that(captured_non_ansi, equal_to(lines), reason="captured multi-line")
        with capsys.disabled():
            console.print(cm.text)

def test_console_message_indent(capsys: pytest.CaptureFixture[str]) -> None:
    words = get_word(3)
    indented_text = ConsoleMessage(text=words).indent(" * ").text
    print(indented_text)
    captured = capsys.readouterr().out
    assert_that(captured, equal_to(indented_text + "\n"), reason="indented text")

    lines = get_word(3, sep="\n")
    indented_ml = ConsoleMessage(text=lines).indent(" * ").text
    print(indented_ml)
    captured = capsys.readouterr().out
    assert_that(captured.count("*"), equal_to(2), reason="indented multi line text")
    with capsys.disabled():
        print(indented_text)
        print(indented_ml)

def test_console_message_make_section() -> None:
    words = get_word(5)
    text = ConsoleMessage(text=words).make_section("title").text
    assert_that(text, starts_with("[b]title:[/b]"), reason="section title")

def test_console_message_make_section_w_indent() -> None:
    words = get_word(5)
    text = ConsoleMessage(text=words).make_section("title", indent=" -- ").text
    assert_that(text, starts_with("[b]title:[/b]"), reason="section title")
    assert_that(text, contains_string(f" -- {words}"), reason="section title")

def test_console_message_make_section_indent_style() -> None:
    word = get_word(1)
    text = ConsoleMessage(text=word).make_section("title", indent=" -- ", style="#DDFFBB").text
    assert_that(text, starts_with("[b]title:[/b]"), "section title")
    assert_that(text, contains_string(f"-- [#DDFFBB]{word}[/#DDFFBB]"), reason="text content")

def test_console_message_make_section_ml_indent() -> None:
    words = get_word(3, sep="\n")
    text = ConsoleMessage(text=words).make_section("title", indent="  #  ").text
    assert_that(text, starts_with("[b]title:[/b]"), "section title")
    assert_that(text.count("#"), equal_to(3), "indented multi-line text")

@parameterize(
    ("text", "expected_stripped"),
    [
        param("[info]Hello, World![/info]", "Hello, World!", id="info"),
        param("[b]Bold[/b]", "Bold", id="bold"),
        param("[i]Italic[/i]", "Italic", id="italic"),
    ],
)
def test_stripped_property(console: Console, text: str, expected_stripped: str) -> None:
    """Test the stripped property with various tagged inputs."""
    message = ConsoleMessage(text=text)
    assert_that(message.stripped, equal_to(expected_stripped), reason="stripped text")

@parameterize(
    ("text", "style", "expected"),
    [
        param("Hello, World!", "info", "[info]Hello, World![/info]", id="info"),
        param("Error occurred", "error", "[error]Error occurred[/error]", id="error"),
        param("", "info", "", id="empty-input"),
    ],
)
def test_wrap(text: str, style: str, expected: str) -> None:
    """Test the wrap method with various inputs."""
    message = ConsoleMessage(text=text)
    assert_that(message.style(style).text, equal_to(expected), reason="styled text")

@parameterize(
    ("text", "title", "indent", "expected"),
    [
        param("Hello, World!", "Greeting", "", "[b]Greeting:[/b]\nHello, World!", id="short"),
        param(
            "This is a message.",
            "Section Title",
            "  ",
            "[b]Section Title:[/b]\n  This is a message.", id="custom"
        ),
        param("", "Title", "", "", id="empty-text"),
        param("Multi-line\nText", "Title", ">>>", "[b]Title:[/b]\n>>>Multi-line\n>>>Text", id="multi-line-text"),
    ],
)
def test_make_section(text: str, title: str, indent: str, expected: str) -> None:
    """Test the make_section method with various inputs."""
    message = ConsoleMessage(text=text)
    msg = message.make_section(title, indent).text
    assert_that(msg, equal_to(expected), reason="section text")


def test_bug_style_with_markup() -> None:
    text = ConsoleMessage(text="[blue]inline[/]").style("yellow").text
    assert_that(text, equal_to('[yellow][blue]inline[/][/yellow]'), reason="no auto escape")
