from __future__ import annotations

import sys
from io import StringIO

import pytest
from rich.console import Console

from pytest_textualize import Textualize


class ConsoleFactory:

    @staticmethod
    def console_null(config: pytest.Config) -> Console:
        # noinspection PyProtectedMember
        from rich._null_file import NullFile
        from pytest_textualize.plugin import console_key

        null_console = Console(file=NullFile(), stderr=False)
        config.stash[console_key] = null_console
        return null_console

    @staticmethod
    def console_stderr(config: pytest.Config) -> Console:
        from pytest_textualize.plugin import error_console_key

        console = ConsoleFactory.console_stdout(config, stderr=True)
        assert console.stderr is True, "error console should write to stderr only"
        config.stash[error_console_key] = console
        return console

    @staticmethod
    def console_stdout(config: pytest.Config, stderr: bool = False) -> Console:
        from pytest_textualize.plugin import console_key
        from pytest_textualize.plugin import error_console_key

        console_settings = Textualize.settings(config).console_settings
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
                    log_time=False,
                    stderr=True,
                    force_interactive=False,
                    theme=theme,
                    **exclude_none_unset,
                )
            else:
                console = Console(stderr=False, theme=theme, log_time=False, **exclude_none_unset)
            # console = ConsoleFactory.redirect_log_render(console)
            config.stash.setdefault(console_key, console)

        return console

    @staticmethod
    def console_buffer(config: pytest.Config) -> Console:
        """
        This console does not require to be in stash since he works with strings
        """
        console_settings = Textualize.settings(config).console_settings
        exclude_none = console_settings.model_dump(exclude_none=True)
        return Console(file=StringIO(), stderr=False, **exclude_none)

    # @staticmethod
    # def redirect_log_render(console: Console) -> Console:
    #     textualize().logging_config()
    #     render = getattr(console, "_log_render")
    #     console._log_render = LoggingConfig.create_console_render(
    #         show_time=render.show_time,
    #         show_path=render.show_path,
    #     )
    #     return console
