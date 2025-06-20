# Project : pytest-textualize
# File Name : collector_observer.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

import sys
from functools import cached_property
from typing import TYPE_CHECKING

import pluggy
import pytest
from pendulum import DateTime

from pytest_textualize.textualize.hook_message import HookMessage

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

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"started={getattr(self, "_start_time", "<UNSET>")}>"
        )

    @cached_property
    def isatty(self) -> bool:
        return sys.stdin.isatty()

    @pytest.hookimpl
    def pytest_console_and_settings(self, console: Console, settings: TextualizeSettings) -> None:
        self.settings = settings
        self.console = console

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        self.pluginamanager = config.pluginmanager

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection(self, session: pytest.Session) -> None:
        import time

        self.test_run_results.collect.precise_start = time.perf_counter()
        self.test_run_results.collect.start = DateTime.now()
        self._start_time = self.test_run_results.collect.start.to_time_string()

        self.console.rule(
            f"[#D1F8EF]Collector started at {self._start_time}", characters="=", style="#A1E3F9"
        )

        node_id = session.nodeid if session.nodeid else session.name
        hm = HookMessage("pytest_plugin_registered", info=node_id)

        if self.isatty:
            if self.config.option.verbose >= 0:
                self.console.print(hm)
                self.console.print("[b]collecting ... [/]", end="")
                self.console.file.flush()
        elif self.config.option.verbose >= 1:
            self.console.print(hm, end="")
            self.console.print("[b]collecting ... [/]", end="")
            self.console.file.flush()

    @pytest.hookimpl
    def pytest_make_collect_report(self, collector: pytest.Collector) -> None:
        try:
            self.pluginamanager.hook.pytest_report_make_collect_report(colector=collector)
        except pluggy.HookCallError:
            self.config.pluginmanager.hook.pytest_report_make_collect_report(collector=collector)
