# Project : pytest-textualize
# File Name : base.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

import sys
from abc import ABC
from abc import abstractmethod
from functools import cached_property
from typing import NoReturn
from typing import TYPE_CHECKING

import pytest
from pydantic import TypeAdapter
from pydantic_core import PydanticCustomError
from rich.console import Console

from pytest_textualize import Verbosity
from pytest_textualize.settings import TextualizeSettings

if TYPE_CHECKING:
    from pytest_textualize.plugin import PytestPluginType


class _BaseTextualizeSettingsPlugin(ABC):
    settings: TextualizeSettings | None = None

    def configure(self, config: pytest.Config) -> None:
        from pytest_textualize.plugin import settings_key

        settings = config.stash.get(settings_key, None)
        self.settings = self.validate_settings(settings)

    @classmethod
    def validate_settings(cls, settings: TextualizeSettings) -> TextualizeSettings | NoReturn:
        return TypeAdapter(TextualizeSettings).validate_python(settings)


class _BaseRichConsolePlugin(_BaseTextualizeSettingsPlugin, ABC):
    console: Console | None = None

    def configure(self, config: pytest.Config) -> None:
        from pytest_textualize.plugin import console_key

        super().configure(config)
        console = config.stash.get(console_key, None)
        self.console = _BaseRichConsolePlugin.validate_console(console)

    @classmethod
    def validate_console(cls, console: Console) -> Console | NoReturn:
        if console is None or isinstance(console, Console) is False:
            raise PydanticCustomError(
                error_type="is_subclass_of",
                message_template="input should be a subclass of {subclass}",
                context={
                    "subclass": Console.__name__,
                    "input_type": type(console),
                    "input_value": console,
                },
            )
        return console


class BaseTextualizePlugin(_BaseRichConsolePlugin):
    config: pytest.Config | None = None

    def configure(self, config: pytest.Config) -> None:
        super().configure(config)
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def traceconfig(self) -> bool:
        return self.config.option.traceconfig

    @property
    def verbosity(self) -> Verbosity:
        return self.settings.verbosity

    @cached_property
    def isatty(self) -> bool:
        return sys.stdout.isatty()

    def cleanup_factory(self, plugin: PytestPluginType) -> None:
        from pytest_textualize.plugin import cleanup_factory
        self.config.add_cleanup(cleanup_factory(self.config.pluginmanager, plugin))
