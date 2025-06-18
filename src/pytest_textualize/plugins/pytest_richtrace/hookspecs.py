# Project : pytest-textualize
# File Name : hookspecs.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

import pytest

from pytest_textualize import TextualizeSettings

if TYPE_CHECKING:
    from rich.console import Console


@pytest.hookspec(historic=True)
def pytest_console_and_settings(
    console: Console, error_console: Console, settings: TextualizeSettings
) -> None:
    """Provides the framework settings and the rich console,

    :param error_console: and sys.stderr console
    :param console: The rich.Console instance
    :param settings: The configuration settings
    :return: a dictionary with the information collected
    """


@pytest.hookspec
def pytest_collect_env_info(config: pytest.Config) -> dict[str, Any]:
    """Collects environment information for the header,

    :param config: The pytest config
    :return: a dictionary with the information collected
    """
    pass
