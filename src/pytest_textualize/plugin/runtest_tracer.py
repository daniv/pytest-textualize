from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pytest_textualize import TextualizePlugins
from pytest_textualize.plugin.base import BaseTextualizePlugin

if TYPE_CHECKING:
    from pytest_textualize.plugin import TestRunResults


class RunTestTracer(BaseTextualizePlugin):

    name = TextualizePlugins.RUNTEST_TRACER

    results: TestRunResults

    def __init__(self, results: TestRunResults):
        self.results = results
        self.pluginmanager: pytest.PytestPluginManager | None = None
        self._started = False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} " f"name='{self.name}' " f"started={self._started!r}>"

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        super().configure(config)
        self.pluginmanager = config.pluginmanager
