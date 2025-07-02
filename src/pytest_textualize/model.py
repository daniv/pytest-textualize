from __future__ import annotations

import sys
from enum import StrEnum
from pathlib import Path
from typing import ClassVar
from typing import ParamSpec
from typing import TYPE_CHECKING
from typing import Type
from typing import TypeVar

import pytest
from pendulum import Interval
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from pydantic import field_serializer
from pydantic_extra_types.pendulum_dt import DateTime
from pytest import CollectReport
from rich.console import ConsoleRenderable
from rich.console import Group
from rich.panel import Panel
from rich.repr import auto
from rich.syntax import Syntax
from rich.text import Text

from pytest_textualize import Textualize

if TYPE_CHECKING:
    from collections.abc import Iterable
    from rich.console import RenderableType
    from pytest_textualize.typist import PanelType
    from rich.console import Console


Marker = str
PerfTime = float
NodeId = str
ModuleId = str
ItemId = NodeId | ModuleId
E = TypeVar("E", bound=BaseException, covariant=True)
P = ParamSpec("P")


class TestStage(StrEnum):
    Collect = "collect"
    Setup = "setup"
    Call = "call"
    Teardown = "teardown"


class TestResult(StrEnum):
    Error = "error"
    Passed = "passed"
    Failed = "failed"
    Skipped = "skipped"
    XFailed = "xfailed"
    XPassed = "xpassed"
    Deselected = "deselected"
    Unknown = "unknown"


class SkipInfo(BaseModel):
    reason: str
    markers: list[Marker] = Field(default_factory=list)


RaisesType = Type[BaseException] | tuple[Type[BaseException], ...]


class XfailInfo(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    reason: str
    raises: RaisesType | None
    run: bool
    strict: bool
    markers: list[Marker] = Field(default_factory=list)

    @field_serializer("raises")
    def serialize_exception(self, exc: RaisesType | None, _info) -> str:
        if exc is None:
            return ""

        if isinstance(exc, tuple):
            excs = exc
        else:
            excs = (exc,)

        return ", ".join([str(exc.__name__) for exc in excs])


class WarningReport(BaseModel):
    """Simple structure to hold warnings information captured by ``pytest_warning_recorded``."""

    msg_256: str = Field(exclude=True)
    messages: list[str] = Field(
        default_factory=list,
        description="User friendly messages about the warning.",
        title="Messages",
    )
    nodeid: str | None = Field(
        default=None,
        description="The pytest nodeid on the warning",
        alias="nodeid",
        title="Node Id",
    )
    category: Type[Warning] = Field(
        default=None,
        description="Category of the source of the warning.",
        exclude=True,
        title="Category Description",
    )
    filename: str | None = Field(
        default=None, description="File system file location of the warning.", title="File Path"
    )
    lineno: int | None = Field(
        default=None, description="File system lineno of the warning.", title="Line #"
    )
    count_towards_summary: ClassVar[bool] = Field(
        default=True,
        description="Whether the warning should be counted as a summary of the warning.",
        exclude=True,
    )

    def render(self, console: Console) -> None:
        from rich.table import Table
        from rich.pretty import Pretty

        repr_h = Textualize.theme_factory().repr_highlighter()
        path_h = Textualize.theme_factory().path_highlighter()

        items: list[ConsoleRenderable] = []
        if hasattr(self.category, "__doc__"):
            items.append(
                Panel(
                    Text(f"{self.category.__doc__}", "#48abb1", justify="center"),
                    border_style="#E3835B",
                )
            )
        items_table = Table.grid(padding=(0, 1), expand=False)
        items_table.add_column(justify="right")
        for key, field_info in self.model_fields.items():
            highlighter = repr_h
            if field_info.exclude:
                continue
            value = getattr(self, key)
            if key == "filename":
                value = Path(self.filename).as_posix()
                highlighter = path_h
            items_table.add_row(
                f"[inspect.attr]{field_info.title}[/] [inspect.equals] =[/]",
                Pretty(value, highlighter=highlighter),
            )
        if sys.stdout.isatty():
            items_table.add_row(
                f"[inspect.attr]link[/] [inspect.equals] =[/]",
                f"[bright_blue][link={self.filename}:{self.lineno}]{Path(self.filename).name}:{self.lineno}[/link] ⮄ click[/]",
            )
        items.append(items_table)

        p = Panel.fit(
            Group(*items),
            title=f"[#B75742]Warning Report for [/][python.builtin]{self.category.__name__}[/]",
            border_style="#9d4a39",
            padding=(0, 1),
        )
        console.print(p)

    def _render(self) -> Iterable[RenderableType]:
        pass

        #
        # if hasattr(self.category, "__doc__"):
        #     key_text = Text.assemble((self.category.__doc__, "inspect.help",))
        #     # yield Panel(
        #     #     Pretty(key_text, highlighter=repr_h),
        #     #     border_style="inspect.value.border",
        #     # )
        #     yield Panel(
        #         key_text,
        #         border_style="inspect.value.border",
        #     )
        #
        # items_table = Table.grid(padding=(0, 1), expand=False)
        # items_table.add_column(justify="right")
        #
        # for key, field_info in self.model_fields.items():
        #     if field_info.exclude:
        #         continue
        #     value = safe_getattr(self, key)
        #     highlighter = repr_h
        #     if key == "filename":
        #         value = Path(self.filename).relative_to(TS_BASE_PATH).as_posix()
        #         highlighter = path_h
        #
        #     key_text = Text.assemble(
        #         (field_info.title, "inspect.attr", ),
        #         (" =", "inspect.equals"),
        #     )
        #     items_table.add_row(key_text, Pretty(value, highlighter=highlighter))
        # yield items_table


@auto
class Timings(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        validate_default=True,
        validation_error_cause=True,
        extra="forbid",
    )
    start: DateTime | None = None
    finish: DateTime | None = None
    precise_start: PerfTime = 0.0
    precise_finish: PerfTime = 0.0

    @property
    def timezone_name(self) -> str:
        if self.start is None:
            return "Unknown"
        return self.start.timezone_name

    @property
    def interval_dt(self) -> Interval | None:
        if self.start is None or self.finish is None:
            return None
        return Interval(self.start, self.finish)

    @property
    def interval_precise(self) -> float:
        if self.precise_finish is None:
            return 0.0
        return self.precise_finish - self.precise_start

    @computed_field(alias="timezone name", repr=False)
    @property
    def start_to_datetime_string(self) -> str:
        if self.start is None:
            return ""
        return self.start.to_datetime_string()

    @computed_field(alias="timezone name", repr=False)
    @property
    def start_to_date_string(self) -> str:
        if self.start is None:
            return ""
        return self.start.to_date_string()

    @computed_field(alias="timezone name", repr=False)
    @property
    def start_to_day_datetime_string(self) -> str:
        if self.start is None:
            return ""
        return self.start.to_day_datetime_string()

    @computed_field(alias="timezone name", repr=False)
    @property
    def start_to_time_string(self) -> str:
        if self.start is None:
            return ""
        return self.start.to_time_string()

    @property
    def finish_to_datetime_string(self) -> str:
        if self.finish is None:
            return ""
        return self.start.to_datetime_string()

    @property
    def finish_to_date_string(self) -> str:
        if self.finish is None:
            return ""
        return self.start.to_date_string()

    @property
    def finish_to_day_datetime_string(self) -> str:
        if self.finish is None:
            return ""
        return self.start.to_day_datetime_string()

    @property
    def finish_to_time_string(self) -> str:
        if self.finish is None:
            return ""
        return self.start.to_time_string()


class CollectStats(BaseModel):
    total_errors: int = Field(default=0, alias="errors")
    total_skipped: int = Field(default=0, alias="skipped")
    total_xfailed: int = Field(default=0, alias="xfailed")
    total_deselected: int = Field(default=0, alias="deselected")
    total_collected: int = Field(default=0, alias="collected")
    total_ignored_collected: int = Field(default=0, alias="ignored")

    @property
    def selected(self) -> int:
        # sub_total = sum([self.total_deselected, self.total_skipped, self.total_xfailed, self.total_errors])
        return self.total_collected - self.total_deselected

    def __rich_repr__(self):
        yield "errors", self.total_errors
        yield "skipped", self.total_skipped
        yield "xfailed", self.total_xfailed
        yield "deselected", self.total_deselected
        yield "collected", self.total_collected
        yield "ignored", self.total_ignored_collected
        yield "selected", self.selected


class ErrorInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    exception: BaseException = Field(alias="exception")
    collect_report: pytest.CollectReport = Field(alias="report")
    rich_report: Panel
    error_syntax: Syntax = Field(alias="syntax")


@auto
class TestCollectionRecord(Timings):
    errors: dict[ModuleId, ErrorInfo] = Field(default_factory=dict)
    skip: dict[NodeId, list[SkipInfo]] = Field(default_factory=dict)
    skip_reports: dict[NodeId, CollectReport] = Field(default_factory=dict)

    xfail: dict[NodeId, list[XfailInfo]] = Field(default_factory=dict)
    stats: CollectStats = Field(default_factory=CollectStats)

    @property
    def errors_count(self) -> int:
        return len(self.errors.keys())

    def register_error(
        self,
        nodeid: str,
        exception: BaseException,
        pytest_report: pytest.CollectReport,
        rich_report: PanelType,
        syntax: Syntax,
    ) -> None:
        self.errors[nodeid] = ErrorInfo(
            exception=exception, report=pytest_report, rich_report=rich_report, syntax=syntax
        )

    # @field_serializer("errors")
    # def serialize_exception(
    #     self, error: dict[ModuleId, Error], _info
    # ) -> dict[ModuleId, str]:
    #     def format_exc(exc: BaseException) -> str:
    #         import traceback
    #
    #         return "".join(traceback.format_exception_only(type(exc), exc)).rstrip("\n")
    #
    #     return {k: format_exc(exc) for k, exc in exc_info.items()}


class TestRunResults(Timings):
    collect: TestCollectionRecord | None = Field(default=None)
    warnings: list[WarningReport] = Field(default_factory=list)

    def create_collect(self, precise_start: PerfTime, start: DateTime) -> TestCollectionRecord:
        self.collect = TestCollectionRecord(precise_start=precise_start, start=start)
        return self.collect
