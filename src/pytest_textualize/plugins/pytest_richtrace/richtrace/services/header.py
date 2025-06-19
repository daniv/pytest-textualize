# Project : pytest-textualize
# File Name : header.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace/services
from __future__ import annotations

from typing import cast

import pytest


class PytestCollectorService:
    name = ""


class PluggyCollectorService:
    name = ""


class PoetryCollectorService:
    name = ""


class PythonCollectorService:
    name = ""


class HookHeaderCollectorService:
    name = ""


class CollectorWrapper:
    name = ""


class HeaderServiceManager:
    names = [
        PytestCollectorService.name,
        PluggyCollectorService.name,
        PoetryCollectorService.name,
        PythonCollectorService.name,
        HookHeaderCollectorService.name,
        CollectorWrapper.name,
    ]

    def setup(self, config: pytest.Config) -> None:
        from ..textualize_reporter import TextualizeReporter

        plugin = config.pluginmanager.getplugin(TextualizeReporter.name)
        cast(TextualizeReporter, plugin).monitored_classes.extend(self.names)

        pass

    def call(self, config: pytest.Config):
        collector_wrapper = CollectorWrapper()
        config.pluginmanager.register(collector_wrapper, CollectorWrapper.name)

        python_collector = PythonCollectorService()
        config.pluginmanager.register(python_collector, PythonCollectorService.name)

        pytest_collector = PytestCollectorService()
        config.pluginmanager.register(pytest_collector, PytestCollectorService.name)

        poetry_collector = PoetryCollectorService()
        config.pluginmanager.register(poetry_collector, PoetryCollectorService.name)

        pluggy_collector = PluggyCollectorService()
        config.pluginmanager.register(pluggy_collector, PluggyCollectorService.name)

        hook_collector = HookHeaderCollectorService()
        config.pluginmanager.register(hook_collector, HookHeaderCollectorService.name)

    def teardown(self, config: pytest.Config) -> None:
        for name in self.names:
            plugin = config.pluginmanager.getplugin(name)
            config.pluginmanager.hook.pytest_plugin_unregistered(plugin=plugin)
            config.pluginmanager.unregister(plugin, name)
