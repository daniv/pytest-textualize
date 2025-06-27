from __future__ import annotations
from __future__ import annotations

import hashlib
import os
import warnings
from pathlib import Path
from types import ModuleType
from typing import Any
from typing import TYPE_CHECKING
from typing import cast

import pytest
from rich.traceback import PathHighlighter

from pytest_textualize import TS_BASE_PATH
from pytest_textualize import TextualizePlugins
from pytest_textualize import trace_logger
from pytest_textualize.plugin.base import BaseTextualizePlugin
from pytest_textualize.plugin.exceptions import ConsoleMessage
from pytest_textualize.plugin.model import TestCollectionRecord
from pytest_textualize.textualize import hook_msg
from pytest_textualize.textualize import keyval_msg
from pytest_textualize.textualize.verbose_log import Verbosity

if TYPE_CHECKING:
    from rich.console import Console, ConsoleRenderable
    from collections.abc import Iterable
    from pytest_textualize.plugin import TestRunResults
    from pytest_textualize.settings import TextualizeSettings
    from _pytest._code.code import ExceptionRepr
    from pytest_textualize.plugin.model import WarningReport
    from rich.traceback import Frame


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


    def __init__(self, results: TestRunResults):
        self.config: pytest.Config | None = None
        self.settings: TextualizeSettings | None = None
        self.console: Console | None = None
        self.error_console: Console | None = None
        self.results = results
        self.console_logger = trace_logger()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} " f"name='{self.name}'>"

    def render_locals(self, frame: Frame) -> Iterable[ConsoleRenderable]:
        from rich.scope import render_scope
        if frame.locals:
            yield render_scope(
                frame.locals,
                title="locals",
                indent_guides=self.settings.tracebacks.indent_guides,
                max_length=self.settings.tracebacks.locals_max_length,
                max_string=self.settings.tracebacks.locals_max_string,
            )

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        from pytest_textualize.plugin import error_console_key

        super().configure(config)
        setattr(config, "_already_displayed_warnings", [])
        console = self.config.stash[error_console_key]
        self.error_console = self.validate_console(console)


    @pytest.hookimpl
    def pytest_warning_recorded(
        self,
        warning_message: warnings.WarningMessage,
        nodeid: str,
    ) -> None:
        from pytest_textualize.plugin.model import WarningReport

        results = hook_msg("pytest_warning_recorded", info=nodeid)
        self.console_logger.log(*results, verbosity=Verbosity.VERBOSE)
        results = keyval_msg("category", warning_message.category.__name__, value_style="python.builtin")
        self.console_logger.log(*results, verbosity=Verbosity.VERBOSE)

        encoded_string = str(warning_message.message).encode('utf-8')
        hasher = hashlib.sha256()
        hasher.update(encoded_string)
        wr = WarningReport(
            msg_256=hasher.hexdigest(),
            warning_message_lineno=warning_message.lineno,
            warning_message_filename=warning_message.filename,
            category=warning_message.category,
            nodeid=nodeid,
            messages=str(warning_message.message).splitlines()
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

        try:
            results = hook_msg("pytest_internalerror", info=f"[python.builtin]{excinfo.typename}[/]")
            self.console_logger.log(*results, verbosity=Verbosity.QUIET)
            self.console.line()
            self.console.rule(title="[#C5172E]INTERNAL ERROR[/]", style="bright_red", characters="=")
            suppress_modules = suppress([pluggy, _pytest])
            path = PathHighlighter()(Path(excrepr.reprcrash.path).relative_to(TS_BASE_PATH).as_posix()).markup
            messages = [
                f"message: {excrepr.reprcrash.message}",
                f"path: {path}",
                f"lineno: {excrepr.reprcrash.lineno}",
            ]
            text = ConsoleMessage(text="\n".join(messages)).make_section("▪ Crash Information", indent="   | ").text
            self.error_console.print(text)
            if self.isatty:
                self.error_console.print(
                    f" click -> [link={excrepr.reprcrash.path}:{excrepr.reprcrash.lineno}]"
                    f"{Path(excrepr.reprcrash.path).name}:{excrepr.reprcrash.lineno}[/link]"
                )
            else:
                self.error_console.print(f" {Path(excrepr.reprcrash.path).as_posix()}:{excrepr.reprcrash.lineno}")
            self.console.line()
            for entry in excrepr.reprtraceback.reprentries:
                for line in entry.lines:
                    if list(filter(lambda c: line.find(c) > 0, suppress_modules)):
                        self.console_logger.error("INTERNALERROR>", line.splitlines()[0])
                    else:
                        self.console_logger.error("INTERNALERROR>", line[:-1])
            self.console.rule(title="[#C5172E]END INTERNAL ERROR[/]", style="bright_red", characters="=")
        except (SyntaxError | Exception) as exc:
            return False
        return True

    @pytest.hookimpl
    def pytest_exception_interact(
            self,
            node: pytest.Item | pytest.Collector,
            call: pytest.CallInfo[Any],
            report: pytest.CollectReport | pytest.TestReport
    ) -> None:
        results = hook_msg("pytest_exception_interact", info=f"[python.builtin]{call.excinfo.typename}[/]")
        self.console_logger.log(*results, verbosity=Verbosity.QUIET)
        if isinstance(report, pytest.CollectReport):
            if node.nodeid in self.results.collect.errors:
                pass
            else:
                record = TestCollectionRecord.create_error_model(when=report.when, nodeid=node.nodeid)
                record.collect_report = report
                messages = []
                msg = ConsoleMessage(debug=True,
                                     text=f"The error occurred on stage '{report.when}'.\n"
                                          f"[scope.key_ni]nodeid:[/] {node.nodeid}\n"
                                          f"[scope.key_ni]name:[/] {node.name}\n"
                                          "The exception was caught on [pyest.hook.tag]hook: "
                                          "[/][pyest.hook.name]pytest_exception_interact[/].\n"
                                     ).make_section("Causes", "    | ").text
                messages.append(msg)
                exc = cast(BaseException, call.excinfo.value)
                from pytest_textualize.plugin import TextualizeRuntimeError
                error = TextualizeRuntimeError.create(reason="Error collecting module", exception=exc, info=messages)
                record.runtime_error = error

                self.results.collect.errors[report.head_line] = record
