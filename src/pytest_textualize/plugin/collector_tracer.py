from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING
from typing import assert_never

import pytest
from _pytest import timing
from boltons.strutils import cardinalize
from pendulum import DateTime

from rich.control import Control
from rich.segment import ControlType
from rich.text import Text

from pytest_textualize import Textualize
from pytest_textualize import TextualizePlugins
from pytest_textualize import Verbosity
from pytest_textualize.factories.theme_factory import ThemeFactory
from pytest_textualize.plugin.base import BaseTextualizePlugin

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Sequence
    from rich.console import RenderableType
    from pytest_textualize.typist import TestRunResultsType
    from pytest_textualize.typist import ListAny
    from pathlib import Path
    from rich.console import ConsoleRenderable


path_highlighter = ThemeFactory.path_highlighter()


class CollectorTracer(BaseTextualizePlugin):
    name = TextualizePlugins.COLLECTOR_TRACER

    def __init__(self, results: TestRunResultsType) -> None:
        self.results = results
        self.pluginmanager: pytest.PytestPluginManager | None = None

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

    @pytest.hookimpl(tryfirst=True)
    def pytest_configure(self, config: pytest.Config) -> None:
        super().configure(config)

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        super().configure(config)
        self.pluginmanager = config.pluginmanager
        Textualize.print_pytest_textualize_sessionstart_header(self.console)

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection(self, session: pytest.Session) -> None:
        """Called at the start of collection."""
        import time

        self._pytest_session = session

        precise_start = time.perf_counter()
        start = DateTime.now()
        self._start_time = start.to_time_string()
        self.results.create_collect(precise_start=precise_start, start=start)

        if self.verbosity > Verbosity.NORMAL:
            Textualize.stage_rule(self.console, "collection", time_str=self._start_time)
            node_id = session.nodeid if session.nodeid else session.name
            msg, info, level = Textualize.hook_msg("pytest_collection", info=node_id)
            self.verbose_logger.log(msg, info, level_text=level, verbosity=Verbosity.VERBOSE)

        end = "" if self.verbosity == Verbosity.NORMAL else "\n"
        if self.isatty:
            if self.verbosity >= Verbosity.NORMAL:
                self.console.print(f"[b]▪ collecting ... [/]", end=end)
                self.console.file.flush()
        elif self.verbosity >= Verbosity.NORMAL:
            self.console.print(f"[b]▪ collecting ... [/]", end=end)
            self.console.file.flush()

    @pytest.hookimpl
    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed:
            self.results.collect.stats.total_errors += 1
            if report.head_line in self.results.collect.errors:
                self.results.collect.errors[report.head_line].collect_report = report
        elif report.skipped:
            self.results.collect.stats.total_skipped += 1
        if self.isatty:
            self.report_collect()

    @pytest.hookimpl
    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        hook, _, level = Textualize.hook_msg("pytest_collection_modifyitems")
        self.verbose_logger.log(hook, level_text=level, verbosity=Verbosity.VERBOSE)
        return None

    def report_collect(self, final: bool = False) -> None:
        from _pytest.terminal import REPORT_COLLECTING_RESOLUTION

        if self.verbosity == Verbosity.QUIET:
            return None

        if not final:
            # Only write the "collecting" report every `REPORT_COLLECTING_RESOLUTION`.
            if self._last_write.elapsed().seconds < REPORT_COLLECTING_RESOLUTION:
                return None
            self._last_write = timing.Instant()

        dump = self.results.collect.stats.model_dump(mode="python", by_alias=True)
        prefix = ""
        if self.isatty:
            prefix = "▪"
        row: list[RenderableType] = [
            Text(f"{prefix}collected" if final else f"▪ collecting ", style="items"),
            Text(f"{dump["collected"]} {cardinalize("item", dump["collected"])}", style="items"),
        ]
        if dump["errors"]:
            row.append(
                Text(f" / {dump["errors"]} {cardinalize("error", dump["errors"])}", style="error")
            )
        if dump["deselected"]:
            row.append(Text(f" / {dump["deselected"]} deselected", style="deselected"))
        if dump["skipped"]:
            row.append(Text(f" / {dump["skipped"]} skipped", style="skipped"))
        if dump["xfailed"]:
            row.append(Text(f" / {dump["xfailed"]} xfailed", style="xfailed"))
        if dump["collected"] > self.results.collect.stats.selected:
            row.append(Text(f" / {self.results.collect.stats.selected} selected", style="selected"))

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
            self.results.collect.stats.total_ignored_collected += 1
        return result

    def itemcollected(self, item: pytest.Item) -> None:
        if self.verbosity < Verbosity.VERBOSE:
            return None

        hook, info, level = Textualize.hook_msg("pytest_itemcollected", info=item.nodeid)
        self.verbose_logger.log(hook, info, level_text=level, verbosity=Verbosity.VERBOSE)

        markers = list(item.iter_markers())
        skip_markers = ", ".join([mark.name for mark in markers if mark.name.startswith("skip")])
        xfail_markers = ", ".join([mark.name for mark in markers if mark.name.startswith("xfail")])

        from _pytest.skipping import evaluate_skip_marks, evaluate_xfail_marks

        if skip_markers or xfail_markers:
            skipped = evaluate_skip_marks(item)
            if skipped is not None:
                renderables = key_value_scope(
                    [
                        ("type", "[skip]skip[/]"),
                        ("reason", Text(skipped.reason)),
                        ("marker", Text(f"@{skip_markers}", style="#B3AE60")),
                    ]
                )
                self.console.print(renderables)

            xfailed = evaluate_xfail_marks(item)
            if xfailed is not None:
                xfail_list = [
                    ("type", f"[xfail]xfail[/]"),
                    ("reason", Text(xfailed.reason)),
                    ("run", str(xfailed.run)),
                    ("strict", str(xfailed.strict)),
                ]
                if xfailed.raises:
                    xfail_list.append(("raises", str(xfailed.raises)))
                    xfail_list.append(("marker", Text(f"@{skip_markers}", style="#B3AE60")))

                renderables = key_value_scope(xfail_list)
                self.console.print(renderables)

        return None

    @pytest.hookimpl
    def pytest_itemcollected(self, item: pytest.Item) -> None:
        from pytest_textualize.model import SkipInfo, XfailInfo, NodeId
        from _pytest.skipping import evaluate_xfail_marks, evaluate_skip_marks

        self.results.collect.stats.total_collected += 1
        hook, info, level = Textualize.hook_msg("pytest_itemcollected", info=item.nodeid)
        self.verbose_logger.log(hook, info, level_text=level, verbosity=Verbosity.VERBOSE)

        markers = [mark.name for mark in item.iter_markers()]

        node_id = NodeId(item.nodeid)
        skipped = evaluate_skip_marks(item)
        if skipped is not None:
            self.results.collect.stats.total_skipped += 1
            skip_info = SkipInfo(
                reason=skipped.reason,
                markers=markers,
            )
            if node_id not in self.results.collect.skip:
                self.results.collect.skip[node_id] = []
            self.results.collect.skip[node_id].append(skip_info)

        xfailed = evaluate_xfail_marks(item)
        if xfailed is not None:
            self.results.collect.stats.total_xfailed += 1
            xfail_info = XfailInfo(
                reason=xfailed.reason,
                raises=xfailed.raises,
                run=xfailed.run,
                strict=xfailed.strict,
                markers=markers,
            )
            if node_id not in self.results.collect.xfail:
                self.results.collect.xfail[node_id] = []
            self.results.collect.xfail[node_id].append(xfail_info)

        self.itemcollected(item)
        return None

    @pytest.hookimpl
    def pytest_deselected(self, items: Sequence[pytest.Item]) -> None:
        self.results.collect.stats.total_deselected += len(items)
        return None

    def _pytest_pycollect_makemodule(
        self, module_path: Path, parent: pytest.Collector
    ) -> pytest.Module | None:
        from _pytest.pathlib import import_path

        try:
            import_mode = self.config.getoption("--import-mode")
            consider_namespace_packages = self.config.getini("consider_namespace_packages")
            import_path(
                str(module_path),
                mode=import_mode,
                root=self.config.rootpath,
                consider_namespace_packages=consider_namespace_packages,
            )
        except (SyntaxError, ValueError, Exception) as exc:
            from pathlib import Path

            # todo: is already counted?
            self.results.collect.stats.total_collected += 1

            hook, info, level = Textualize.hook_msg(
                "pytest_pycollect_makemodule", info=parent.nodeid
            )
            self.verbose_logger.log(hook, info, level_text=level, verbosity=Verbosity.VERBOSE)
            self.verbose_logger.warning("error message", str(exc))
            error_tracer = self.config.pluginmanager.get_plugin(TextualizePlugins.ERROR_TRACER)

            from pytest_textualize.textualize.tracebacks import TextualizeTracebacks

            exceptions_info = TextualizeTracebacks.from_exception(exc)
            path = Textualize.relative_path(module_path).as_posix()
            ph = ThemeFactory.path_highlighter()
            # error_tracer.make_error_report(
            #     exception_info=exceptions_info, collector=parent,
            #     message=Text("Reason: error while collecting module").append_text(ph(path)).markup
            # )

            # relative = Textualize.relative_path(module_path)
            # ph = ThemeFactory.path_highlighter()
            # rep_h = ThemeFactory.repr_highlighter()
            # if isinstance(exc, SyntaxError):
            #     link_path = Textualize.create_link(
            #         exc.filename, exc.lineno, self.isatty, use_click=True, click_location="before"
            #     )
            #     lines = Lines(
            #         [
            #             Text("Reason: error while collecting module on ").append("pytest_pycollect_makemodule", style="b"),
            #             Text(" | Error type: ").append("SyntaxError", style="python.builtin"),
            #             Text(" | Error path: ").append_text(ph(relative.as_posix())),
            #             Text(" | Error message: ").append_text(rep_h(f"'{exc.msg}'")),
            #             # Text("  Error Message: ").append(f"'{exc.msg}'"),
            #             Text(" | Location link: ").append(link_path),
            #         ]
            #     )
            #     self.console.print(lines, style="bright_red")
            #     self.console.log(lines)
            #     self.verbose_logger.warning(lines)
            #     pass
            # markup = ph(relative.as_posix()).markup
            # if isinstance(exc, SyntaxError):
            #     if self.isatty:
            #         link = (
            #             f"[bright_blue][link={exc.filename}:{exc.lineno}]"
            #             f"{relative.name}#{exc.lineno}[/link] {chr(0x2b84)} click[/]"
            #         )
            #     else:
            #         link = f" File {relative.as_posix()}:{exc.lineno}"
            #     logs = [
            #         "Description  : error while collecting module",
            #         f"[scope.key_ni]  Error Type   :[/] [python.builtin]SyntaxError[/]",
            #         f"[scope.key_ni]  Error Path   :[/] {markup}",
            #         f"[scope.key_ni]  Error Message:[/] {exc.msg}",
            #         f"  Location     : {link}"
            #     ]
            #
            #     self.console.print("\n".join(logs))
            #     self.verbose_logger.warning("\n".join(logs))
            #     from_exc_info = pytest.ExceptionInfo.from_exc_info(sys.exc_info())
            #     msg = ConsoleMessage(debug=True,
            #         text="[python.line.comment]The error occurred while pytest was collecting a testing module.[/]\n"
            #                               f"[scope.key_ni]module_path:[/] {markup}\n"
            #                               f"[scope.key_ni]collector:[/] {str(parent)}\n"
            #                               "The exception was caught on [pyest.hook.tag]hook: "
            #              "[/][pyest.hook.name]pytest_pycollect_makemodule[/].\n"
            #                          ).make_section("Causes", "    | ").text
            #
            #     plugin = self.pluginmanager.get_plugin(TextualizePlugins.ERROR_TRACER)
            #     plugin.make_error_report(from_exc_info, msg)

            #     record = self.results.create_error_model(when="collect")
            #
            #     error = TextualizeRuntimeError.create(reason="Error collecting module", exception=exc, info=messages)
            #
            #
            #
            # self.results.collect.errors[str(relative.as_posix())] = record
            # # 'tests/test_exceptions_console_message.py'
            # self.console_logger.warning("Error collecting module", f"[white]{str(module_path)}[/]")
            # self.console_logger.warning(f"message: {str(exc)}")
            # if not self.isatty:
            #     cause_relative = module_path.relative_to(self.config.rootpath)
            #     location = f"{cause_relative.as_posix()}:{tf.lineno}"
            #     self.console.print("", location)

        return None

    @pytest.hookimpl
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        import time
        from rich.padding import Padding

        self.results.collect.precise_finish = time.perf_counter()
        self.results.collect.finish = DateTime.now()
        self._end_time = self.results.collect.finish.to_time_string()
        self.report_collect(True)

        lines = self.config.hook.pytest_report_collectionfinish(
            config=self.config, start_path=self.config.invocation_params.dir, items=session.items
        )
        for line in lines:
            if isinstance(line, list):
                for item in line:
                    self.console.print(item[0])
            self.console.print(line)

        if self.config.getoption("collectonly"):
            if session.items:
                renderable = collect_only_report(session)
                self.console.print(Padding(renderable, (0, 0, 0, 3)), crop=False, overflow="ignore")

            if self.results.collect.errors_count > 0:
                pass

        hook, info, level = Textualize.hook_msg("pytest_collection_finish", info=session.name)
        self.verbose_logger.log(hook, info, level_text=level, verbosity=Verbosity.VERBOSE)
        Textualize.stage_rule(self.console, "collection", time_str=self._end_time, start=False)
        return None

    @pytest.hookimpl
    def pytest_make_collect_report(self, collector: pytest.Collector) -> None:
        if self.verbosity <= Verbosity.VERBOSE or collector.nodeid == "":
            return
        if isinstance(collector, pytest.Session):
            info = f'pytest.Session -> "{collector.nodeid}"'
        elif isinstance(collector, pytest.Directory):
            info = f'pytest.Directory -> "{collector.nodeid}"'
        elif isinstance(collector, pytest.File):
            info = f'pytest.File -> "{collector.nodeid}"'
        else:
            assert_never("unsupported collector")
        hook, info, level = Textualize.hook_msg("pytest_make_collect_report", info=info)
        self.verbose_logger.log(hook, info, level_text=level, verbosity=Verbosity.VERBOSE)

    @pytest.hookimpl
    def pytest_report_collectionfinish(
        self, items: Sequence[pytest.Item]
    ) -> ConsoleRenderable | ListAny | str | None:
        if not self.collectonly and self.verbosity > Verbosity.NORMAL:
            return collect_only_report(None, items)
        return None

    @pytest.hookimpl
    def pytest_unconfigure(self) -> None:
        msg, info, level = Textualize.hook_msg("pytest_unconfigure", info=self.__class__.__name__)
        self.verbose_logger.log(msg, info, level_text=level, verbosity=Verbosity.VERBOSE)


def collect_only_report(
    session: Optional[pytest.Session], pyt_items: Optional[Sequence[pytest.Item]] = None
) -> ConsoleRenderable:
    import inspect
    from rich.tree import Tree
    from rich.panel import Panel
    from rich import box
    from rich.columns import Columns
    from rich.console import Group
    from rich.markup import escape
    from rich.table import Table
    from _pytest.nodes import Node
    from collections import Counter

    def collected_tree() -> ConsoleRenderable:

        def _format_node(node: Node) -> RenderableType:
            type_name = node.__class__.__name__.lower()
            name_style = "i #BBE9FF"

            match type_name:
                case "dir":
                    renderable = (
                        Text(f"<Dir: ", style="#FFEEA9")
                        .append(node.name, style=name_style)
                        .append(">", style="#FFEEA9")
                    )
                case "package":
                    renderable = (
                        Text(f"<Package: ", style="#4CC9FE")
                        .append(node.name, style=name_style)
                        .append(">", style="#4CC9FE")
                    )
                case "module":
                    renderable = (
                        Text(f"<Module: ", style="#6FE6FC")
                        .append(node.name, style=name_style)
                        .append(">", style="#6FE6FC")
                    )
                case "function":
                    renderable = (
                        Text(f"<Function: ", style="#4ED7F1")
                        .append(node.name, style=name_style)
                        .append(">", style="#4ED7F1")
                    )
                case _:
                    assert_never(type_name)

            obj = getattr(node, "obj", None)
            doc = inspect.getdoc(obj) if obj else None
            if doc:
                table = Table(show_header=False, safe_box=True, show_edge=True, style="#4CC9FE")
                table.add_column("Doc", style="#BBE9FF", no_wrap=True)
                for line in doc.splitlines():
                    table.add_row(line)

                return Group(renderable, table)

            return renderable

        root = Tree("pytest session", highlight=False, hide_root=True)
        stack: list[Node] = []
        tree_stack: list[Tree] = []
        for item in session.items:
            needed_collectors = item.listchain()[1:]  # strip root node
            while stack:
                if stack == needed_collectors[: len(stack)]:
                    break
                stack.pop()
                tree_stack.pop()
            for col in needed_collectors[len(stack) :]:
                formatted_node = _format_node(col)
                if len(stack) == 0:
                    leaf = root.add(formatted_node, guide_style="#BBE9FF", highlight=False)
                    tree_stack.append(leaf)
                else:
                    tree_stack.append(
                        tree_stack[-1].add(formatted_node, guide_style="#BBE9FF", highlight=False)
                    )
                stack.append(col)
        panel = Panel(
            root,
            expand=False,
            box=box.DOUBLE,
            padding=(1, 2, 1, 4),
            title="Execution Plan",
            style="#578FCA",
            subtitle="collect-only",
            subtitle_align="left",
        )
        return panel

    def collected_list() -> ConsoleRenderable:
        renderables: list[str] = []
        for i, item in enumerate(session.items, start=1):
            renderables.append(f"[#9FB3DF]{i}.[/]{escape(item.name)}")
        return Panel(
            Columns(renderables, column_first=True, expand=True),
            title="[#C5D3E8]Selected items",
            style="#BBE9FF",
            border_style="#4CC9FE",
            box=box.DOUBLE,
            padding=(1, 0, 0, 1),
        )

    def collected_groups(items: Sequence[pytest.Item] | None = None) -> ConsoleRenderable:

        def get_content(n: str, c: int):
            return path_highlighter(
                Text.from_markup(
                    f"[pytest.name]{n}[/]\n[pytest.version]{c}[/]",
                    justify="center",
                )
            )

        if session is not None:
            items = session.items

        counts = Counter(item.nodeid.split("::", 1)[0] for item in items)
        renderables = [
            Panel(get_content(name, count), expand=False) for name, count in sorted(counts.items())
        ]
        return Panel(
            Columns(renderables, column_first=True, expand=False),
            title="[#EAE4D5]Selected Items by module",
            style="#D29F80",
            border_style="#735557",
            box=box.DOUBLE,
            padding=(1, 0, 0, 1),
        )

    if pyt_items:
        return collected_groups(pyt_items)

    test_cases_verbosity = session.config.get_verbosity(pytest.Config.VERBOSITY_TEST_CASES)
    if test_cases_verbosity < 0:
        if test_cases_verbosity < -1:
            return collected_groups()
        else:
            return collected_list()
    return collected_tree()


# if self.verbosity > Verbosity.VERBOSE and hasattr(item, "callspec"):
#
#             table = Table.grid(expand=False)
#             table.add_column(justify="right", style="cyan")
#             table.add_column(justify="right", style="cyan")
#             table.add_row("nodeid", item.nodeid)
#             table.add_row("name", item.name)
#             if hasattr(item, "originalname"):
#                 table.add_row("originalname", item.originalname)
#             import copy
#             deep_copied_dict = copy.deepcopy(item.callspec.__dict__)
#             scope = render_scope(
#                 dict(
#                     params=deep_copied_dict.get("params", {}),
#                     indices=deep_copied_dict.get("indices", {}),
#                     idlist=deep_copied_dict.get("_idlist", {}),
#                     marks=deep_copied_dict.get("marks", {}),
#                 ),
#                 title="callspec",
#                 sort_keys=True,
#             )
#             p = Panel(Group(table, scope))
#             item.stash[item_stash] = p
#
#             r = keyval_msg(
#                 "pytest.Item.callspec",
#                 render_scope(
#                     dict(
#                         params=deep_copied_dict.get("params", {}),
#                         indices=deep_copied_dict.get("indices", {}),
#                         idlist=deep_copied_dict.get("_idlist", {}),
#                         marks=deep_copied_dict.get("marks", {}),
#                     ),
#                     title="callspec",
#                     sort_keys=True,
#                 ),
#                 value_style="scope.fill",
#                 # console=self.console,
#             )
