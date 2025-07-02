# pioneer
from __future__ import annotations


__all__ = (
    "console_key",
    "error_console_key",
    "settings_key",
)

import pytest
from rich.console import Console
from pytest_textualize.settings import TextualizeSettings

console_key = pytest.StashKey[Console]()
error_console_key = pytest.StashKey[Console]()
settings_key = pytest.StashKey[TextualizeSettings]()
