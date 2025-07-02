from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

import pytest
from _pytest.reports import BaseReport
from pydantic import BaseModel
from rich.padding import Padding
from rich.scope import render_scope

from pytest_textualize import Textualize
from pytest_textualize import TextualizePlugins
from pytest_textualize import Verbosity
from pytest_textualize.plugin.base import BaseTextualizePlugin


if TYPE_CHECKING:
    from rich.console import Console
    from collections.abc import Generator
    from collections.abc import Callable
    from pytest_textualize.typist import TestRunResultsType
    from pytest_textualize.typist import WarningReportType


class SummaryService(BaseTextualizePlugin):
    name = TextualizePlugins.SUMMARY_SERVICE

    def __init__(self) -> None:
        self.results: TestRunResultsType | None = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} " f"name='{self.name}'>"

    @pytest.hookimpl(tryfirst=True)
    def pytest_configure(self, config: pytest.Config) -> None:
        super().configure(config)

    @pytest.hookimpl
    def pytest_stats_summary(
        self, config: pytest.Config, terminalreporter: pytest.TerminalReporter
    ) -> None:
        self.results = getattr(terminalreporter, "results")
        if self.verbosity < Verbosity.NORMAL:
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
        config: pytest.Config,
    ) -> Generator[None]:
        self.results = getattr(terminalreporter, "results")

        hook, info, level = Textualize.hook_msg("pytest_terminal_summary", info=str(exitstatus))
        self.verbose_logger.log(hook, info, level_text=level, verbosity=Verbosity.VERBOSE)

        self.verbose_logger.debug("summarizing errors ...")
        summary_errors(config, self.results, self.console)
        self.verbose_logger.debug("summarizing failures ...")
        summary_failures()
        summary_xfailures()
        self.verbose_logger.debug("summarizing warnings not final")
        summary_warnings(config, self.has_opt, self.results.warnings, self.console)
        self.verbose_logger.debug("summarizing passes ...")
        summary_passes()
        self.verbose_logger.debug("summarizing [pytest.xpassed]xpasses[/]")
        summary_xpasses()
        try:
            return (yield)
        finally:
            short_test_summary()
            summary_warnings(config, self.has_opt, self.results.warnings, self.console)


def summary_errors(config: pytest.Config, results: TestRunResultsType, console: Console) -> None:
    if config.option.tbstyle != "no":
        reports: list[BaseReport] = results.collect.errors
        if not reports:
            return None

        console.rule("[#FF5151]ERRORS SUMMARY[/]", characters="=", style="pytest.outcome.error")
        for name, err_info in results.collect.errors.items():
            if err_info.report.when == "collect":
                msg = "ERROR collecting " + name
            else:
                msg = f"ERROR at {err_info.when} of {name}"
            console.rule(f"[#FF5151]{msg}[/]", characters="_", style="pytest.outcome.error")
            console.print(err_info.rich_report)
            # todo: should traceback print?
            if config.option.showcapture == "no":
                return None
            for section_name, content in err_info.collect_report.sections:
                if (
                    config.option.showcapture != "all"
                    and config.option.showcapture not in section_name
                ):
                    continue
                console.rule(
                    f"[#FF5151]section_name[/]", characters="-", style="pytest.outcome.error"
                )
                if content[-1:] == "\n":
                    content = content[:-1]
                console.print(content)
            else:
                return None
        else:
            return None
    return None


def summary_failures():
    pass


def summary_xfailures():
    pass


def summary_warnings(
    config: pytest.Config,
    has_opt: Callable[[str], bool],
    warns: list[WarningReportType],
    console: Console,
) -> None:
    if has_opt("w"):
        all_warnings: list[WarningReportType] | None = warns
        if not all_warnings:
            return None
        _already_displayed_warnings = getattr(config, "_already_displayed_warnings", None)
        final = len(_already_displayed_warnings) > 0
        if final:
            warning_reports = all_warnings[len(_already_displayed_warnings) :]
        else:
            warning_reports = all_warnings
        setattr(
            config, "_already_displayed_warnings", list(map(lambda x: x.msg_256, warning_reports))
        )
        if not warning_reports:
            return None

        reports_grouped_by_message: dict[str, list[WarningReportType]] = {}
        for wr in warning_reports:
            reports_grouped_by_message.setdefault(wr.msg_256, []).append(wr)

        title = (
            "[#ffe0b1]WARNINGS SUMMARY [dim](final)[/][/]"
            if final
            else "[#ffe0b1]WARNINGS SUMMARY[/]"
        )
        console.rule(title, characters="=", style="pytest.outcome.warnings")
        for hashed, message_reports in reports_grouped_by_message.items():
            category = message_reports[0].category
            model = cast(BaseModel, message_reports[0]).model_dump(exclude={"msg_256", "category"})
            scope = render_scope(model, title=f"[#ffe0b1]{category}[/]")
            console.print(
                Padding(scope, (0, 0, 0, 1), expand=False), style="pytest.outcome.warnings"
            )
        console.print(" -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n")
    return None


def summary_passes():
    pass


def summary_xpasses():
    pass


def short_test_summary():
    pass


def _build_summary_stats_line(collectonly: bool, results: TestRunResultsType) -> list[str]:
    if collectonly:
        return _build_collect_only_summary_stats_line(results)
    else:
        return _build_normal_summary_stats_line()


def _build_collect_only_summary_stats_line(results: TestRunResultsType) -> list[str]:
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
            collected_output = (
                f"[#A4B465]{selected}/{collected} tests collected ({deselected} deselected)[/]"
            )

        parts.append(collected_output)

    if errors:
        parts.append(f"[#FF0000]{errors} {cardinalize("error", errors)}[/]")

    return parts


def _build_normal_summary_stats_line() -> list[str]:
    pass
