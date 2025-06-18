# Project : pytest-textualize
# File Name : tests_console_factory.py
# Dir Path : tests/plugin_tests/textualize_tests/console_tests

from __future__ import annotations

from io import StringIO
from io import TextIOWrapper
from typing import TYPE_CHECKING

import pytest
import rich.console
from boltons.iterutils import first
from hamcrest import assert_that
from hamcrest import equal_to
from hamcrest import instance_of
from hamcrest import not_none, none
from hamcrest import is_not

from pytest_textualize import ConsoleFactory
from pytest_textualize import TextualizeSettings
from pytest_textualize.plugins.pytest_richtrace import console_key
from pytest_textualize.plugins.pytest_richtrace import error_console_key
from pytest_textualize.settings import settings_key

if TYPE_CHECKING:
    pass

parameterize = pytest.mark.parametrize


@pytest.mark.tryfirst
def test_console_output(pytestconfig: pytest.Config) -> None:
    textualize_settings = TextualizeSettings()
    pytestconfig.stash.setdefault(settings_key, textualize_settings)

    console = ConsoleFactory.console_output(pytestconfig)
    stash_console = pytestconfig.stash.get(console_key, None)
    assert_that(stash_console, not_none(), "console stashed")

    assert_that(stash_console, instance_of(rich.console.Console), "instance of rich.console.Console")
    assert_that(stash_console.stderr, equal_to(False), "stderr")
    assert_that(stash_console.file, instance_of(TextIOWrapper), "file sys.stdout (stream)")
    assert_that(stash_console, equal_to(console), "console same as the stashed")


def test_console_error_output(pytestconfig: pytest.Config) -> None:
    textualize_settings = TextualizeSettings()
    pytestconfig.stash.setdefault(settings_key, textualize_settings)

    err_console = ConsoleFactory.console_error_output(pytestconfig)
    stash_console = pytestconfig.stash.get(error_console_key, None)
    assert_that(stash_console, not_none(), "console stashed")

    assert_that(stash_console, instance_of(rich.console.Console), "instance of rich.console.Console")
    assert_that(stash_console.stderr, equal_to(True), "stderr")
    assert_that(stash_console.file, instance_of(TextIOWrapper), "file sys.stdout (stream)")
    assert_that(stash_console.style, equal_to("red"), "style")
    assert_that(stash_console.is_interactive, equal_to(False), "is_interactive")

    assert_that(stash_console, equal_to(err_console), "console same as the stashed")


def test_console_null_output(pytestconfig: pytest.Config) -> None:
    from rich._null_file import NullFile

    null_console = ConsoleFactory.console_null_output(pytestconfig)
    assert_that(null_console.file, instance_of(NullFile), "file -> NullFile")

    stash_console = pytestconfig.stash.get(console_key, None)
    assert_that(stash_console, not_none(), "console stashed")

    null_console.print("lrkorotorkotorotrotiorioriotioritoriroitroitoiritro")
    stash_console.print("lrkorotorkotorotrotiorioriotioritoriroitroitoiritro")

    assert_that(stash_console, instance_of(rich.console.Console), "instance of")
    assert_that(stash_console.stderr, equal_to(False), "stderr")
    assert_that(stash_console.file, instance_of(NullFile), "file -> NullFile")

    assert_that(stash_console.file, equal_to(null_console.file), "console same as the stashed")


def test_console_buffered_output(pytestconfig: pytest.Config) -> None:
    textualize_settings = TextualizeSettings()
    pytestconfig.stash.setdefault(settings_key, textualize_settings)

    pytestconfig.stash[console_key] = None
    buffered_console = ConsoleFactory.console_buffered_output(pytestconfig)
    assert_that(buffered_console.file, instance_of(StringIO), "file is StringIO")

    stash_console = pytestconfig.stash.get(console_key, None)
    assert_that(stash_console, none(), "expected not to be stashed")
