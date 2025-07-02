from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pytest_textualize.model import PerfTime
    from pytest_textualize.typist import DictStrAny
    from pytest_textualize.typist import WarningReportType
    from pytest_textualize.typist import TestRunResultsType
    from pendulum import DateTime


class ModelFactory:
    @staticmethod
    def test_run_results(precise_start: PerfTime, start: DateTime) -> TestRunResultsType:
        from pytest_textualize.model import TestRunResults

        return TestRunResults(precise_start=precise_start, start=start)

    @staticmethod
    def warning(data: DictStrAny) -> WarningReportType:
        from pytest_textualize.model import WarningReport

        return WarningReport(**data)

    #
    # @staticmethod
    # def create_error_model(data: DictStrAny) -> Error:
    #     from pytest_textualize.model import Error
    #     return Error(**data)
