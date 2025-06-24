# Project : pytest-textualize
# File Name : error_observer.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pytest_textualize import TextualizePlugins
from pytest_textualize.plugin.base import BaseTextualizePlugin

if TYPE_CHECKING:
    from rich.console import Console
    from pytest_textualize.settings import TextualizeSettings


class ErrorExecutionTracer(BaseTextualizePlugin):
    name = TextualizePlugins.ERROR_TRACER


    def __init__(self):
        self.config: pytest.Config | None = None
        self.settings: TextualizeSettings | None = None
        self.console: Console | None = None
        self.error_console: Console | None = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} " f"name='{self.name}'>"

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        super().configure(config)

    @pytest.hookspec(historic=True)
    def pytest_console_and_settings(self, error_console: Console) -> None:
        self.error_console = self.validate_console(error_console)
