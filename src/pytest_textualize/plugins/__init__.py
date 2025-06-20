# Project : pytest-textualize
# File Name : __init__.py
# Dir Path : src/pytest_textualize/plugins
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pytest_textualize.plugins.pytest_richtrace.richtrace.model import TestRunResults
from pytest_textualize.textualize.hook_message import HookMessage

if TYPE_CHECKING:
    PytestPlugin = object

__all__ = ["PytestPlugin", "cleanup_factory", "NotTest", "TestRunResults", "HookMessage"]


def cleanup_factory(pluginmanager: pytest.PytestPluginManager, plugin: PytestPlugin):
    def clean_up() -> None:
        name = pluginmanager.get_name(plugin)
        # TODO: log message
        pluginmanager.unregister(name=name)
        pluginmanager.hook.pytest_plugin_unregistered(plugin=plugin)

    return clean_up


class NotTest:
    def __init_subclass__(cls):
        cls.__test__ = NotTest not in cls.__bases__
