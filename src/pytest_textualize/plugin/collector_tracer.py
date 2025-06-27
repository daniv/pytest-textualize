from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from _pytest import timing
from _pytest.terminal import REPORT_COLLECTING_RESOLUTION
from boltons.strutils import cardinalize
from pendulum import DateTime
from rich.control import Control
from rich.padding import Padding
from rich.segment import ControlType
from rich.text import Text
from rich.traceback import PathHighlighter

from pytest_textualize import TextualizePlugins
from pytest_textualize.plugin.exceptions import ConsoleMessage
from pytest_textualize.textualize.verbose_log import Verbosity
from pytest_textualize import trace_logger
from pytest_textualize.plugin.base import BaseTextualizePlugin
from pytest_textualize.textualize import PrefixEnum
from pytest_textualize.textualize import hook_msg
from pytest_textualize.textualize import stage_rule

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from rich.console import Console
    from pytest_textualize.plugin import TestRunResults
    from pytest_textualize.settings import TextualizeSettings
    from rich.console import RenderableType


path_highlighter = PathHighlighter()


class CollectorTracer(BaseTextualizePlugin):
    name = TextualizePlugins.COLLECTOR_TRACER

    def __init__(self, results: TestRunResults) -> None:
        self.config: pytest.Config | None = None
        self.settings: TextualizeSettings | None = None
        self.console: Console | None = None
        self.results: TestRunResults = results
        self.pluginmanager: pytest.PytestPluginManager | None = None
        self.collect = results.collect

        self._start_time: str | None = None
        self._end_time: str | None = None
        self._last_write = timing.Instant()
        self._pytest_session: pytest.Session | None = None
        self.console_logger = trace_logger()


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
            f"started={getattr(self, "_start_time", "<UNSET>")} "
            f"ended={getattr(self, "_end_time", "<UNSET>")}>"
        )

    @property
    def collectonly(self) -> bool:
        return self.config.getoption("collectonly")

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        super().configure(config)
        self.pluginmanager = config.pluginmanager

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection(self, session: pytest.Session) -> None:
        """Called at the start of collection. """
        from pytest_textualize.plugin.model import TestCollectionRecord
        import time

        self._pytest_session = session

        precise_start = time.perf_counter()
        start = DateTime.now()
        self._start_time = start.to_time_string()
        self.collect = TestCollectionRecord(precise_start=precise_start, start=start)
        self.results.collect = self.collect

        if self.verbosity > Verbosity.NORMAL:
            stage_rule(self.console, "collection", time_str=self._start_time)
            node_id = session.nodeid if session.nodeid else session.name
            results = hook_msg("pytest_collection", info=node_id)
            self.console_logger.log(*results, verbosity=Verbosity.VERBOSE)

        end = "" if self.verbosity == Verbosity.NORMAL else "\n"
        if self.isatty:
            if self.verbosity >= Verbosity.NORMAL:
                self.console.print(f"[b]{PrefixEnum.PREFIX_SQUARE} collecting ... [/]", end=end)
                self.console.file.flush()
        elif self.verbosity >= Verbosity.NORMAL:

            self.console.print(f"[b]{PrefixEnum.PREFIX_SQUARE} collecting ... [/]", end=end)
            self.console.file.flush()

    @pytest.hookimpl
    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed:
            self.collect.stats.total_errors += 1
            if report.head_line in self.collect.errors:
                self.collect.errors[report.head_line].collect_report = report
        elif report.skipped:
            self.collect.stats.total_skipped += 1
        if self.isatty:
            self.report_collect()

    def report_collect(self, final: bool = False) -> None:
        if self.verbosity == Verbosity.QUIET:
            return None

        if not final:
            # Only write the "collecting" report every `REPORT_COLLECTING_RESOLUTION`.
            if self._last_write.elapsed().seconds < REPORT_COLLECTING_RESOLUTION:
                return None
            self._last_write = timing.Instant()

        dump = self.collect.stats.model_dump(mode="python", by_alias=True)
        prefix = ""
        if self.isatty:
            prefix = f" {PrefixEnum.PREFIX_SQUARE} "
        row: list[RenderableType] = [
            Text(
                f"{prefix}collected"
                if final
                else f" {PrefixEnum.PREFIX_SQUARE} collecting ", style="items"
            ),
            Text(f"{dump["collected"]} {cardinalize("item", dump["collected"])}", style="items"),
        ]
        if dump["errors"]:
            row.append(Text(f" / {dump["errors"]} {cardinalize("error", dump["errors"])}", style="error"))
        if dump["deselected"]:
            row.append(Text(f" / {dump["deselected"]} deselected", style="deselected"))
        if dump["skipped"]:
            row.append(Text(f" / {dump["skipped"]} skipped", style="skipped"))
        if dump["xfailed"]:
            row.append(Text(f" / {dump["xfailed"]} xfailed", style="xfailed"))
        if dump["collected"] > self.collect.stats.selected:
            row.append(Text(f" / {self.collect.stats.selected} selected", style="selected"))

        if self.isatty and self.verbosity == Verbosity.NORMAL:
            if self.verbosity == Verbosity.NORMAL:
                self.console.control(Control((ControlType.ERASE_IN_LINE, 2)))
                self.console.control(Control((ControlType.CURSOR_MOVE_TO_COLUMN, 0)))
                self.console.print(*row, end="")
                if final:
                    self.console.line()
        else:
            self.console.print(*row)
        return None

    @pytest.hookimpl(trylast=True, wrapper=True)
    def pytest_ignore_collect(self) -> Generator[None, object, object]:
        result = yield
        if result:
            self.collect.stats.total_ignored_collected += 1
        return result

    @pytest.hookimpl
    def pytest_itemcollected(self, item: pytest.Item) -> None:
        from pytest_textualize.plugin.model import SkipInfo, XfailInfo, NodeId
        from _pytest.skipping import evaluate_xfail_marks, evaluate_skip_marks

        self.collect.stats.total_collected += 1

        markers = [mark.name for mark in item.iter_markers()]

        node_id = NodeId(item.nodeid)
        skipped = evaluate_skip_marks(item)
        if skipped is not None:
            self.collect.stats.total_skipped += 1
            skip_info = SkipInfo(
                reason=skipped.reason,
                markers=markers,
            )
            if node_id not in self.collect.skip:
                self.collect.skip[node_id] = []
            self.collect.skip[node_id].append(skip_info)

        xfailed = evaluate_xfail_marks(item)
        if xfailed is not None:
            self.collect.stats.total_xfailed += 1
            xfail_info = XfailInfo(
                reason=xfailed.reason,
                raises=xfailed.raises,
                run=xfailed.run,
                strict=xfailed.strict,
                markers=markers,
            )
            if node_id not in self.collect.xfail:
                self.collect.xfail[node_id] = []
            self.collect.xfail[node_id].append(xfail_info)

        return None

    @pytest.hookimpl
    def pytest_deselected(self, items: Sequence[pytest.Item]) -> None:
        self.collect.stats.total_deselected += len(items)
        return None

    @pytest.hookimpl
    def pytest_pycollect_makemodule(self, module_path: Path, parent: pytest.Collector) -> pytest.Module | None:
        from _pytest.pathlib import import_path
        import traceback

        msg = hook_msg("pytest_pycollect_makemodule", info=parent.nodeid)
        self.console_logger.log(*msg, verbosity=Verbosity.VERBOSE)

        import_mode = self.config.getoption("--import-mode")
        try:
            consider_namespace_packages = self.config.getini("consider_namespace_packages")
            import_path(
                str(module_path),
                mode=import_mode,
                root=self.config.rootpath,
                consider_namespace_packages=consider_namespace_packages,
            )
        except (ImportError, ModuleNotFoundError, SyntaxError, BaseException) as exc:
            from pytest_textualize.plugin import TextualizeRuntimeError

            # todo: is already counted?
            self.collect.stats.total_collected += 1

            relative = module_path.relative_to(self.config.rootpath)
            ph = PathHighlighter()
            markup = ph(relative.as_posix()).markup
            tf = traceback.extract_tb(exc.__traceback__)[-1]

            messages = []
            msg = ConsoleMessage(debug=True,
                text="[python.line.comment]The error occurred while pytest was collecting a testing module.[/]\n"
                                      f"[scope.key_ni]module_path:[/] {markup}\n"
                                      f"[scope.key_ni]collector:[/] {str(parent)}\n"
                                      "The exception was caught on [pyest.hook.tag]hook: "
                     "[/][pyest.hook.name]pytest_pycollect_makemodule[/].\n"
                                 ).make_section("Causes", "    | ").text
            messages.append(msg)
            error = TextualizeRuntimeError.create(reason="Error collecting module", exception=exc, info=messages)

            from pytest_textualize.plugin.model import TestCollectionRecord
            record = TestCollectionRecord.create_error_model(when="collect", nodeid=str(module_path))
            record.exception = exc
            record.runtime_error = error
            self.results.collect.errors[str(relative.as_posix())] = record
            # 'tests/test_exceptions_console_message.py'
            self.console_logger.warning("Error collecting module", f"[white]{str(module_path)}[/]")
            self.console_logger.warning(f"message: {str(exc)}")
            if not self.isatty:
                cause_relative = module_path.relative_to(self.config.rootpath)
                location = f"{cause_relative.as_posix()}:{tf.lineno}"
                self.console.print("", location)

        return None

    @pytest.hookimpl
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        import time

        self.collect.precise_finish = time.perf_counter()
        self.collect.finish = DateTime.now()
        self._end_time = self.collect.finish.to_time_string()
        self.report_collect(True)

        lines = self.config.hook.pytest_report_collectionfinish(
            config=self.config,
            start_path=self.config.invocation_params.dir,
            items=session.items
        )
        for line in lines:
            if isinstance(line, list):
                for item in line:
                    self.console.print(item[0])
            self.console.print(line)

        if self.config.getoption("collectonly"):
            if session.items:
                from pytest_textualize.plugin import collect_only_report

                renderable = collect_only_report(session)
                self.console.print(Padding(renderable, (0, 0, 0, 3)), crop=False, overflow="ignore")

            if self.results.collect.errors_count > 0:
                pass

        results = hook_msg("pytest_collection_finish", info=session.name)
        self.console_logger.log(*results, verbosity=Verbosity.VERBOSE)
        stage_rule(self.console, "collection", time_str=self._end_time, start=False)
        return None

    @pytest.hookimpl
    def pytest_report_teststatus(  # type:ignore[empty-body]
        self, report: pytest.CollectReport | pytest.TestReport, config: pytest.Config
    ) -> pytest.TestShortLogReport | tuple[str, str, str | tuple[str, Mapping[str, bool]]]:
        pass

    @pytest.hookimpl
    def pytest_unconfigure(self, config: pytest.Config) -> None:
        pass
