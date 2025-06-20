# Project : pytest-textualize
# File Name : hookspecs.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

from typing import Any
from typing import MutableMapping
from typing import TYPE_CHECKING

import pytest

from pytest_textualize import TextualizeSettings

if TYPE_CHECKING:
    from rich.console import Console
    from pytest_textualize.plugins import PytestPlugin


@pytest.hookspec(historic=True)
def pytest_console_and_settings(
        console: Console, error_console: Console, settings: TextualizeSettings
) -> None:
    """Provides the framework settings and the rich console,

    :param error_console: and sys. stderr console
    :param console: The rich.Console instance
    :param settings: The configuration settings
    :return: a dictionary with the information collected
    """


@pytest.hookspec
def pytest_collect_env_info(config: pytest.Config) -> MutableMapping[str, Any] | None:
    """Collects environment information for the header,

    :param config: The pytest config
    :return: a dictionary with the information collected
    """
    pass


@pytest.hookspec
def pytest_plugin_unregistered(plugin: PytestPlugin) -> None:
    pass


class ReportingHookSpecs:
    @pytest.hookspec(firstresult=True)
    def pytest_render_header(self, config: pytest.Config, data: MutableMapping[str, Any]) -> bool:
        pass

    @pytest.hookspec  # (firstresult=True)
    def pytest_report_make_collect_report(self, collector: pytest.Collector) -> None:
        pass
