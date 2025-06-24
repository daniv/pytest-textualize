# Project : pytest-textualize
# File Name : console_factory.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations

import sys
from io import StringIO
from typing import TYPE_CHECKING

import pytest
from rich.console import Console


from pytest_textualize.plugins.pytest_richtrace import console_key
from pytest_textualize.plugins.pytest_richtrace import error_console_key
from pytest_textualize.plugins.pytest_richtrace import settings_key
from pytest_textualize.textualize.logging import TextualizeConsoleLogRender

if TYPE_CHECKING:
    from pytest_textualize.settings import ConsolePyProjectSettingsModel


class ConsoleFactory:
    @staticmethod
    def check_settings(config: pytest.Config) -> ConsolePyProjectSettingsModel:

        textualize_settings = config.stash.get(settings_key, None)
        assert textualize_settings, "No settings found"
        assert textualize_settings.console, "No console settings found"
        return textualize_settings.console

    @staticmethod
    def console_null(config: pytest.Config) -> Console:
        # noinspection PyProtectedMember
        from rich._null_file import NullFile

        null_console = Console(file=NullFile(), stderr=False)
        config.stash[console_key] = null_console
        return null_console

    @staticmethod
    def console_stderr(config: pytest.Config) -> Console:
        return ConsoleFactory.console_stdout(config, stderr=True)

    @staticmethod
    def console_stdout(config: pytest.Config, stderr: bool = False) -> Console:
        console_settings = ConsoleFactory.check_settings(config)
        console = (
            config.stash.get(error_console_key, None)
            if stderr
            else config.stash.get(console_key, None)
        )
        if console is None:
            exclude_none_unset = console_settings.model_dump(
                exclude_none=True, exclude_unset=True, exclude={"argparse_theme"}
            )

            if not sys.stdout.isatty():
                exclude_none_unset["_environ"] = console_settings.environ
            from rich.console import Console

            theme = console_settings.get_theme(console_settings.color_system)
            if stderr:
                console = Console(
                    stderr=True,
                    style="red",
                    force_interactive=False,
                    theme=theme,
                    **exclude_none_unset,
                )
            else:
                console = Console(stderr=False, theme=theme, **exclude_none_unset)
            console = ConsoleFactory.redirect_log_render(console)
            config.stash.setdefault(console_key, console)

        return console

    @staticmethod
    def console_buffer(config: pytest.Config) -> Console:
        """
        This console does not require to be in stash since he works with strings
        """
        console_settings = ConsoleFactory.check_settings(config)
        exclude_none = console_settings.model_dump(exclude_none=True)
        return Console(file=StringIO(), stderr=False, **exclude_none)

    @staticmethod
    def redirect_log_render(console: Console) -> Console:
        render = getattr(console, "_log_render")
        console._log_render = TextualizeConsoleLogRender(
            show_time=render.show_time,
            show_path=render.show_path,
            time_format=render.time_format,
        )
        return console
