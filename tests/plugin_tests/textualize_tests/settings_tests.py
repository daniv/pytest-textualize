# Project : pytest-textualize
# File Name : settings_tests.py
# Dir Path : tests/plugin_tests/textualize_tests

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from hamcrest import assert_that
from hamcrest import equal_to
from hamcrest import has_key
from hamcrest import has_length
from hamcrest import not_
from rich.traceback import Traceback

from pytest_textualize import TextualizeSettings
from pytest_textualize.settings import ConsoleSettings
from pytest_textualize.settings import TracebacksSettingsModel
from pytest_textualize.textualize import locate

if TYPE_CHECKING:
    from collections.abc import Generator
    from tests.helpers.env import SetEnv
    from rich.console import Console

parameterize = pytest.mark.parametrize


class NoPostInitConsoleSettings(ConsoleSettings):
    def model_post_init(self, context: Any, /) -> None:
        pass


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
    from pytest_textualize.settings import TextualizeSettings

    env.set("PY_COLORS", str(value))
    env_value = int(os.getenv("PY_COLORS", ""))
    settings = TextualizeSettings()
    assert_that(settings.env.py_colors, equal_to(env_value), reason="force_pytest_colors")


def test_console_settings_properties() -> None:
    settings = NoPostInitConsoleSettings()
    dump = settings.model_dump()
    assert_that(dump, has_key("color_system"), reason="color_system")
    assert_that(dump, has_key("force_terminal"), reason="force_terminal")
    assert_that(dump, has_key("force_jupyter"), reason="force_jupyter")
    assert_that(dump, has_key("force_interactive"), reason="force_interactive")
    assert_that(dump, has_key("soft_wrap"), reason="soft_wrap")
    assert_that(dump, has_key("no_color"), reason="no_color")
    assert_that(dump, has_key("markup"), reason="markup")
    assert_that(dump, has_key("emoji"), reason="emoji")
    assert_that(dump, has_key("emoji_variant"), reason="emoji_variant")
    assert_that(dump, has_key("highlight"), reason="highlight")
    assert_that(dump, has_key("log_time"), reason="log_time")
    assert_that(dump, has_key("log_path"), reason="log_path")
    assert_that(dump, has_key("highlighter"), reason="highlighter")
    assert_that(dump, has_key("theme"), reason="theme")
    assert_that(dump, has_key("legacy_windows"), reason="legacy_windows")
    assert_that(dump, has_key("safe_box"), reason="safe_box")
    assert_that(dump, has_key("styles_path"), reason="styles_path")


def test_console_settings_unset_properties() -> None:
    settings = NoPostInitConsoleSettings(color_system="truecolor")
    result = settings.model_dump(exclude_unset=True)
    assert_that(result, has_key("color_system"), reason="color_system")
    assert_that(result.keys(), has_length(1), reason="only color_system")


def test_console_settings_not_none_properties() -> None:
    settings = NoPostInitConsoleSettings()

    without_none = settings.model_dump(exclude_none=True)
    assert_that(without_none, not_(has_key("force_terminal")), reason="not force_terminal")


def test_console_settings_from_settings() -> None:
    from glom import glom

    console_settings = ConsoleSettings()
    textualize_settings = TextualizeSettings()
    toml_settings = glom(textualize_settings.pyproject, "data.tool.textualize-settings.console")

    actual = console_settings.model_dump(exclude_defaults=True)
    assert_that(actual, equal_to(toml_settings), reason="not unset")


@pytest.fixture
def traceback_settings() -> TracebacksSettingsModel:
    settings = TextualizeSettings()
    return settings.tracebacks_settings


def test_default_syntax_theme(traceback_settings: TracebacksSettingsModel) -> None:
    from rich.syntax import ANSI_DARK
    from pygments.token import Name

    default_syntax_theme = traceback_settings.syntax_theme
    assert_that(default_syntax_theme, equal_to("ansi_dark"), "default syntax_theme")

    theme = traceback_settings.get_syntax_theme()
    expected_token = ANSI_DARK.get(Name.Constant)
    actual_token = theme.get_style_for_token(Name.Constant)
    assert_that(actual_token, equal_to(expected_token), reason="expected_token")


@parameterize("pygments_theme", ["monokai", "gruvbox-light"])
def test_pygments_syntax_theme(stream_console: Console | None, pygments_theme: str) -> None:
    traceback_settings = TracebacksSettingsModel(theme=pygments_theme)
    assert_that(traceback_settings.syntax_theme, equal_to(pygments_theme))

    if stream_console:
        with pytest.raises(ValueError) as exc_info:
            raise ValueError("A value error")

    tb = Traceback.from_exception(
        exc_info.type,
        exc_info.value,
        exc_info.tb,
        show_locals=True,
        max_frames=100,
        theme=traceback_settings.syntax_theme,
        width=stream_console.width - 10,
    )
    stream_console.line(2)
    stream_console.rule(f"Traceback for '{pygments_theme}' pygments syntax theme", characters="=")
    stream_console.print(tb)


@parameterize("theme", ["pycharm_dark", "ansi_dark"])
def test_pycharm_dark_theme(stream_console: Console | None, theme: str) -> None:
    traceback_settings = TracebacksSettingsModel(theme=theme)
    assert_that(traceback_settings.syntax_theme, equal_to(theme), reason="syntax_theme")
    if stream_console:
        with pytest.raises(ValueError) as exc_info:
            raise ValueError("A value error")

    tb = Traceback.from_exception(
        exc_info.type,
        exc_info.value,
        exc_info.tb,
        show_locals=True,
        max_frames=100,
        theme=traceback_settings.syntax_theme,
        width=stream_console.width - 10,
    )
    stream_console.line(2)
    stream_console.rule(f"Traceback for '{theme}' pygments syntax theme", characters="=")
    stream_console.print(tb)
