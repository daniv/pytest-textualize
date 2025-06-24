# Project : pytest-textualize
# File Name : manager.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest
from pydantic_extra_types.pendulum_dt import DateTime

from pytest_textualize import TextualizePlugins
from pytest_textualize import stage_rule
from pytest_textualize.plugins.pytest_richtrace.base import BaseTextualizePlugin
from pytest_textualize.settings import Verbosity

if TYPE_CHECKING:
    from pytest_textualize.plugins import PytestPluginType
    from pytest_textualize.plugins import TestRunResults


class TextualizeTracer(BaseTextualizePlugin):
    name: str = TextualizePlugins.TRACER

    def __init__(self) -> None:
        from pytest_textualize.plugins import TestRunResults

        self.pluginmanager: pytest.PytestPluginManager | None = None
        self.results = TestRunResults()
        self._start_time: str | None = None

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"verbosity={self.verbosity!r} "
            f"started={getattr(self, "_start_time", "<UNSET>")}>"
        )

    @property
    def no_header(self) -> bool:
        return bool(self.config.option.no_header)

    @property
    def show_header(self) -> bool:
        return self.verbosity >= Verbosity.NORMAL

    @pytest.hookimpl(tryfirst=True)
    def pytest_plugin_registered(self, plugin: PytestPluginType, plugin_name: str) -> None:
        if plugin_name == "terminalreporter":
            self.config.pluginmanager.set_blocked(plugin_name)

    @pytest.hookimpl(tryfirst=True)
    def pytest_configure(self, config: pytest.Config) -> None:
        from pytest_textualize.plugins import TextualizeReporter
        from pytest_textualize.plugins import ErrorExecutionTracer

        super().configure(config)
        self.pluginmanager = config.pluginmanager

        if self.verbosity > Verbosity.NORMAL or self.traceconfig:
            from pytest_textualize.plugins import TextualizePluginRegistrationService
            service = TextualizePluginRegistrationService()
            service.monitored_classes.extend(
                [
                    TextualizePlugins.REPORTER,
                    TextualizePlugins.ERROR_TRACER,
                    TextualizePlugins.COLLECTOR_TRACER,
                    TextualizePlugins.RUNTEST_TRACER,
                    TextualizePlugins.PLUGIN,
                    self.name,
                ]
            )
            self.pluginmanager.register(service, name=service.name)
            # -- ensure unregister on the end of the execution
            self.cleanup_factory(service)

        # -- Adding a list of textualize plugins to be monitored in plugin_registered hook
        reporter_plugin = TextualizeReporter()
        # -- registering the reporter plugin
        self.pluginmanager.register(reporter_plugin, name=reporter_plugin.name)

        # -- registering the error observer plugin to report detailed errors asap
        error_tracer_plugin = ErrorExecutionTracer()
        self.pluginmanager.register(error_tracer_plugin, name=error_tracer_plugin.name)
        # -- ensure unregister on the end of the execution
        self.cleanup_factory(error_tracer_plugin)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session: pytest.Session) -> None:
        from pytest_textualize.plugins import CollectorTracer
        from pytest_textualize.plugins import HeaderServiceManager

        self.results.precise_start = time.perf_counter()
        self.results.start = DateTime.now()
        self._start_time = self.results.start.to_time_string()
        session.name = "pyest-textualize"

        # -- registering the collector tracker, it will be unregistered on pytest_report_collectionfinish
        collection_tracer = CollectorTracer(self.results)
        session.config.pluginmanager.register(collection_tracer, name=collection_tracer.name)

        if not self.show_header:
            return

        stage_rule(self.console, "session", time_str=self._start_time)
        if not self.no_header:
            hook = session.config.pluginmanager.hook
            manager = HeaderServiceManager()
            manager.setup(session.config)
            manager.call(session.config)
            environment_data = hook.pytest_collect_env_info(config=session.config)
            manager.teardown(session.config)
            hook.pytest_render_header(config=session.config, data=environment_data)

    @pytest.hookimpl
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        from pytest_textualize.plugins import RunTestTracer

        if self.pluginmanager.has_plugin(TextualizePlugins.REGISTRATION_SERVICE):
            registration_service = self.pluginmanager.getplugin(TextualizePlugins.REGISTRATION_SERVICE)
            registration_service.monitored_classes.append(RunTestTracer.name)

        runtest_tracer = RunTestTracer(self.results)
        self.pluginmanager.register(runtest_tracer, runtest_tracer.name)
        self.cleanup_factory(runtest_tracer)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        plugin = session.config.pluginmanager.get_plugin(TextualizePlugins.COLLECTOR_TRACER)
        if plugin:
            session.config.pluginmanager.unregister(plugin, plugin.name)
        return None
