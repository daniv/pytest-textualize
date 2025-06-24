# Project : pytest-textualize
# File Name : collector_observer.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

from typing import Any
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

from pytest_textualize import PrefixEnum
from pytest_textualize import TextualizePlugins
from pytest_textualize import Verbosity
from pytest_textualize import hook_msg
from pytest_textualize import stage_rule
from pytest_textualize.plugin.base import BaseTextualizePlugin

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from pathlib import Path
    from rich.console import Console
    from _pytest.compat import LEGACY_PATH
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
        self.results = results
        self.pluginmanager: pytest.PytestPluginManager | None = None
        self.collect = results.collect

        self._start_time: str | None = None
        self._end_time: str | None = None
        self._last_write = timing.Instant()
        self._pytest_session: pytest.Session | None = None


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
        import time

        self._pytest_session = session
        self.collect.precise_start = time.perf_counter()
        self.collect.start = DateTime.now()
        self._start_time = self.collect.start.to_time_string()

        if self.verbosity > Verbosity.NORMAL:
            stage_rule(self.console, "collection", time_str=self._start_time)
            node_id = session.nodeid if session.nodeid else session.name
            hook_msg("pytest_collection", info=node_id, console=self.console)

        end = "" if self.verbosity == Verbosity.NORMAL else "\n"
        if self.isatty:
            if self.verbosity >= Verbosity.NORMAL:
                self.console.print(f"[b] {PrefixEnum.PREFIX_SQUARE} collecting ... [/]", end=end)
                self.console.file.flush()
        elif self.verbosity >= Verbosity.NORMAL:

            self.console.print(f"[b] {PrefixEnum.PREFIX_SQUARE} collecting ... [/]", end=end)
            self.console.file.flush()

    @pytest.hookimpl
    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed:
            self.collect.stats.total_errors += 1
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
        self.collect.deselected = list(map(lambda x: x.nodeid, items))
        if self.verbosity > Verbosity.NORMAL:
            hook_msg("pytest_deselected", info=f"{len(items)} items were deselected", console=self.console)
        return None

    @pytest.hookimpl
    def pytest_pycollect_makemodule(self, module_path: Path, parent: pytest.Collector) -> pytest.Module | None:
        from _pytest.pathlib import import_path

        import_mode = self.config.getoption("--import-mode")
        try:
            consider_namespace_packages = self.config.getini("consider_namespace_packages")
            import_path(
                str(module_path),
                mode=import_mode,
                root=self.config.rootpath,
                consider_namespace_packages=consider_namespace_packages,
            )
        except (ImportError, ModuleNotFoundError, Exception) as exc:
            self.collect.stats.total_errors += 1
            self.collect.stats.total_collected += 1
            # ---> collect rt reerror    self.test_run_results.collect.error[str(module_path)] = exc
        #     import traceback
        #     tf = traceback.extract_tb(exc.__traceback__)[-1]
        #     from pytest_textualize.plugin.pytest_richtrace.exceptions import ConsoleMessage
        #     # from pytest_textualize.plugin.pytest_richtrace.exceptions import PytestTextualizeRuntimeError
        #     from rich.text import Text
        #     from rich.containers import Lines, Renderables
        #
        #     file = Path(tf.filename).relative_to(self.config.rootpath).as_posix()
        #     renderables = Renderables(
        #         [f"description: {exc.__doc__}", f"message: {tf.line}", f"file: {file}", f"lineno: {tf.lineno}"]
        #     )
        #     self.console.print(renderables)
        #     pass
        #
        #
        #     tb = [f"description:{exc.__doc__}", f"file:{file}", f"message:{tf.line}", f"lineno:{tf.lineno}"]
        #     Text()
        #     try:
        #         c = ConsoleMessage("\n".join(tb)).indent("  - ") #.style("#F6FFDE")
        #         self.console.print(c.text)
        #     except Exception as exc:
        #         pass
        #
        #
        #     c = ConsoleMessage("ddd").make_section("Causes", indent=" - ")
        #     self.console.print(c.text)
        #
        #     exc.add_note("hook pytest_pycollect_makemodule")
        #     reason = str(exc)
        #
        #     messages = [
        #         ConsoleMessage(
        #             "[bold]Causes:[/]\n"
        #             "  - The error occurred while pytest was collecting a testing module.\n"
        #             "  - The imported module is probably malformed and contains Syntax errors.\n"
        #             "  - network interruptions or errors causing corrupted downloads\n\n"
        #             "[b]Solutions:[/]\n"
        #             "  1. Try running your command again using the <c1>--no-cache</> global option enabled.\n"
        #             "  2. Try regenerating your lock file using (<c1>poetry lock --no-cache --regenerate</>).\n\n"
        #             "If any of those solutions worked, you will have to clear your caches using (<c1>poetry cache clear --all CACHE_NAME</>)."
        #         ),
        #     ]
        #     py = PytestTextualizeRuntimeError(reason, messages)
        #     error_console = console_factory(self.config, "stderr")
        #     py.write(error_console, self.config.option.verbose)
        #     pass
        #
        #     exc_type, exc_value, traceback = sys.exc_info()
        #     self.console.print_exception(max_frames=10)
        #     if not self.config.option.continue_on_collection_errors:
        #         pytest.exit(exc.msg)
        #     INDENT = "    "
        #
        #     # TODO: should be in reporter
        #     message = exc.msg
        #
        #     self.console.print(f"{INDENT}[error]Error collecting module[/]:")
        #     self.console.print(f"{INDENT * 2}[white]{module_path}[/]")
        #     if message:
        #         self.console.print(f"{INDENT * 2}{message}")
        #
        # raise PytestTextualizeRuntimeError(reason, messages)
        return None

    @pytest.hookimpl
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        import time

        self.collect.precise_finish = time.perf_counter()
        self.collect.finish = DateTime.now()
        self._end_time = self.collect.finish.to_time_string()
        self.report_collect(True)

        # lines = self.config.hook.pytest_report_collectionfinish(
        #     config=self.config,
        #     start_path=self.config.invocation_params.dir,
        #     items=session.items,
        # )
        # self._write_report_lines_from_hooks(lines)

        if self.config.getoption("collectonly"):
            if session.items:
                from pytest_textualize.plugin import collect_only_helper

                renderable = collect_only_helper(session, 0)
                self.console.print(Padding(renderable, (0, 0, 0, 3)), crop=False, overflow="ignore")

                renderable = collect_only_helper(session, 1)
                self.console.print(Padding(renderable, (0, 0, 0, 3)), crop=False, overflow="ignore")


                renderable = collect_only_helper(session, 2)
                self.console.print(Padding(renderable, (0, 0, 0, 3)), crop=False, overflow="ignore")
            # failed = self.stats.get("failed")
            # if failed:
            #     self._tw.sep("!", "collection failures")
            #     for rep in failed:
            #         rep.toterminal(self._tw)

        if self.verbosity > Verbosity.NORMAL:
            hook_msg("pytest_collection_finish", info=session.name, console=self.console)
            stage_rule(self.console, "collection", time_str=self._end_time, start=False)
        return None




    # @pytest.hookimpl
    # def pytest_pycollect_makeitem(
    #         self, collector: pytest.Module | pytest.Class, name: str, obj: object
    # ) -> None | pytest.Item | pytest.Collector | list[pytest.Item | pytest.Collector]:
    #     pass


    # @pytest.hookimpl
    # def pytest_collection_modifyitems(
    #         self, session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
    # ) -> None:
    #     self.pluginmanager.hook.pytest_report_collection_modifyitems(session=session, config=config, items=items)





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
        raise call.excinfo.value

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
