# Project : pytest-textualize
# File Name : settings_tests.py
# Dir Path : tests/plugin_tests/textualize_tests

from __future__ import annotations

import os
from pathlib import Path
from typing import Sized
from typing import TYPE_CHECKING
from typing import TypeVar
from unittest import mock

import pytest
from hamcrest import assert_that
from hamcrest import equal_to

from pytest_textualize import locate

if TYPE_CHECKING:
    from collections.abc import Generator
    from tests.helpers.env import SetEnv

parameterize = pytest.mark.parametrize
SizedT = TypeVar("SizedT", bound=Sized)


@pytest.fixture(autouse=True, scope="function")
def clean_environment() -> Generator[None, None, None]:
    """Cleans the environment variables after each test"""
    with mock.patch.dict(os.environ, clear=True):
        yield


def test_locate_file_not_exists_raise_exception() -> None:
    with pytest.raises(FileNotFoundError):
        locate("not_exists.txt")

    with pytest.raises(FileNotFoundError):
        locate("C:/test/dir1/dir2")


def test_locate(pytestconfig: pytest.Config) -> None:
    pyproject = locate("pyproject.toml")
    expected_path = pytestconfig.rootpath / "pyproject.toml"
    assert_that(pyproject, equal_to(expected_path), "pyproject.toml doesn't exist")


def test_locate_with_start_path(pytestconfig: pytest.Config) -> None:
    pyproject = locate("pyproject.toml", Path.cwd())
    expected_path = pytestconfig.rootpath / "pyproject.toml"

    assert_that(pyproject, equal_to(expected_path), "pyproject.toml doesn't exist")


def test_locate_with_invalid_cwd(pytestconfig: pytest.Config) -> None:
    invalid_cwd = Path("D:/Users/pytest-textualize/src")
    with pytest.raises(FileNotFoundError):
        locate("pyproject.toml", cwd=invalid_cwd)


@parameterize("value", ["1", "0"])
def test_read_force_pytest_color(env: SetEnv, value: str) -> None:
    from pytest_textualize.textualize.settings import TextualizeSettings

    env.set("PY_COLORS", str(value))
    env_value = int(os.getenv("PY_COLORS", None))
    settings = TextualizeSettings()
    assert_that(settings.env.py_colors, equal_to(env_value), reason="force_pytest_colors")
