# Project : pytest-textualize
# File Name : plugin_registration.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/services
from __future__ import annotations

from pprint import saferepr
from typing import ClassVar
from typing import TYPE_CHECKING

import pytest

from pytest_textualize import TextualizePlugins
from pytest_textualize.textualize.verbose_log import Verbosity
from pytest_textualize import trace_logger
from pytest_textualize.textualize import hook_msg
from pytest_textualize.plugin.base import BaseTextualizePlugin

if TYPE_CHECKING:
    from pytest_textualize.plugin import PytestPluginType


class TextualizePluginRegistrationService(BaseTextualizePlugin):
    name = TextualizePlugins.REGISTRATION_SERVICE

    monitored_classes: ClassVar[list[str]] = [TextualizePlugins.REGISTRATION_SERVICE]

    def __init__(self) -> None:
        self.console_logger = trace_logger()

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        super().configure(config)

    @pytest.hookimpl(trylast=True)
    def pytest_plugin_registered(self, plugin_name: str) -> None:
        if plugin_name is None:
            return None

        if self.traceconfig:
            results = hook_msg("pytest_plugin_registered", info=plugin_name)
            self.console_logger.log(*results, verbosity=Verbosity.VERY_VERBOSE)
        elif plugin_name in self.monitored_classes:
            results = hook_msg("pytest_plugin_registered", info=plugin_name)
            self.console_logger.log(*results, verbosity=Verbosity.VERBOSE)
        return None

    @pytest.hookimpl
    def pytest_plugin_unregistered(self, plugin: PytestPluginType) -> None:
        if self.verbosity > Verbosity.NORMAL:
            if hasattr(plugin, "name"):
                results = hook_msg("pytest_plugin_unregistered", info=getattr(plugin, "name"))
                self.console_logger.log(*results, verbosity=Verbosity.VERBOSE)
            else:
                results = hook_msg("pytest_plugin_unregistered", info=saferepr(plugin))
                self.console_logger.log(*results, verbosity=Verbosity.VERBOSE)
        return None
