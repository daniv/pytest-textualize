from __future__ import annotations

from pprint import saferepr
from typing import ClassVar
from typing import TYPE_CHECKING

import pytest

from pytest_textualize import TextualizePlugins
from pytest_textualize import Verbosity
from pytest_textualize import Textualize
from pytest_textualize.plugin.base import BaseTextualizePlugin


if TYPE_CHECKING:
    from pytest_textualize.typist import PytestPluginType


class TextualizePluginRegistrationService(BaseTextualizePlugin):
    name = TextualizePlugins.REGISTRATION_SERVICE

    monitored_classes: ClassVar[list[str]] = [TextualizePlugins.REGISTRATION_SERVICE]

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        super().configure(config)

    @pytest.hookimpl(trylast=True)
    def pytest_plugin_registered(self, plugin_name: str) -> None:
        if plugin_name is None:
            return None

        if self.traceconfig:
            results = Textualize.hook_msg("pytest_plugin_registered", info=plugin_name)
            self.console_logger.log(*results, verbosity=Verbosity.VERY_VERBOSE)

        elif plugin_name in self.monitored_classes:
            msg, info, level = Textualize.hook_msg("pytest_plugin_registered", info=plugin_name)
            self.verbose_logger.log(msg, info, level_text=level, verbosity=Verbosity.VERBOSE)
        return None

    @pytest.hookimpl
    def pytest_plugin_unregistered(self, plugin: PytestPluginType) -> None:
        if self.verbosity > Verbosity.NORMAL:
            if hasattr(plugin, "name"):
                results = TextualizeFactory.hook_msg(
                    "pytest_plugin_unregistered", info=getattr(plugin, "name")
                )
                self.console_logger.log(*results, verbosity=Verbosity.VERBOSE)
            else:
                results = TextualizeFactory.hook_msg(
                    "pytest_plugin_unregistered", info=saferepr(plugin)
                )
                self.console_logger.log(*results, verbosity=Verbosity.VERBOSE)
        return None
