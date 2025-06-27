# Project : pytest-textualize
# File Name : model.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import ClassVar
from typing import Self
from typing import Type
from typing import TypeVar

import pytest
from _pytest.pathlib import absolutepath
from _pytest.pathlib import bestrelpath
from pendulum import Interval
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from pydantic import field_serializer
from pydantic import model_validator
from pydantic_extra_types.pendulum_dt import DateTime
from rich.repr import auto
from pytest import CollectReport
from rich.traceback import Traceback

from pytest_textualize.plugin.exceptions import TextualizeRuntimeError

Marker = str
PerfTime = float
NodeId = str
ModuleId = str
ItemId = NodeId | ModuleId
E = TypeVar("E", bound=BaseException, covariant=True)


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

    msg_256: str
    messages: list[str] = Field(default_factory=list, description="User friendly messages about the warning.")
    nodeid: str | None = Field(default=None, description="File system location of the source of the warning.")
    category: Type[Warning] = Field(default=None, description="File system category of the source of the warning.")
    warning_message_filename: str | None = Field(default=None, description="File system location of the warning.")
    warning_message_lineno: int | None = Field(default=None, description="File system location lineno of the warning.")
    count_towards_summary: ClassVar[bool] = True


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


class Error(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    when: str
    nodeid: str
    exception: BaseException | None = Field(default=None, alias="exception")
    collect_report: pytest.CollectReport | None = None
    test_report: pytest.TestReport | None = None
    runtime_error: TextualizeRuntimeError | None = Field(default=None)
    traceback: Traceback | None = Field(default=None)
    # exception_info: pytest.ExceptionInfo | None = Field(default=None)


@auto
class TestCollectionRecord(Timings):
    errors: dict[ModuleId, Error] = Field(default_factory=dict)
    skip: dict[NodeId, list[SkipInfo]] = Field(default_factory=dict)
    skip_reports: dict[NodeId, CollectReport] = Field(default_factory=dict)

    xfail: dict[NodeId, list[XfailInfo]] = Field(default_factory=dict)
    # deselected: list[NodeId] = Field(default_factory=list)
    stats: CollectStats = Field(default_factory=CollectStats)

    @classmethod
    def create_error_model(
            cls, when: str, nodeid: str) -> Error:
        return Error(when=when, nodeid=nodeid)

    @property
    def errors_count(self) -> int:
        return len(self.errors.keys())

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
