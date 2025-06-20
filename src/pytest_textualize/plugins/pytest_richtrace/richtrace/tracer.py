# Project : pytest-textualize
# File Name : manager.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import pluggy
import pytest

from pytest_textualize.settings import Verbosity

if TYPE_CHECKING:
    from pytest_textualize.plugins import TestRunResults
    from pytest_textualize.settings import TextualizeSettings
    from rich.console import Console


class TextualizeTracer:
    name: str = "pytest-textualize-tracer"

    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.console: Console | None = None
        self._lock = threading.Lock()
        self.settings: TextualizeSettings | None = None
        self.test_results: TestRunResults | None = None
        self.hook_relay: pluggy.HookRelay | None = None
        self._start_time: str | None = None

    @property
    def verbosity(self) -> Verbosity:
        return self.settings.verbosity

    @property
    def no_header(self) -> bool:
        return bool(self.config.option.no_header)

    @property
    def show_header(self) -> bool:
        return self.verbosity >= Verbosity.NORMAL

    def pytest_console_and_settings(self, console: Console, settings: TextualizeSettings) -> None:
        self.settings = settings
        self.console = console

    @pytest.hookimpl(tryfirst=True)
    def pytest_configure(self, config: pytest.Config) -> None:
        from pytest_textualize.plugins import cleanup_factory
        from pytest_textualize.plugins import TestRunResults
        from .textualize_reporter import TextualizeReporter
        from .error_observer import ErrorExecutionObserver

        pluginmanager = config.pluginmanager
        self.hook_relay = pluginmanager.hook

        # -- initializing the tests results model
        self.test_results = TestRunResults()

        # -- Adding a list of textualize plugins to be monitored in plugin_registered hook
        reporter = TextualizeReporter(config)
        reporter.monitored_classes.extend(
            [
                ErrorExecutionObserver.name,
                "textualize-collection-observer",
                "textualize-test-result-observer",
                "pytest-textualize",
                self.name,
            ]
        )

        # -- registering the reporter plugin
        pluginmanager.register(reporter, name=TextualizeReporter.name)

        # -- registering the error observer plugin to report detailed errors asap
        errors = ErrorExecutionObserver(config, self.test_results)
        pluginmanager.register(errors, name=ErrorExecutionObserver.name)
        # -- ensure unregister on the end of the execution
        config.add_cleanup(cleanup_factory(pluginmanager, errors))

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session: pytest.Session) -> None:
        from pydantic_extra_types.pendulum_dt import DateTime

        import time

        self.test_results.precise_start = time.perf_counter()
        self.test_results.start = DateTime.now()
        self._start_time = self.test_results.start.to_time_string()
        session.name = "pyest-textualize"
        self.settings.verbosity = Verbosity(session.config.option.verbose)

        from .collector_observer import CollectionObserver

        observer = CollectionObserver(session.config, self.test_results)
        session.config.pluginmanager.register(observer, name=CollectionObserver.name)

        if not self.show_header:
            return
        self.console.rule(
            f"[#D1F8EF]Session '{session.name}' started at {self._start_time}", characters="=", style="#A1E3F9"
        )
        if not self.no_header:
            from .services.header import HeaderServiceManager

            hook = session.config.pluginmanager.hook

            manager = HeaderServiceManager()
            manager.setup(session.config)
            manager.call(session.config)
            environment_data = hook.pytest_collect_env_info(config=session.config)
            manager.teardown(session.config)
            hook.pytest_render_header(config=session.config, data=environment_data)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"verbosity={self.verbosity!r} "
            f"started={getattr(self, "_start_time", "<UNSET>")}>"
        )
