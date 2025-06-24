# pioneer
from __future__ import annotations


__all__ = (
    "textualize_plugin",
    "NotTest",
    "PytestPluginType",
    "TextualizeTracer",
    "TextualizeReporter",
    "ErrorExecutionTracer",
    "RunTestTracer",
    "CollectorTracer",
    "TestRunResults",
    "cleanup_factory",
    "HeaderServiceManager",
    "CollectorWrapper",
    "HookHeaderCollectorService",
    "PluggyCollectorService",
    "PoetryCollectorService",
    "PythonCollectorService",
    "skipif_no_console",
    "TextualizePluginRegistrationService",
    "collect_only_helper",
    "collected_items_helper"
)


from typing import TYPE_CHECKING

import pytest
from rich.console import ConsoleRenderable

from pytest_textualize.plugins.pytest_richtrace import plugin as textualize_plugin
from pytest_textualize.plugins.pytest_richtrace.exceptions import ConsoleMessage
from pytest_textualize.plugins.pytest_richtrace.model import TestRunResults
from pytest_textualize.plugins.pytest_richtrace.collector_tracer import (
    CollectorTracer,
)
from pytest_textualize.plugins.pytest_richtrace.error_tracer import (
    ErrorExecutionTracer,
)
from pytest_textualize.plugins.pytest_richtrace.plugin import skipif_no_console
from pytest_textualize.plugins.pytest_richtrace.services.header import CollectorWrapper
from pytest_textualize.plugins.pytest_richtrace.services.header import HeaderServiceManager
from pytest_textualize.plugins.pytest_richtrace.services.header import HookHeaderCollectorService
from pytest_textualize.plugins.pytest_richtrace.services.plugin_registration import TextualizePluginRegistrationService
from pytest_textualize.plugins.pytest_richtrace.services.header import PluggyCollectorService
from pytest_textualize.plugins.pytest_richtrace.services.header import PoetryCollectorService
from pytest_textualize.plugins.pytest_richtrace.services.header import PythonCollectorService
from pytest_textualize.plugins.pytest_richtrace.runtest_tracer import RunTestTracer
from pytest_textualize.plugins.pytest_richtrace.textualize_reporter import (
    TextualizeReporter,
)
from pytest_textualize.plugins.pytest_richtrace.tracer import TextualizeTracer


if TYPE_CHECKING:
    PytestPluginType = object


def cleanup_factory(pluginmanager: pytest.PytestPluginManager, plugin: PytestPluginType):
    def clean_up() -> None:
        name = pluginmanager.get_name(plugin)
        # TODO: log message
        pluginmanager.unregister(name=name)
        pluginmanager.hook.pytest_plugin_unregistered(plugin=plugin)

    return clean_up


class NotTest:
    def __init_subclass__(cls):
        cls.__test__ = NotTest not in cls.__bases__


def collect_only_helper(session: pytest.Session, t) -> ConsoleRenderable:
    from pytest_textualize.plugins.pytest_richtrace.helpers.collectors import collectonly
    return collectonly(session, t)

def collected_items_helper(session: pytest.Session) -> ConsoleRenderable:
    from pytest_textualize.plugins.pytest_richtrace.helpers.collectors import collectitems
    return collectitems(session)
