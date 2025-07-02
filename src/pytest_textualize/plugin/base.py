from __future__ import annotations

import sys
from abc import ABC
from abc import abstractmethod
from functools import cached_property
from typing import NoReturn
from typing import TYPE_CHECKING

import pytest
from pydantic import BaseModel
from pydantic import TypeAdapter
from pydantic import field_validator
from rich.console import Console

from pytest_textualize import Verbosity

if TYPE_CHECKING:
    from argparse import Namespace as NamespaceType
    from pytest_textualize.typist import PytestPluginType
    from pytest_textualize.typist import TextualizeSettingsType
    from pytest_textualize.typist import VerboseLoggerType


# noinspection PyNestedDecorators
class ValidateConsole(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    console_stderr: Console
    console_stdout: Console

    @field_validator("console_stdout", mode="after")
    @classmethod
    def validate_stdout(cls, console: Console) -> Console:
        if console.stderr:
            raise TypeError(
                f"Expected Console.file stream name to be <stdout> however is {c.file.name}"
            )
        return console

    @field_validator("console_stderr", mode="after")
    @classmethod
    def validate_stderr(cls, console: Console) -> Console:
        if not console.stderr:
            raise TypeError(
                f"Expected Console.file stream name to be <stderr> however is {console.file.name}"
            )
        return console


class _BaseTextualizeSettingsPlugin(ABC):
    settings: TextualizeSettingsType | None = None

    def configure(self, config: pytest.Config) -> None:
        from pytest_textualize.plugin import settings_key

        settings = config.stash.get(settings_key, None)
        self.settings = self.validate_settings(settings)

    @classmethod
    def validate_settings(
        cls, settings: TextualizeSettingsType
    ) -> TextualizeSettingsType | NoReturn:
        from pytest_textualize.settings import TextualizeSettings

        return TypeAdapter(TextualizeSettings).validate_python(settings)


class BaseTextualizePlugin(_BaseTextualizeSettingsPlugin):
    config: pytest.Config | None = None
    verbose_logger: VerboseLoggerType | None = None
    console: Console | None = None

    def configure(self, config: pytest.Config) -> None:
        from pytest_textualize.plugin import console_key
        from pytest_textualize.plugin import error_console_key
        from pytest_textualize.textualize.logging import VerboseLogger

        super().configure(config)
        self.config = config

        stdout = config.stash.get(console_key, None)
        stderr = config.stash.get(error_console_key, None)
        consoles = ValidateConsole(console_stderr=stderr, console_stdout=stdout)
        self.console = consoles.console_stdout

        self.verbose_logger = VerboseLogger(config)
        self.verbose_logger.add_console("<stdout>", consoles.console_stdout)
        self.verbose_logger.add_console("<stderr>", consoles.console_stderr)

    @cached_property
    def my_property(self):
        print("Computing my_property")
        return "cached_value"

    @property
    def options(self) -> NamespaceType:
        return self.config.option

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def tb_style(self) -> str:
        return self.options.tbstyle

    @property
    def traceconfig(self) -> bool:
        return self.options.traceconfig

    @property
    def verbosity(self) -> Verbosity:
        return Verbosity(self.config.option.verbose)

    @cached_property
    def isatty(self) -> bool:
        return sys.stdout.isatty()

    @property
    def showcapture(self) -> bool:
        return self.options.showcapture

    def has_opt(self, char: str) -> bool:
        from _pytest.terminal import getreportopt

        report_chars = getreportopt(self.config)
        char = {"xfailed": "x", "skipped": "s"}.get(char, char)
        return char in report_chars

    def cleanup_factory(self, plugin: PytestPluginType) -> None:
        from pytest_textualize import cleanup_factory

        self.config.add_cleanup(cleanup_factory(self.config.pluginmanager, plugin))
