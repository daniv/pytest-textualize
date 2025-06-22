# Project : pytest-textualize
# File Name : tiemr.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

import time

from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from pytest_textualize.plugins import TestRunResults


class TextualizeExecutionTimer:
    name: str = "pytest-textualize-timer"
    test_run_results: TestRunResults

    def __init__(self, results: TestRunResults) -> None:
        self.test_run_results = results

    # https://docs.pytest.org/en/stable/reference.html#initialization-hooks
    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_sessionstart(self):
        start = time.perf_counter()
        yield
        end = time.perf_counter()
        self.test_run_results.durations["pytest_sessionstart"] = end - start

    # https://docs.pytest.org/en/stable/reference.html#collection-hooks
    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_collection(self):
        start = time.perf_counter()
        yield
        end = time.perf_counter()
        self.test_run_results.durations["pytest_collection"] = end - start

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_collect_file(self, file_path: Path) -> Generator[None, Any, None]:
        start = time.perf_counter()
        yield
        end = time.time()
        self.test_run_results.durations[f"pytest_collect_file:{file_path.name}"] = end - start

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"durations={self.test_run_results.durations!r}>"
        )
