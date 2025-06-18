# Project : pytest-textualize
# File Name : tests_textwrapp.py
# Dir Path : tests/setup_tests

from __future__ import annotations

from typing import Sized
from typing import TYPE_CHECKING
from typing import TypeVar

import pytest

if TYPE_CHECKING:
    pass

parameterize = pytest.mark.parametrize
SizedT = TypeVar("SizedT", bound=Sized)


def test_template() -> None:
    pass
