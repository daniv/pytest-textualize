from __future__ import annotations

import hashlib
import os
import sys
import warnings
from contextlib import suppress
from types import ModuleType
from typing import Any
from typing import NotRequired
from typing import TYPE_CHECKING
from typing import TypedDict
from typing import Unpack

import pytest
from rich.padding import Padding
from rich.syntax import Syntax
from rich.syntax import SyntaxTheme
from rich.text import Text

from pytest_textualize import ConsoleMessage
from pytest_textualize import Textualize
from pytest_textualize import TextualizePlugins
from pytest_textualize import Verbosity
from pytest_textualize.factories.theme_factory import ThemeFactory
from pytest_textualize.plugin.base import BaseTextualizePlugin

if TYPE_CHECKING:
    from traceback import FrameSummary
    from _pytest._code import TracebackEntry
    from _pytest._code import ExceptionInfo
    from _pytest._code.code import ExceptionRepr
    from _pytest.outcomes import Exit
    from collections.abc import Iterable
    from rich.console import Console
    from pytest_textualize.typist import TestRunResultsType


def suppress(modules: Iterable[str | ModuleType]) -> Iterable[str | ModuleType]:
    suppressions = []
    for suppress_entity in modules:
        if not isinstance(suppress_entity, str):
            assert (
                suppress_entity.__file__ is not None
            ), f"{suppress_entity!r} must be a module with '__file__' attribute"
            path = os.path.dirname(suppress_entity.__file__)
        else:
            path = suppress_entity
        path = os.path.normpath(os.path.abspath(path))
        suppressions.append(path)
    return suppressions


class ErrorExecutionTracer(BaseTextualizePlugin):
    name = TextualizePlugins.ERROR_TRACER

    def __init__(self, results: TestRunResultsType):
        self.error_console: Console | None = None
        self.results = results
        self._keyboard_interrupt_memo: ExceptionRepr | None = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} " f"name='{self.name}'>"

    @property
    def keyboard_interrupt_memo(self) -> ExceptionRepr | None:
        return self._keyboard_interrupt_memo

    @keyboard_interrupt_memo.setter
    def keyboard_interrupt_memo(self, value: ExceptionRepr | None) -> None:
        self._keyboard_interrupt_memo = value

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        from pytest_textualize.plugin import error_console_key

        super().configure(config)
        setattr(config, "_already_displayed_warnings", [])
        self.error_console = self.config.stash[error_console_key]

    @pytest.hookimpl
    def pytest_warning_recorded(
        self,
        warning_message: warnings.WarningMessage,
        nodeid: str,
    ) -> None:

        hook, info, level = Textualize.hook_msg("pytest_warning_recorded", info=nodeid)
        self.verbose_logger.log(hook, info, level_text=level, verbosity=Verbosity.VERBOSE)
        key, val, level = Textualize.keyval_msg(
            "category", warning_message.category.__name__, value_style="python.builtin"
        )
        self.verbose_logger.log(key, val, level_text=level, verbosity=Verbosity.VERBOSE)
        key, val, level = Textualize.keyval_msg("doc", warning_message.category.__doc__)
        self.verbose_logger.log(key, val, level_text=level, verbosity=Verbosity.VERBOSE)
        encoded_string = str(warning_message.message).encode("utf-8")
        hasher = hashlib.sha256()
        hasher.update(encoded_string)
        from pytest_textualize.model import WarningReport

        wr = WarningReport(
            msg_256=hasher.hexdigest(),
            lineno=warning_message.lineno,
            filename=warning_message.filename,
            category=warning_message.category,
            nodeid=nodeid,
            messages=str(warning_message.message).splitlines(),
        )
        self.results.warnings.append(wr)

    @pytest.hookimpl
    def pytest_internalerror(
        self,
        excrepr: ExceptionRepr,
        excinfo: pytest.ExceptionInfo[BaseException],
    ) -> bool | None:
        import pluggy
        import _pytest
        import traceback
        from rich.console import render_scope

        try:
            hook, info, level = Textualize.hook_msg(
                "pytest_internalerror", info=f"[python.builtin]{excinfo.typename}[/]"
            )
            self.verbose_logger.log(
                hook, info, level_text=level, verbosity=Verbosity.VERBOSE, log_locals=True
            )
            self.console.line()
            self.console.rule(
                title="[#C5172E]INTERNAL ERROR[/]", style="bright_red", characters="="
            )
            suppress_modules = suppress([pluggy, _pytest])

            path_h = ThemeFactory.path_highlighter()
            relative = Textualize.relative_path(excrepr.reprcrash.path)
            path = path_h(relative.as_posix()).markup
            messages = [
                f"message: {excrepr.reprcrash.message}",
                f"path: {path}",
                f"lineno: {excrepr.reprcrash.lineno}",
            ]
            text = (
                ConsoleMessage(text="\n".join(messages))
                .make_section("Crash Information", indent="   | ")
                .text
            )
            self.verbose_logger.error(text)
            link = Textualize.create_link(
                excrepr.reprcrash.path, excrepr.reprcrash.lineno, self.isatty
            )
            self.verbose_logger.error("crash location ⮆ ", link)

            for entry in excrepr.reprtraceback.reprentries:
                for line in entry.lines:
                    if list(filter(lambda c: line.find(c) > 0, suppress_modules)):
                        self.verbose_logger.error(
                            "INTERNALERROR>", line.splitlines()[0], highlight=True
                        )
                    else:
                        self.verbose_logger.error(
                            "INTERNALERROR>", line[:-1], highlight=True, log_locals=True
                        )
                        if "File " not in line:
                            continue
                        fs = traceback.extract_tb(excinfo.tb)[-1]
                        tbe = excinfo.traceback[-1]
                        theme = self.settings.tracebacks_settings._syntax_theme
                        syntax = syntax_from_frame_summary(theme, fs, tbe, self.console.width - 40)
                        t = syntax.highlight("".join(tbe.source.raw_lines), (1, 3))
                        self.console.print(t)
                        self.console.print(syntax)
                        # self.error_console.print(Padding(syntax, (0, 0, 0, 2)))

                        if tbe.locals:
                            locals_ = render_scope(
                                tbe.locals,
                                title="locals",
                                indent_guides=self.settings.tracebacks_settings.indent_guides,
                                max_length=self.settings.tracebacks_settings.locals_max_length,
                                max_string=self.settings.tracebacks_settings.locals_max_string,
                            )
                            self.error_console.print(Padding(locals_, (0, 0, 0, 2)))

            self.console.rule(
                title="[#C5172E]END INTERNAL ERROR[/]", style="bright_red", characters="="
            )
        except (SyntaxError, Exception) as exc:
            self.verbose_logger.warning("error while printing traceback -> ", str(exc))
            for line in str(excrepr).split("\n"):
                self.verbose_logger.error("INTERNALERROR> " + line)
            return True
        return False

    @pytest.hookimpl
    def pytest_exception_interact(
        self,
        node: pytest.Item | pytest.Collector,
        call: pytest.CallInfo[Any],
        report: pytest.CollectReport | pytest.TestReport,
    ) -> None:
        hook, info, level = Textualize.hook_msg(
            "pytest_exception_interact", info=f"[python.builtin]{call.excinfo.typename}[/]"
        )
        self.verbose_logger.log(hook, info, level_text=level, verbosity=Verbosity.NORMAL)
        self.verbose_logger.warning("error message", str(call.excinfo.value))

        if isinstance(report, pytest.CollectReport):
            self.make_error_report("pytest_exception_interact", node, call, report)
        else:
            self.verbose_logger.error(f"Error message ⟶ {str(call.excinfo.value)}.", highlight=True)

        # from boltons.tbutils import ExceptionInfo
        # exc_traceback = call.excinfo.tb
        # exc_info = ExceptionInfo.from_exc_info(call.excinfo.type, call.excinfo.value, call.excinfo.tb)
        # tbi = TracebackInfo.from_traceback(exc_traceback)
        # pass
        #
        # long = call.excinfo.getrepr(showlocals=True, style="long")
        # native = call.excinfo.getrepr(showlocals=True, style="native")
        # short = call.excinfo.getrepr(showlocals=True, style="short")
        # value = call.excinfo.getrepr(showlocals=True, style="value")
        # no = call.excinfo.getrepr(showlocals=True, style="no")
        # if isinstance(report, pytest.CollectReport):
        #     if node.nodeid in self.results.collect.errors:
        #         if self.tb_style == "no":
        #             runtime_err = self.results.collect.errors[node.nodeid].runtime_err
        #             runtime_err.write(self.error_console)
        #     else:
        #         record = ModelFactory.create_error_model(when=report.when, nodeid=node.nodeid)
        #         record.collect_report = report
        #         messages = []
        #         msg = ConsoleMessage(debug=True,
        #                              text=f"The error occurred on stage '{report.when}'.\n"
        #                                   f"[scope.key_ni]nodeid:[/] {node.nodeid}\n"
        #                                   f"[scope.key_ni]name:[/] {node.name}\n"
        #                                   "The exception was caught on [pyest.hook.tag]hook: "
        #                                   "[/][pyest.hook.name]pytest_exception_interact[/].\n"
        #                              ).make_section("Causes", "    | ").text
        #         messages.append(msg)
        #         exc = cast(BaseException, call.excinfo.value)
        #         from pytest_textualize.plugin import TextualizeRuntimeError
        #         error = TextualizeRuntimeError.create(reason="Error collecting module", exception=exc, info=messages)
        #         record.runtime_error = error
        #
        #         self.results.collect.errors[report.head_line] = record

    class ReportTypeDict(TypedDict):
        node: NotRequired[pytest.Item | pytest.Collector]
        call: NotRequired[pytest.CallInfo[Any]]
        report: NotRequired[pytest.CollectReport | pytest.TestReport]
        message: NotRequired[str]
        exception_info: NotRequired[ExceptionInfo[BaseException]]
        collector: NotRequired[pytest.Collector]

    def make_error_report(self, *args, **kwargs: Unpack[ReportTypeDict]) -> None:
        import inspect
        from rich.containers import Lines
        from rich.console import Group
        from rich.padding import Padding

        from rich.table import Table
        from pytest_textualize.factories.theme_factory import ThemeFactory

        when = ""
        nodeid = ""
        node_name = ""
        collector_type = ""
        exc_info = None
        caller = inspect.stack()[1].function
        if caller == "pytest_pycollect_makemodule":
            when = "collect"
            exc_info = kwargs.pop("exception_info", None)
            collector = kwargs.pop("collector", None)
            nodeid = collector.nodeid
            node_name = collector.name
            collector_type = str(collector)
            if "message" in kwargs:
                message = kwargs.pop("message")
                caller += "\n" + message

        repr_h = ThemeFactory.repr_highlighter()
        path_h = ThemeFactory.path_highlighter()

        txt = Text(f" ≫ hook {caller} was invoked")
        txt.highlight_words([caller], style="pyest.hook.name")

        node_table = Table.grid(padding=(0, 1))
        node_table.add_column(justify="left")
        node_table.add_column(justify="left", style="scope.key_ni")
        node_table.add_row("|", "when: ", when)
        node_table.add_row("|", "node type: ", node.__class__.__name__)
        node_table.add_row("|", "node name: ", node_name)
        node_table.add_row("|", "node id: ", nodeid)
        te = exc_info.traceback[-1]
        relative = Textualize.relative_path(te.path)
        link = Textualize.create_link(str(te.path), te.lineno, sys.stdout.isatty(), use_click=True)
        lines = Lines(
            [
                Text(" | ".rjust(9))
                .append("File")
                .append(" = ", style="i")
                .append_text(path_h(relative.as_posix())),
                Text(" | ".rjust(9))
                .append("Function")
                .append(" = ", style="i")
                .append(te.name, style="i"),
                Text(" | ".rjust(9))
                .append("Lineno")
                .append(" = ", style="i")
                .append_text(repr_h(str(te.lineno))),
                Text(" | ".rjust(9))
                .append("Statement ↦ ")
                .append(Text("\n".join(te.statement).strip(), style="white")),
                Text(" | ".rjust(9)).append(link).append(" ", style="reset"),
            ]
        )

        group = Group(
            txt,
            Text("\n Node Details:", style="b"),
            Padding(node_table, pad=(0, 0, 0, 8)),
            Text("\n Documentation:", style="white b"),
            Text(f"{" | ".rjust(9)}{exc_info.value.__doc__}", style="white", end="\n\n"),
            Text(" Exception Message:", style="b"),
            repr_h(f"{" | ".rjust(9)}{str(exc_info.value)}\n"),
            Text(" Exception Details:", style="b"),
            lines,
        )
        from rich.panel import Panel

        title = f"[b]{str(exc_info.type)}[/b]"
        panel = Panel(group, title=title, style="red", width=120)
        theme = self.settings.tracebacks_settings._syntax_theme
        syntax = syntax_from_tb_entry(theme, te, self.console.width - 20)
        if isinstance(report, pytest.CollectReport):
            self.results.collect.register_error(
                report.nodeid, exc_info.value, report, panel, syntax
            )
        return None

    def makzzze_error_report(
        self, excinfo: ExceptionInfo[BaseException], message: ConsoleMessage | None = None
    ) -> None:
        traceback_entry = excinfo.traceback[-1]
        ph = Textualize.theme_factory().path_highlighter()
        path = traceback_entry.path.relative_to(self.config.rootpath)
        link = f"{traceback_entry.path.as_posix()}:{traceback_entry.lineno}"
        if self.isatty:
            link = f"[link={link}]{path.name}:{traceback_entry.lineno}[/link]"
        lines = [
            f"[scope.key_ni]error type:[/] [python.builtin]{excinfo.typename}[/]",
            f"message: {str(excinfo.value)}",
            f"path: {ph(path.as_posix()).markup}",
            f"func: {traceback_entry.name}",
            f"lineno: {traceback_entry.lineno}",
            f"link: {link}",
        ]
        text = (
            ConsoleMessage(text="\n".join(lines)).make_section("Exception Information", "  | ").text
        )
        self.console_logger.error(text)
        self.error_console.print(text)
        from rich.syntax import Syntax

        themes = ThemeFactory.syntax_theme()
        syntax = Syntax(
            "".join(traceback_entry.source.raw_lines),
            lexer="python",
            code_width=self.error_console.width - 20,
            line_numbers=True,
            theme=Syntax.get_theme("pycharm_dark"),
            indent_guides=True,
            highlight_lines={traceback_entry.lineno},
            padding=1,
            start_line=traceback_entry.lineno - traceback_entry.relline,
            dedent=True,
        )

    @pytest.hookimpl
    def pytest_keyboard_interrupt(self, excinfo: ExceptionInfo[KeyboardInterrupt | Exit]) -> None:
        self._keyboard_interrupt_memo = excinfo.getrepr(funcargs=True)
        tryshort_true = excinfo.exconly(tryshort=True)
        tryshort_false = excinfo.exconly(tryshort=False)
        for_later = excinfo.for_later()
        for_later = excinfo.for_later()

        results = TextualizeFactory.hook_msg(
            "pytest_keyboard_interrupt", info=f"[python.builtin]{excinfo.typename}[/]"
        )
        self.console_logger.log(*results, verbosity=Verbosity.QUIET)
        traceback_entry = excinfo.traceback[-1]

        ph = ThemeFactory.path_highlighter()
        path = traceback_entry.path.relative_to(self.config.rootpath)
        link = f"{traceback_entry.path.as_posix()}:{traceback_entry.lineno}"
        if self.isatty:
            link = f"[link={link}]{path.name}:{traceback_entry.lineno}[/link]"
        lines = [
            f"[scope.key_ni]error type:[/] [python.builtin]{excinfo.typename}[/]",
            f"message: {str(excinfo.value)}",
            f"path: {ph(path.as_posix()).markup}",
            f"func: {traceback_entry.name}",
            f"lineno: {traceback_entry.lineno}",
            f"link: {link}",
        ]
        # theme = RichTextualizeSyntaxTheme(),
        text = (
            ConsoleMessage(text="\n".join(lines)).make_section("Exception Information", "  | ").text
        )
        self.console_logger.error(text)
        self.error_console.print(text)
        from rich.syntax import Syntax

        themes = ThemeFactory.syntax_theme()
        syntax = Syntax(
            "".join(traceback_entry.source.raw_lines),
            lexer="python",
            code_width=self.error_console.width - 20,
            line_numbers=True,
            theme=Syntax.get_theme("pycharm_dark"),
            indent_guides=True,
            highlight_lines={traceback_entry.lineno},
            padding=1,
            start_line=traceback_entry.lineno - traceback_entry.relline,
            dedent=True,
        )
        self.console.print(syntax)
        pass
        syntax.stylize_range(
            style="traceback.error_range",
            start=(356, 1),
            end=(358, 11),
        )
        self.console.print(syntax)

        self.console_logger.error(*results, verbosity=Verbosity.QUIET)

        self.error_console.print(*results)

    def report_keyboard_interrupt(self) -> None:
        from rich.text import Text

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

    @pytest.hookimpl
    def pytest_unconfigure(self) -> None:
        if self._keyboard_interrupt_memo is not None:
            self.report_keyboard_interrupt()


def syntax_from_frame_summary(
    theme: SyntaxTheme, fs: FrameSummary, tbe: TracebackEntry, width: int
) -> Syntax:
    # return Syntax(
    #     "".join(tbe.source.raw_lines), lexer="python", code_width=width,
    #     line_numbers=True, theme=theme, indent_guides=True, highlight_lines={fs.lineno}, padding=(0,1),
    #     start_line=fs.lineno - tbe.relline, dedent=True, line_range=(fs.lineno - 3, fs.end_lineno + 3)
    # )
    return Syntax(
        "".join(tbe.source.raw_lines),
        lexer="python",
        theme=theme,
        code_width=width,
        line_numbers=True,
        start_line=fs.lineno - tbe.relline,
        highlight_lines={fs.lineno},
        # line_range=(
        #     1,
        #     4,
        # ),
    )
    # syntax.stylize_range(tbe.lineno - tbe.relline)
