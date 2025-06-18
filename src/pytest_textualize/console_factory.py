# Project : pytest-textualize
# File Name : console_factory.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations

import sys
from io import StringIO
from typing import Any
from typing import IO
from typing import TYPE_CHECKING
from typing import TextIO

import pytest

from pytest_textualize.plugins.pytest_richtrace import console_key
from pytest_textualize.plugins.pytest_richtrace import error_console_key
from rich.console import Console

if TYPE_CHECKING:
    from pytest_textualize.settings import ConsoleSettings
    from pytest_textualize import TextualizeSettings


class ConsoleFactory:
    @staticmethod
    def check_settings(config: pytest.Config) -> ConsoleSettings:
        from pytest_textualize.settings import settings_key

        textualize_settings = config.stash.get(settings_key, None)
        assert textualize_settings, "No settings found"
        assert textualize_settings.console_settings, "No console settings found"
        return textualize_settings.console_settings

    @staticmethod
    def console_null_output(config: pytest.Config) -> Console:
        from rich._null_file import NullFile

        null_console = Console(file=NullFile(), stderr=False)
        config.stash[console_key] = null_console
        return null_console

    @staticmethod
    def console_error_output(config: pytest.Config) -> Console:
        console_settings = ConsoleFactory.check_settings(config)
        error_console = config.stash.get(error_console_key, None)
        if error_console is None:
            exclude_none = console_settings.model_dump(exclude_none=True)

            if not sys.stdout.isatty():
                exclude_none["_environ"] = console_settings.terminal_size_fallback

            from rich.console import Console

            error_console = Console(stderr=True, style="red", force_interactive=False, **exclude_none)
            config.stash.setdefault(error_console_key, error_console)

        return error_console

    @staticmethod
    def console_output(config: pytest.Config) -> Console:
        console_settings = ConsoleFactory.check_settings(config)
        console = config.stash.get(console_key, None)
        if console is None:
            exclude_none = console_settings.model_dump(exclude_none=True)
            if "theme" in exclude_none:
                pass
            if not sys.stdout.isatty():
                exclude_none["_environ"] = console_settings.terminal_size_fallback
            from rich.console import Console

            console = Console(stderr=False, **exclude_none)
            config.stash.setdefault(console_key, console)

        return console

    @staticmethod
    def console_buffered_output(config: pytest.Config) -> Console:
        """
        This console does not require to be in stash since he works with strings
        """
        console_settings = ConsoleFactory.check_settings(config)
        exclude_none = console_settings.model_dump(exclude_none=True)
        return Console(file=StringIO(), stderr=False, **exclude_none)
