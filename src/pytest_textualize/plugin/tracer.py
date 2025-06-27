# Project : pytest-textualize
# File Name : manager.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest
from pydantic_extra_types.pendulum_dt import DateTime
from rich.padding import Padding
import sys

from rich.text import Text

from pytest_textualize import TextualizePlugins
from pytest_textualize import trace_logger
from pytest_textualize.plugin.base import BaseTextualizePlugin
from pytest_textualize.textualize import hook_msg
from pytest_textualize.textualize import stage_rule
from pytest_textualize.textualize.theme.error_report_styles import style
from pytest_textualize.textualize.verbose_log import Verbosity
from pytest_textualize.plugin import CollectorTracer
from pytest_textualize.plugin import HeaderServiceManager
from pytest_textualize.plugin import ErrorExecutionTracer
from pytest_textualize.plugin import TestRunResults
from pytest_textualize.plugin import RunTestTracer
from pytest_textualize.plugin import SummaryService
from pytest_textualize.plugin import TextualizePluginRegistrationService

if TYPE_CHECKING:
    from pytest_textualize.plugin import PytestPluginType
    # from pytest_textualize.plugin import TestRunResults
    from collections.abc import Generator
    from _pytest._code import ExceptionInfo
    from _pytest._code.code import ExceptionRepr
    from _pytest.outcomes import Exit


class TextualizeTracer(BaseTextualizePlugin):
    name: str = TextualizePlugins.TRACER

    def __init__(self) -> None:
        self.pluginmanager: pytest.PytestPluginManager | None = None
        self.results: TestRunResults | None = None
        self._start_time: str | None = None
        self._keyboard_interrupt_memo: ExceptionRepr | None = None
        self.console_logger = trace_logger()

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

    @property
    def no_summary(self) -> bool:
        return bool(self.config.option.no_summary)

    @property
    def collectonly(self) -> bool:
        return self.config.option.collectonly

    @pytest.hookimpl(tryfirst=True)
    def pytest_plugin_registered(self, plugin: PytestPluginType, plugin_name: str) -> None:
        if plugin_name == "terminalreporter":
            pass
            self.config.pluginmanager.set_blocked(plugin_name)

    @pytest.hookimpl(tryfirst=True)
    def pytest_configure(self, config: pytest.Config) -> None:
        # from pytest_textualize.plugin import TextualizeReporter
        # from pytest_textualize.plugin import TextualizePluginRegistrationService

        super().configure(config)
        self.pluginmanager = config.pluginmanager

        if self.verbosity > Verbosity.NORMAL or self.traceconfig:
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


        # -- Adding a list of textualize plugins to be monitored in plugin_registered hook
        from pytest_textualize.plugin import TextualizeReporter

        reporter_plugin = TextualizeReporter()
        # -- registering the reporter plugin
        self.pluginmanager.register(reporter_plugin, name=reporter_plugin.name)


    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session: pytest.Session) -> None:
        # from pytest_textualize.plugin import CollectorTracer
        # from pytest_textualize.plugin import HeaderServiceManager
        # from pytest_textualize.plugin import ErrorExecutionTracer
        # from pytest_textualize.plugin import TestRunResults

        precise_start = time.perf_counter()
        start = DateTime.now()
        self._start_time = start.to_time_string()
        self.results = TestRunResults(precise_start=precise_start, start=start)
        session.name = "pyest-textualize"

        # -- registering the error observer plugin to report detailed errors asap
        error_tracer_plugin = ErrorExecutionTracer(self.results)
        self.pluginmanager.register(error_tracer_plugin, name=error_tracer_plugin.name)
        # -- ensure unregister on the end of the execution
        self.cleanup_factory(error_tracer_plugin)

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

            from .helpers.header_renderer import header_console_renderable
            renderable = header_console_renderable(session.config, environment_data)
            self.console.print(Padding(renderable, (0, 0, 0, 2)))
            self.console.line(2)

    @pytest.hookimpl
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        # from pytest_textualize.plugin import RunTestTracer
        # from pytest_textualize.plugin import SummaryService

        if self.pluginmanager.has_plugin(TextualizePlugins.REGISTRATION_SERVICE):
            registration_service = self.pluginmanager.getplugin(TextualizePlugins.REGISTRATION_SERVICE)
            registration_service.monitored_classes.append(RunTestTracer.name)
            registration_service.monitored_classes.append(SummaryService.name)

        summary_service = SummaryService()
        self.pluginmanager.register(summary_service, summary_service.name)
        self.cleanup_factory(summary_service)

        if not self.collectonly:
            runtest_tracer = RunTestTracer(self.results)
            self.pluginmanager.register(runtest_tracer, runtest_tracer.name)
            self.cleanup_factory(runtest_tracer)

        plugin = session.config.pluginmanager.get_plugin(TextualizePlugins.COLLECTOR_TRACER)
        if plugin:
            session.config.pluginmanager.unregister(plugin, plugin.name)

    @pytest.hookimpl
    def pytest_keyboard_interrupt(self, excinfo: ExceptionInfo[KeyboardInterrupt | Exit]) -> None:
        self._keyboard_interrupt_memo = excinfo.getrepr(funcargs=True)

    @pytest.hookimpl
    def pytest_unconfigure(self, config: pytest.Config) -> None:
        if config.pluginmanager.has_plugin(TextualizePlugins.REGISTRATION_SERVICE):
            service = self.pluginmanager.getplugin(TextualizePlugins.REGISTRATION_SERVICE)
            self.pluginmanager.unregister(service, service.name)

        if self._keyboard_interrupt_memo is not None:
            self.report_keyboard_interrupt()

    def report_keyboard_interrupt(self) -> None:
        from pytest_textualize.plugin.exceptions import ConsoleMessage

        exc_type, exc_value, traceback = sys.exc_info()
        excrepr = self._keyboard_interrupt_memo
        assert excrepr is not None
        assert excrepr.reprcrash is not None
        msg = excrepr.reprcrash.message

        self.console.rule(Text(msg, style="#FF6363"), characters="!", style="#D14D72")
        if "KeyboardInterrupt" in msg:
            if self.config.option.fulltrace:
                excrepr.toterminal(self._tw)
            else:
                excrepr.reprcrash.toterminal(self._tw)
                self._tw.line(
                    "(to show a full traceback on KeyboardInterrupt use --full-trace)",
                    yellow=True,
                )

    @pytest.hookimpl(wrapper=True)
    def pytest_sessionfinish(
        self, session: pytest.Session, exitstatus: int | pytest.ExitCode
    ) -> Generator[None]:

        if not self.collectonly:
            results = hook_msg("pytest_sessionfinish", info=repr(exitstatus))
            self.console_logger.log(results, verbosity=Verbosity.VERBOSE)

        result = yield

        summary_exit_codes = (
            pytest.ExitCode.OK,
            pytest.ExitCode.TESTS_FAILED,
            pytest.ExitCode.INTERRUPTED,
            pytest.ExitCode.USAGE_ERROR,
            pytest.ExitCode.NO_TESTS_COLLECTED,
        )
        if exitstatus in summary_exit_codes and not self.no_summary:
            self.config.hook.pytest_terminal_summary(
                terminalreporter=self, exitstatus=exitstatus, config=self.config
            )
        if session.shouldfail:
            self.write_sep("!", str(session.shouldfail), red=True)
        if exitstatus == pytest.ExitCode.INTERRUPTED:
            self.report_keyboard_interrupt()
            self._keyboard_interrupt_memo = None
        elif session.shouldstop:
            self.write_sep("!", str(session.shouldstop), red=True)

        self.results.precise_finish = time.perf_counter()
        self.results.finish = DateTime.now()
        self.config.hook.pytest_stats_summary(config=self.config, terminalreporter=self)
        if not self.collectonly:
            stage_rule(self.console, "session", time_str=self.results.finish.to_time_string(), start=False)

        return result
