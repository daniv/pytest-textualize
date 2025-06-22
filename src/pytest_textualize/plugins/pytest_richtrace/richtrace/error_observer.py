# Project : pytest-textualize
# File Name : error_observer.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pytest_textualize.plugins.pytest_richtrace import console_key
from pytest_textualize.plugins.pytest_richtrace import error_console_key
from pytest_textualize.settings import settings_key

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
        self.console: Console = config.stash.get(console_key, None)
        self.error_console: Console = config.stash.get(error_console_key, None)
        self.settings: TextualizeSettings = config.stash.get(settings_key, None)

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} " f"name='{self.name}'>"
