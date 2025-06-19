# Project : pytest-textualize
# File Name : textualize_reporter.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

import sys
import threading
from functools import cached_property
from pprint import saferepr
from typing import Any
from typing import ClassVar

import pytest
from rich import box
from rich.panel import Panel
from rich.text import Text
from typing_extensions import TYPE_CHECKING

from pytest_textualize.settings import Verbosity
from pytest_textualize.textualize.hook_message import HookMessage

if TYPE_CHECKING:
    from rich.console import Console
    from pytest_textualize.plugins import PytestPlugin
    from pytest_textualize import TextualizeSettings


class TextualizeReporter:
    name = "pytest-textualize-reporter"

    monitored_classes: ClassVar[list[str]] = []

    def __init__(self, config: pytest.Config):
        self.config = config
        self.console: Console | None = None
        self.settings: TextualizeSettings | None = None
        self._lock = threading.Lock()

    @property
    def traceconfig(self) -> bool:
        return self.config.option.traceconfig

    @property
    def verbosity(self) -> Verbosity:
        if self.settings is None:
            return Verbosity.QUIET
        return self.settings.verbosity

    @cached_property
    def isatty(self) -> bool:
        return sys.stdin.isatty()

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        from pytest_textualize.settings import settings_key
        from pytest_textualize.plugins.pytest_richtrace import console_key

        self.monitored_classes.append(self.name)
        self.settings = config.stash.get(settings_key, None)
        self.console = config.stash.get(console_key, None)
        from pytest_textualize import __version__
        panel = Panel(
            Text(
                "A pytest plugin using Rich for beautiful test result formatting.",  # noqa: E501
                justify="center",
            ),
            box=box.ROUNDED,
            style="pytest.panel.border",
            padding=2,
            title="[#4da8da]pytest-textualize plugin[/]",
            subtitle=f"[#A9C46C]v{__version__}[/]",
        )
        self.console.print(panel)

    @pytest.hookimpl(trylast=True)
    def pytest_plugin_registered(self, plugin: PytestPlugin, plugin_name: str) -> None:
        if plugin_name is None or self.verbosity < Verbosity.VERBOSE:
            return None

        if self.config.option.traceconfig:
            hm = HookMessage("pytest_plugin_registered", info=plugin_name)
            with self._lock:
                self.console.print(hm)
        else:
            if plugin_name in self.monitored_classes:
                hm = HookMessage("pytest_plugin_registered", info=plugin_name)
                with self._lock:
                    self.console.print(hm)
        return None

    @pytest.hookimpl
    def pytest_plugin_unregistered(self, plugin: PytestPlugin) -> None:
        if self.verbosity > Verbosity.NORMAL:
            hm = HookMessage("pytest_plugin_unregistered", info=saferepr(plugin))
            self.console.print(hm)

    @pytest.hookimpl(trylast=True)
    def pytest_unconfigure(self) -> None:
        if self.verbosity > Verbosity.NORMAL:
            hm = HookMessage("pytest_unconfigure")
            self.console.print(hm)
        self.config.pluginmanager.unregister(self, self.name)
