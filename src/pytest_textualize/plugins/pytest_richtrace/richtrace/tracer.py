# Project : pytest-textualize
# File Name : manager.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import pytest

from pytest_textualize.textualize import Verbosity

if TYPE_CHECKING:
    from pytest_textualize.plugins import TestRunResults
    from pytest_textualize.settings import TextualizeSettings
    from rich.console import Console


class PytestRichTracer:
    name: str = "pytest-rich-tracer"

    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.console: Console | None = None
        self._lock = threading.Lock()
        self.settings: TextualizeSettings | None = None
        self.test_results: TestRunResults | None = None
        self._start_time: str | None = None

    @property
    def verbosity(self) -> Verbosity:
        return self.settings.verbosity

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"verbosity={self.verbosity!r} "
            f"started={getattr(self, "_start_time", "<UNSET>")}>"
        )
