# Project : pytest-textualize
# File Name : error_observer.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest_textualize import TextualizeSettings
    from pytest_textualize.plugins import TestRunResults
    from rich.console import Console


class ErrorExecutionObserver:
    name = "textualize-error-observer"
    test_run_results: TestRunResults

    def __init__(self, config: pytest.Config, results: TestRunResults):
        self.config = config
        self.test_run_results = results
        self.console: Console | None = None
        self.settings: TextualizeSettings | None = None

    def pytest_console_and_settings(self, console: Console, settings: TextualizeSettings) -> None:
        self.settings = settings
        self.console = console

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} " f"name='{self.name}'>"
