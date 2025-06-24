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
    "PythonCollectorService",
    "skipif_no_console",
    "collect_only_helper",
    "collected_items_helper", 
    "HeaderRenderer",
    "console_key",
    "collector_tracer",
    "error_console_key",
    "settings_key"
)


from typing import TYPE_CHECKING

import pytest
from rich.console import ConsoleRenderable


from pytest_textualize.plugin import plugin as textualize_plugin
from pytest_textualize.plugin.exceptions import ConsoleMessage
from pytest_textualize.plugin.model import TestRunResults
from pytest_textualize.plugin.collector_tracer import (
    CollectorTracer,
)
from pytest_textualize.plugin.error_tracer import (
    ErrorExecutionTracer,
)
from pytest_textualize.plugin.plugin import skipif_no_console
from pytest_textualize.plugin.services.header_data_collector import PythonCollectorService
from pytest_textualize.plugin.services.header_renderer import HeaderRenderer
from pytest_textualize.plugin.runtest_tracer import RunTestTracer
from pytest_textualize.plugin.textualize_reporter import (
    TextualizeReporter,
)
from pytest_textualize.plugin.tracer import TextualizeTracer


if TYPE_CHECKING:
    PytestPluginType = object


from rich.console import Console
from pytest_textualize.settings import TextualizeSettings
console_key = pytest.StashKey[Console]()
error_console_key = pytest.StashKey[Console]()
settings_key = pytest.StashKey[TextualizeSettings]()


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
    from pytest_textualize.plugin.helpers.collectors import collectonly
    return collectonly(session, t)

def collected_items_helper(session: pytest.Session) -> ConsoleRenderable:
    from pytest_textualize.plugin.helpers.collectors import collectitems
    return collectitems(session)
