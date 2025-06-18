# Project : pytest-textualize
# File Name : __init__.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from rich.console import Console


console_key = pytest.StashKey[Console]()
error_console_key = pytest.StashKey[Console]()
