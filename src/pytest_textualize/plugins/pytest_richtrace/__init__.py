# Project : pytest-textualize
# File Name : __init__.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

import pytest
from rich.console import Console

from pytest_textualize.settings import TextualizeSettings

console_key = pytest.StashKey[Console]()
error_console_key = pytest.StashKey[Console]()
settings_key = pytest.StashKey[TextualizeSettings]()
