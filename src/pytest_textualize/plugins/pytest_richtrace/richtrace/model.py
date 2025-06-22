# Project : pytest-textualize
# File Name : model.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

from enum import StrEnum
from typing import Self
from typing import Type
from typing import TypeVar

from pendulum import Interval
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from pydantic import field_serializer
from pydantic import model_validator
from pydantic_extra_types.pendulum_dt import DateTime
from rich.repr import auto

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

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        # if self.start is None:
        #     raise ValueError('Passwords do not match')
        return self

    @computed_field(alias="timezone name", repr=False)
    @property
    def timezone_name(self) -> str:
        if self.start is None:
            return "Unknown"
        return self.start.timezone_name

    @computed_field(alias="datetime interval", repr=False)
    @property
    def interval_dt(self) -> Interval | None:
        if self.start is None or self.finish is None:
            return None
        return Interval(self.start, self.end)

    @computed_field(alias="precise interval", repr=False)
    def interval_precise(self) -> float:
        if self.precise_finish is None:
            return 0.0
        return self.precise_finish - self.precise_start

    @property
    def start_to_datetime_string(self) -> str:
        if self.start is None:
            return ""
        return self.start.to_datetime_string()

    @property
    def start_to_date_string(self) -> str:
        if self.start is None:
            return ""
        return self.start.to_date_string()

    @property
    def start_to_day_datetime_string(self) -> str:
        if self.start is None:
            return ""
        return self.start.to_day_datetime_string()

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


@auto
class TestCollectionRecord(Timings):
    count: int = 0
    error: dict[ModuleId, BaseException] = Field(default_factory=dict)
    files_collected: int = 0
    directories_collected: int = 0
    ignored_collected: int = 0
    skip: dict[NodeId, list[SkipInfo]] = Field(default_factory=dict)
    xfail: dict[NodeId, list[XfailInfo]] = Field(default_factory=dict)
    deselected: list[NodeId] = Field(default_factory=list)

    @property
    def errors_count(self) -> int:
        return len(self.error)

    def __rich_repr__(self):
        yield "error", self.error
        yield "skip", self.skip
        yield "xfail", self.xfail
        if self.deselected:
            yield "deselected", self.deselected

    @field_serializer("error")
    def serialize_exception(
            self, exc_info: dict[ModuleId, BaseException], _info
    ) -> dict[ModuleId, str]:
        def format_exc(exc: BaseException) -> str:
            import traceback
            return "".join(traceback.format_exception_only(type(exc), exc)).rstrip("\n")

        return {k: format_exc(exc) for k, exc in exc_info.items()}


class TestRunResults(Timings):
    durations: dict[str, float] = Field(default_factory=dict)
    collect: TestCollectionRecord = Field(default_factory=TestCollectionRecord)
