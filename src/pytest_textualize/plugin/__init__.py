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
    "collected_tree",
    "collected_list",
    "console_key",
    "collector_tracer",
    "error_console_key",
    "settings_key",
    "collected_groups",
    "collect_only_report",
    "ConsoleMessage"
)

from typing import NewType
from typing import TYPE_CHECKING

import pytest

from pytest_textualize.plugin import plugin as textualize_plugin
from pytest_textualize.plugin.collector_tracer import (
    CollectorTracer,
)
from pytest_textualize.plugin.error_tracer import (
    ErrorExecutionTracer,
)
from pytest_textualize.plugin.exceptions import ConsoleMessage
from pytest_textualize.plugin.helpers.collectors import collect_only_report
from pytest_textualize.plugin.helpers.collectors import collected_groups
from pytest_textualize.plugin.helpers.collectors import collected_list
from pytest_textualize.plugin.helpers.collectors import collected_tree
from pytest_textualize.plugin.model import TestRunResults
from pytest_textualize.plugin.plugin import skipif_no_console
from pytest_textualize.plugin.runtest_tracer import RunTestTracer
from pytest_textualize.plugin.services.header_data_collector import PythonCollectorService
from pytest_textualize.plugin.tracer import TextualizeTracer
from pytest_textualize.plugin.textualize_reporter import (
    TextualizeReporter,
)

if TYPE_CHECKING:
    PytestPluginType = NewType("PytestPluginType", object)

from rich.console import Console
from pytest_textualize.settings import TextualizeSettings
console_key = pytest.StashKey[Console]()
error_console_key = pytest.StashKey[Console]()
settings_key = pytest.StashKey[TextualizeSettings]()




def cleanup_factory(pluginmanager: pytest.PytestPluginManager, plugin_: PytestPluginType):
    def clean_up() -> None:
        name = pluginmanager.get_name(plugin_)
        # todo: log message
        pluginmanager.unregister(name=name)
        pluginmanager.hook.pytest_plugin_unregistered(plugin=plugin_)

    return clean_up


class NotTest:
    def __init_subclass__(cls):
        cls.__test__ = NotTest not in cls.__bases__
