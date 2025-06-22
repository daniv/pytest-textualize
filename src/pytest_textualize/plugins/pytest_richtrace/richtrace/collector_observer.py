# Project : pytest-textualize
# File Name : collector_observer.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

import sys
from functools import cached_property
from typing import Any
from typing import TYPE_CHECKING

import pytest
from pendulum import DateTime
from rich.traceback import PathHighlighter

from pytest_textualize.plugins.pytest_richtrace import console_key
from pytest_textualize.settings import Verbosity
from pytest_textualize.settings import settings_key
from pytest_textualize.textualize.hook_message import PrefixEnum
from pytest_textualize.textualize.hook_message import tracer_message

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from _pytest.compat import LEGACY_PATH
    from pytest_textualize.plugins import TestRunResults
    from pytest_textualize import TextualizeSettings
    from rich.console import Console
    from pathlib import Path


path_highlighter = PathHighlighter()

class CollectionObserver:
    name = "textualize-collection-observer"
    test_run_results: TestRunResults

    def __init__(self, config: pytest.Config, results: TestRunResults) -> None:
        self.config = config
        self.test_run_results = results
        self.console: Console = config.stash.get(console_key, None)
        self.settings: TextualizeSettings = config.stash.get(settings_key, None)
        self._start_time: str | None = None
        self._end_time: str | None = None
        self.pluginamanager = config.pluginmanager

    def __repr__(self) -> str:
        repr_str = (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"started={getattr(self, "_start_time", "<UNSET>")}>"
        )
        if self._end_time is None:
            return repr_str
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"started={getattr(self, "_end_time", "<UNSET>")}>"
        )

    @cached_property
    def isatty(self) -> bool:
        return sys.stdin.isatty()

    @property
    def verbosity(self) -> Verbosity:
        verbose = self.config.option.verbose
        return Verbosity(verbose)

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        pass

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
        trm = tracer_message("pytest_collection", info=node_id)

        if self.isatty:
            if self.config.option.verbose >= 0:

                self.console.print(f"[b] {PrefixEnum.PREFIX_SQUARE} collecting ... [/]")
                self.console.file.flush()
        elif self.config.option.verbose >= 1:
            trm(self.console)
            self.console.print(f"[b] {PrefixEnum.PREFIX_SQUARE} collecting ... [/]")
            self.console.file.flush()


    @pytest.hookimpl
    def pytest_collect_file(self) -> pytest.Collector | None:
        self.test_run_results.collect.files_collected += 1
        return None

    @pytest.hookimpl(trylast=True, wrapper=True)
    def pytest_ignore_collect(self) -> Generator[None, object, object]:
        result = yield
        if result:
            self.test_run_results.collect.ignored_collected += 1
        return result

    @pytest.hookimpl(tryfirst=True)
    def pytest_collect_directory(self) -> pytest.Collector | None:
        self.test_run_results.collect.directories_collected += 1
        return None

    @pytest.hookimpl
    def pytest_pycollect_makemodule(self, module_path: Path, parent: pytest.Collector) -> pytest.Module | None:
        from _pytest.pathlib import import_path

        import_mode = self.config.getoption("--import-mode")
        try:
            consider_namespace_packages = self.config.getini("consider_namespace_packages")
            import_path(str(module_path), mode=import_mode, root=self.config.rootpath,
                        consider_namespace_packages=consider_namespace_packages)
        except (ImportError, ModuleNotFoundError) as exc:
            self.test_run_results.collect.count += 1
            self.test_run_results.collect.error[str(module_path)] = exc
            exc_type, exc_value, traceback = sys.exc_info()
            self.console.print_exception(max_frames=10)
            if not self.config.option.continue_on_collection_errors:
                pytest.exit(exc.msg)
            INDENT = "    "

            # TODO: should be in reporter
            message = exc.msg

            self.console.print(f"{INDENT}[error]Error collecting module[/]:")
            self.console.print(f"{INDENT * 2}[white]{module_path}[/]")
            if message:
                self.console.print(f"{INDENT * 2}{message}")
        return None

    # @pytest.hookimpl
    # def pytest_pycollect_makeitem(
    #         self, collector: pytest.Module | pytest.Class, name: str, obj: object
    # ) -> None | pytest.Item | pytest.Collector | list[pytest.Item | pytest.Collector]:
    #     pass

    @pytest.hookimpl
    def pytest_itemcollected(self, item: pytest.Item) -> None:
        from .model import SkipInfo, XfailInfo, NodeId
        from _pytest.skipping import evaluate_xfail_marks, evaluate_skip_marks

        self.test_run_results.collect.count += 1

        markers = [mark.name for mark in item.iter_markers()]

        payload: dict[str, SkipInfo | XfailInfo] = {}
        node_id = NodeId(item.nodeid)

        skipped = evaluate_skip_marks(item)
        if skipped is not None:
            skip_info = SkipInfo(
                reason=skipped.reason,
                markers=markers,
            )
            if node_id not in self.test_run_results.collect.skip:
                self.test_run_results.collect.skip[node_id] = []
            self.test_run_results.collect.skip[node_id].append(skip_info)
            payload["skipped"] = skip_info

        xfailed = evaluate_xfail_marks(item)
        if xfailed is not None:
            xfail_info = XfailInfo(
                reason=xfailed.reason,
                raises=xfailed.raises,
                run=xfailed.run,
                strict=xfailed.strict,
                markers=markers,
            )
            if node_id not in self.test_run_results.collect.xfail:
                self.test_run_results.collect.xfail[node_id] = []
            self.test_run_results.collect.xfail[node_id].append(xfail_info)
            payload["xfail"] = xfail_info

        parameterize = item.get_closest_marker("parameterize")
        if parameterize:
            parametrize_argnames: set[str] = set()
            for marker in item.iter_markers(name="parametrize"):
                if not marker.kwargs.get("indirect", False):
                    p_argnames, _ = ParameterSet._parse_parametrize_args(
                        *marker.args, **marker.kwargs
                    )
                    parametrize_argnames.update(p_argnames)
            return parametrize_argnames

        return None

    # @pytest.hookimpl
    # def pytest_collection_modifyitems(
    #         self, session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
    # ) -> None:
    #     self.pluginamanager.hook.pytest_report_collection_modifyitems(session=session, config=config, items=items)

    @pytest.hookimpl
    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        pass

    @pytest.hookimpl
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        import time

        self.test_run_results.collect.precise_finish = time.perf_counter()
        self.test_run_results.collect.finish = DateTime.now()
        self._end_time = self.test_run_results.collect.finish.to_time_string()
        # todo: outcome or status

        if self.verbosity < Verbosity.VERBOSE:
            trm = tracer_message("pytest_collection_finish", info=session.name)
            trm(self.console)

        self.console.rule(
            f"[#D1F8EF]Collector finished at {self._end_time}", characters="=", style="#A1E3F9"
        )
        return None

    @pytest.hookimpl
    def pytest_report_collectionfinish(
            self,
            config: pytest.Config,
            start_path: Path,
            startdir: LEGACY_PATH,
            items: Sequence[pytest.Item],
    ) -> str | list[str]:
        pass


    @pytest.hookimpl
    def pytest_exception_interact(
            self,
            node: pytest.Item | pytest.Collector,
            call: pytest.CallInfo[Any],
            report: pytest.CollectReport | pytest.TestReport,
    ) -> None:
        pass






    @pytest.hookimpl
    def pytest_runtestloop(self, session: pytest.Session) -> object | None:
        pass

    @pytest.hookimpl
    def pytest_sessionfinish(
            self,
            session: pytest.Session,
            exitstatus: int | pytest.ExitCode,
    ) -> None:
        pass

    @pytest.hookimpl
    def pytest_terminal_summary(
            self,
            terminalreporter: pytest.TerminalReporter,
            exitstatus: pytest.ExitCode,
            config: pytest.Config,
    ) -> None:
        pass

    @pytest.hookimpl
    def pytest_report_teststatus(  # type:ignore[empty-body]
            self, report: pytest.CollectReport | pytest.TestReport, config: pytest.Config
    ) -> pytest.TestShortLogReport | tuple[str, str, str | tuple[str, Mapping[str, bool]]]:
        pass

    @pytest.hookimpl
    def pytest_unconfigure(self, config: pytest.Config) -> None:
        pass
