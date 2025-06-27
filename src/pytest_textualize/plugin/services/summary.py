from __future__ import annotations


from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING
from typing import cast

import pytest
from pydantic import BaseModel
from rich.columns import Columns
from rich.console import Group
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.scope import render_scope
from rich.text import Text
from rich_argparse_plus.themes import style
from rich import box

from pytest_textualize.textualize.verbose_log import Verbosity
from pytest_textualize.textualize import hook_msg
from pytest_textualize import TextualizePlugins
from pytest_textualize.settings import TextualizeSettings
from pytest_textualize.plugin import TestRunResults
from rich.console import Console

if TYPE_CHECKING:
    from argparse import Namespace
    from pytest_textualize.plugin.model import WarningReport
    from collections.abc import Generator
    from _pytest.reports import BaseReport
    from collections.abc import Callable
    from pytest_textualize.plugin import TestRunResults


class SummaryService:
    name = TextualizePlugins.SUMMARY_SERVICE

    def __init__(self) -> None:
        self.settings: TextualizeSettings | None = None
        self.console: Console | None = None
        self.results: TestRunResults | None = None
        self.report_chars: str | None = None
        self.options: Namespace | None = None

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}'>"
        )

    @property
    def showcapture(self) -> bool:
        return self.options.showcapture

    def has_opt(self, char: str) -> bool:
        char = {"xfailed": "x", "skipped": "s"}.get(char, char)
        return char in self.report_chars

    @pytest.hookimpl
    def pytest_stats_summary(self, config: pytest.Config, terminalreporter: pytest.TerminalReporter) -> None:
        if self.settings is None:
            self.settings = cast(TextualizeSettings, getattr(terminalreporter, "settings"))
            self.results = cast(TestRunResults, getattr(terminalreporter, "results"))
            self.console = cast(Console, getattr(terminalreporter, "console"))
            self.options = config.option
        if self.settings.verbosity < Verbosity.NORMAL:
            return None
        parts = _build_summary_stats_line(config.option.collectonly, self.results)
        msg = ", ".join(parts)
        if self.results.interval_precise < 60.0:
            fmt = "{:.2f} s".format(self.results.interval_precise)
        else:
            fmt = self.results.interval_dt.in_seconds()

        duration = f" in {fmt}"
        msg += duration
        self.console.rule(msg, characters="=", style="#68D2E8")
        return None

    @pytest.hookimpl(wrapper=True)
    def pytest_terminal_summary(
            self,
            terminalreporter: pytest.TerminalReporter,
            exitstatus: pytest.ExitCode,
            config: pytest.Config
    ) ->  Generator[None]:
        from _pytest.terminal import getreportopt

        self.report_chars = getreportopt(config)
        assert hasattr(terminalreporter, "results")
        assert hasattr(terminalreporter, "console")
        assert hasattr(terminalreporter, "settings")

        self.settings = cast(TextualizeSettings, getattr(terminalreporter, "settings"))
        self.results = cast(TestRunResults, getattr(terminalreporter, "results"))
        self.console = cast(Console, getattr(terminalreporter, "console"))

        from pytest_textualize.textualize.verbose_log import Verbosity
        if self.settings.verbosity > Verbosity.NORMAL:
            hook_msg("pytest_terminal_summary", info=str(exitstatus))

        summary_errors(config, self.results, self.console)
        summary_failures()
        summary_xfailures()
        summary_warnings(config, self.has_opt, self.results.warnings, self.console)
        summary_passes()
        summary_xpasses()
        try:
            return (yield)
        finally:
            short_test_summary()
            summary_warnings(config, self.has_opt, self.results.warnings, self.console)

def summary_errors(config: pytest.Config, results: TestRunResults, console: Console) -> None:
    if config.option.tbstyle != "no":
        reports: list[BaseReport] = results.collect.errors
        if not reports:
            return

        console.rule("[#FFCDB2]ERRORS[/]", characters="=", style="#E5989B")
        console.line(1)
        columns = Columns()
        for name, rep in results.collect.errors.items():
            group = Group(fit=True)
            if rep.when == "collect":
                msg = "ERROR collecting " + name
            else:
                msg = f"ERROR at {rep.when} of {name}"
            title = f"[#FF0000]{msg}[/]"
            group.renderables.append(rep.runtime_error.render(verbose=Verbosity.NORMAL))
            showcapture = config.option.showcapture
            if showcapture == "no":
                columns.add_renderable(Panel(group))
                return
            for sec_name, content in rep.collect_report.sections:
                if showcapture != "all" and showcapture not in sec_name:
                    continue
                group.renderables.append(Rule(str(sec_name), characters="-"))
                if content[-1:] == "\n":
                    content = content[:-1]
                group.renderables.append(content)
            columns.add_renderable(Panel(group, title=title, padding=1, box=box.DOUBLE_EDGE, border_style="white", width=110))
        console.print(Padding(columns, pad=(0, 0, 0, 2), style="bright_red"))
        console.line(2)
        pass


def summary_failures():
    pass


def summary_xfailures():
    pass


def summary_warnings(config: pytest.Config, has_opt: Callable[[str], bool], warns: list[WarningReport], console: Console) -> None:
    if has_opt("w"):
        all_warnings: list[WarningReport] | None = warns
        if not all_warnings:
            return None
        _already_displayed_warnings = getattr(config, "_already_displayed_warnings", None)
        final = len(_already_displayed_warnings) > 0
        if final:
            warning_reports = all_warnings[len(_already_displayed_warnings):]
        else:
            warning_reports = all_warnings
        setattr(config, "_already_displayed_warnings", list(map(lambda x: x.msg_256, warning_reports)))
        if not warning_reports:
            return None

        reports_grouped_by_message: dict[str, list[WarningReport]] = {}
        for wr in warning_reports:
            reports_grouped_by_message.setdefault(wr.msg_256, []).append(wr)

        title = "[#FF9800]warnings summary [dim](final)[/][/]" if final else "[#FF9800]warnings summary[/]"
        console.rule(title, characters="=", style="yellow")
        for hashed, message_reports in reports_grouped_by_message.items():
            category = message_reports[0].category
            model = cast(BaseModel, message_reports[0]).model_dump(exclude={"msg_256", "category"})
            scope = render_scope(model, title=f"[#FF9800]{category}[/]")
            console.print(Padding(scope, (0, 0, 0, 1), expand=False), style="#FF9800")
        console.print(
            " -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n"
        )
    return None


def summary_passes():
    pass


def summary_xpasses():
    pass


def short_test_summary():
    pass


def _build_summary_stats_line(collectonly: bool, results: TestRunResults) -> list[str]:
    if collectonly:
        return _build_collect_only_summary_stats_line(results)
    else:
        return _build_normal_summary_stats_line()


def _build_collect_only_summary_stats_line(results: TestRunResults) -> list[str]:
    deselected = results.collect.stats.total_deselected
    errors = results.collect.stats.total_errors
    collected = results.collect.stats.total_collected
    selected = results.collect.stats.selected

    parts: list[str] = []
    from boltons.strutils import cardinalize

    if collected == 0:
        parts.append("[#FFCF50]no tests collected[/]")
    elif deselected == 0:
        collected_output = f"[#A4B465]{collected} {cardinalize("test", collected)} collected[/]"
        parts.append(collected_output)
    else:
        all_tests_were_deselected = collected == deselected
        if all_tests_were_deselected:
            collected_output = f"[#FFCF50]no tests collected ({deselected} deselected)[/]"
        else:
            collected_output = f"[#A4B465]{selected}/{collected} tests collected ({deselected} deselected)[/]"

        parts.append(collected_output)

    if errors:
        parts.append(f"[#FF0000]{errors} {cardinalize("error", errors)}[/]")

    return parts


def _build_normal_summary_stats_line() -> list[str]:
    pass
