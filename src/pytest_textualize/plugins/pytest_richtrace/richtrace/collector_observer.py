# Project : pytest-textualize
# File Name : collector_observer.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest_textualize.plugins import TestRunResults
    from pytest_textualize import TextualizeSettings
    from rich.console import Console


class CollectionObserver:
    name = "textualize-collection-observer"
    test_run_results: TestRunResults

    def __init__(self, config: pytest.Config, results: TestRunResults):
        self.config = config
        self.test_run_results = results
        self.console: Console | None = None
        self.settings: TextualizeSettings | None = None
        self._start_time: str | None = None
        self.pluginamanager: pytest.PytestPluginManager | None = None

    @pytest.hookimpl
    def pytest_console_and_settings(self, console: Console, settings: TextualizeSettings) -> None:
        self.settings = settings
        self.console = console

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        self.pluginamanager = config.pluginmanager
