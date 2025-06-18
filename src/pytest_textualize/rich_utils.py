# Project : pytest-textualize
# File Name : rich_utils.py
# Dir Path : src/pytest_textualize
from __future__ import annotations

import sys

import pytest_textualize._lazy_rich as r

_HIGHLIGHTS = [
    r"`(?P<syntax>[^`]*)`|(?:^|\s)(?P<args>-{1,2}[\w]+[\w-]*)",
]

_windows_console_fixed: bool | None = None


def rich_strip(text: r.Text) -> r.Text:
    """Strip leading and trailing whitespace from `rich.text.Text`.

    :param text: Text to be stripped of leading and trailing whitespace
    """
    plain = text.plain.strip()
    return r.Text.from_markup(plain)


def rich_wrap(console: r.Console, text: r.Text, width: int) -> r.Lines:
    """`textwrap.wrap()` equivalent for `rich.text.Text`.

    :param console: The rich console
    :param text: the rich text object
    :param width: with of the wrapped text
    :return: a rich Lines object
    """
    text = text.copy()
    text.expand_tabs(8)
    whitespace_trans = dict.fromkeys(map(ord, "\t\n\x0b\x0c\r "), ord(" "))
    text.plain = text.plain.translate(whitespace_trans)
    return text.wrap(console, width)


def rich_fill(console: r.Console, text: r.Text, width: int, indent: r.Text) -> r.Text:
    """`textwrap.fill()` equivalent for `rich.text.Text`.

    :param console: The rich console
    :param text: the rich text object
    :param width: with of the wrapped text
    :param indent: the indentation size
    :return: a rich Text object
    """
    lines = rich_wrap(console, text, width)
    return r.Text("\n").join(indent + line for line in lines)
