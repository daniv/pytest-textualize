# Project : pytest-textualize
# File Name : settings_tests.py
# Dir Path : tests/plugin_tests/textualize_tests

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from glom import glom
from hamcrest import assert_that
from hamcrest import equal_to
from hamcrest import greater_than
from hamcrest import none

from pytest_textualize import TextualizeSettings
from pytest_textualize import get_bool_opt
from pytest_textualize.helpers import SetEnv
from pytest_textualize.helpers import get_int_opt
from pytest_textualize.textualize import locate

if TYPE_CHECKING:
    pass
    from collections.abc import Generator

parameterize = pytest.mark.parametrize


@pytest.fixture(autouse=False, scope="module")
def clean_environment() -> Generator[None, None, None]:
    """Cleans the environment variables"""
    with mock.patch.dict(os.environ, clear=True):
        yield

def test__init__model_config(pytestconfig: pytest.Config) -> None:
    settings = TextualizeSettings(pytestconfig=pytestconfig)

    assert_that(settings.model_config.get("extra"), equal_to("forbid"), reason="extra")
    assert_that(settings.model_config.get("validate_default"), equal_to(True), reason="validate_default")
    assert_that(settings.model_config.get("case_sensitive"), equal_to(False), reason="case_sensitive")
    assert_that(settings.model_config.get("env_file"), equal_to(".env"), reason="env_file")
    assert_that(settings.model_config.get("env_file"), equal_to(".env"), reason="env_file")
    assert_that(settings.model_config.get("env_file_encoding"), equal_to("utf-8"), reason="env_file_encoding")
    assert_that(settings.model_config.get("env_ignore_empty"), equal_to(True), reason="env_ignore_empty")
    assert_that(settings.model_config.get("env_parse_none_str"), equal_to("None"), reason="env_parse_none_str")
    assert_that(settings.model_config.get("title"), equal_to('Pytest Textualize Settings'), reason="title")
    assert_that(settings.model_config.get('pyproject_toml_table_header'), equal_to(('tool', 'textualize-settings')), reason="pyproject_toml_table_header")
    assert_that(settings.model_config.get('pyproject_toml_depth'), greater_than(1), reason="pyproject_toml_depth")


def test__init__dot_env(pytestconfig: pytest.Config) -> None:
    expected_py_colors = get_int_opt("py_colors", os.getenv("PY_COLORS"))
    expected_console_outputs = get_bool_opt("console_outputs", os.getenv("CONSOLE_OUTPUTS"))

    settings = TextualizeSettings(pytestconfig=pytestconfig)
    assert_that(glom(settings.model_fields, "py_colors.default"), equal_to(0), reason="default py_colors")
    assert_that(glom(settings.model_fields, "console_outputs.default"), equal_to(False), reason="default console_outputs")
    assert_that(settings.py_colors, equal_to(expected_py_colors), reason="PY_COLORS")
    assert_that(settings.console_outputs, equal_to(expected_console_outputs), reason="CONSOLE_OUTPUTS")


def test_logging_model_defaults(pytestconfig: pytest.Config) -> None:
    settings = TextualizeSettings(pytestconfig=pytestconfig)
    logging = settings.model_fields["logging"]

    field_info = settings.get_field_value(logging, "level")
    assert_that(field_info.default, equal_to(0), reason="default level")

    field_info = settings.get_field_value(logging, "enable_link_path")
    assert_that(field_info.default, equal_to(True), reason="default enable_link_path")

    field_info = settings.get_field_value(logging, "highlighter")
    assert_that(field_info.default, none(), reason="default enable_link_path")

    field_info = settings.get_field_value(logging, "markup")
    assert_that(field_info.default, equal_to(False), reason="default markup")

    field_info = settings.get_field_value(logging, "locals_max_length")
    assert_that(field_info.default, equal_to(10), reason="default locals_max_length")


def test_tracebacks_model_defaults(pytestconfig: pytest.Config) -> None:
    settings = TextualizeSettings(pytestconfig=pytestconfig)
    tracebacks = settings.model_fields["tracebacks"]

    field_info = settings.get_field_value(tracebacks, "code_width")
    assert_that(field_info.default, equal_to(88), reason="default code_width")

    field_info = settings.get_field_value(tracebacks, "extra_lines")
    assert_that(field_info.default, equal_to(3), reason="default extra_lines")

    field_info = settings.get_field_value(tracebacks, "max_frames")
    assert_that(field_info.default, equal_to(100), reason="default max_frames")

    field_info = settings.get_field_value(tracebacks, "show_locals")
    assert_that(field_info.default, equal_to(False), reason="default show_locals")

    field_info = settings.get_field_value(tracebacks, "word_wrap")
    assert_that(field_info.default, equal_to(True), reason="default word_wrap")


@pytest.mark.usefixtures("clean_environment")
@parameterize("py_colors, console_outputs", [(0, True), (1, False)])
def test_changing_env_values(
        pytestconfig: pytest.Config,
        env: SetEnv, py_colors: int, console_outputs: bool
) -> None:
    assert "PY_COLORS" not in os.environ
    assert "CONSOLE_OUTPUTS" not in os.environ
    env.set("PY_COLORS", str(py_colors))
    env.set("CONSOLE_OUTPUTS", str(console_outputs))
    assert "PY_COLORS" in os.environ
    assert "CONSOLE_OUTPUTS" in os.environ

    # noinspection PyArgumentList
    settings = TextualizeSettings(pytestconfig=pytestconfig)
    assert_that(settings.py_colors, equal_to(py_colors), reason="PY_COLORS")
    assert_that(settings.console_outputs, equal_to(console_outputs), reason="CONSOLE_OUTPUTS")

@pytest.mark.usefixtures("clean_environment")
@pytest.mark.xfail(raises=AssertionError, reason="not updated atef changing environment")
def test_changing_env_values_after__init(
        pytestconfig: pytest.Config, env: SetEnv
) -> None:
    settings = TextualizeSettings(pytestconfig=pytestconfig)

    default_py_color = glom(settings.model_fields, "py_colors.default")
    default_console_outputs = glom(settings.model_fields, "console_outputs.default")
    assert_that(settings.py_colors, equal_to(default_py_color), reason="PY_COLORS default")
    assert_that(settings.console_outputs, equal_to(default_console_outputs), reason="CONSOLE_OUTPUTS")

    new_py_color = 1 if default_py_color == 0 else 1
    new_console_outputs = not default_console_outputs
    env.set("PY_COLORS", str(new_py_color))
    env.set("CONSOLE_OUTPUTS", str(new_console_outputs))

    assert_that(settings.py_colors, equal_to(new_py_color), reason="new value PY_COLORS")
    assert_that(settings.console_outputs, equal_to(new_console_outputs), reason="new value CONSOLE_OUTPUTS")


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

# def test_console_settings_properties() -> None:
#     settings = NoPostInitConsoleSettings()
#     dump = settings.model_dump()
#     assert_that(dump, has_key("color_system"), reason="color_system")
#     assert_that(dump, has_key("force_terminal"), reason="force_terminal")
#     assert_that(dump, has_key("force_jupyter"), reason="force_jupyter")
#     assert_that(dump, has_key("force_interactive"), reason="force_interactive")
#     assert_that(dump, has_key("soft_wrap"), reason="soft_wrap")
#     assert_that(dump, has_key("no_color"), reason="no_color")
#     assert_that(dump, has_key("markup"), reason="markup")
#     assert_that(dump, has_key("emoji"), reason="emoji")
#     assert_that(dump, has_key("emoji_variant"), reason="emoji_variant")
#     assert_that(dump, has_key("highlight"), reason="highlight")
#     assert_that(dump, has_key("log_time"), reason="log_time")
#     assert_that(dump, has_key("log_path"), reason="log_path")
#     assert_that(dump, has_key("highlighter"), reason="highlighter")
#     assert_that(dump, has_key("theme"), reason="theme")
#     assert_that(dump, has_key("legacy_windows"), reason="legacy_windows")
#     assert_that(dump, has_key("safe_box"), reason="safe_box")
#     assert_that(dump, has_key("styles_path"), reason="styles_path")
#
#
# def test_console_settings_unset_properties() -> None:
#     settings = NoPostInitConsoleSettings(color_system="truecolor")
#     result = settings.model_dump(exclude_unset=True)
#     assert_that(result, has_key("color_system"), reason="color_system")
#     assert_that(result.keys(), has_length(1), reason="only color_system")
#
#
# def test_console_settings_not_none_properties() -> None:
#     settings = NoPostInitConsoleSettings()
#
#     without_none = settings.model_dump(exclude_none=True)
#     assert_that(without_none, not_(has_key("force_terminal")), reason="not force_terminal")
#
#
# def test_console_settings_from_settings() -> None:
#     from glom import glom
#
#     console_settings = ConsoleSettings()
#     textualize_settings = TextualizeSettings()
#     toml_settings = glom(textualize_settings.pyproject, "data.tool.textualize-settings.console")
#
#     actual = console_settings.model_dump(exclude_defaults=True)
#     assert_that(actual, equal_to(toml_settings), reason="not unset")
#
#
# @pytest.fixture
# def traceback_settings() -> TracebacksSettingsModel:
#     settings = TextualizeSettings()
#     return settings.tracebacks_settings
#
#
# def test_default_syntax_theme(traceback_settings: TracebacksSettingsModel) -> None:
#     from rich.syntax import ANSI_DARK
#     from pygments.token import Name
#
#     default_syntax_theme = traceback_settings.syntax_theme
#     assert_that(default_syntax_theme, equal_to("ansi_dark"), "default syntax_theme")
#
#     theme = traceback_settings.get_syntax_theme()
#     expected_token = ANSI_DARK.get(Name.Constant)
#     actual_token = theme.get_style_for_token(Name.Constant)
#     assert_that(actual_token, equal_to(expected_token), reason="expected_token")
#
#
# @parameterize("pygments_theme", ["monokai", "gruvbox-light"])
# def test_pygments_syntax_theme(stream_console: Console | None, pygments_theme: str) -> None:
#     traceback_settings = TracebacksSettingsModel(theme=pygments_theme)
#     assert_that(traceback_settings.syntax_theme, equal_to(pygments_theme))
#
#     if stream_console:
#         with pytest.raises(ValueError) as exc_info:
#             raise ValueError("A value error")
#
#     tb = Traceback.from_exception(
#         exc_info.type,
#         exc_info.value,
#         exc_info.tb,
#         show_locals=True,
#         max_frames=100,
#         theme=traceback_settings.syntax_theme,
#         width=stream_console.width - 10,
#     )
#     stream_console.line(2)
#     stream_console.rule(f"Traceback for '{pygments_theme}' pygments syntax theme", characters="=")
#     stream_console.print(tb)
#
#
# @parameterize("theme", ["pycharm_dark", "ansi_dark"])
# def test_pycharm_dark_theme(stream_console: Console | None, theme: str) -> None:
#     traceback_settings = TracebacksSettingsModel(theme=theme)
#     assert_that(traceback_settings.syntax_theme, equal_to(theme), reason="syntax_theme")
#     if stream_console:
#         with pytest.raises(ValueError) as exc_info:
#             raise ValueError("A value error")
#
#     tb = Traceback.from_exception(
#         exc_info.type,
#         exc_info.value,
#         exc_info.tb,
#         show_locals=True,
#         max_frames=100,
#         theme=traceback_settings.syntax_theme,
#         width=stream_console.width - 10,
#     )
#     stream_console.line(2)
#     stream_console.rule(f"Traceback for '{theme}' pygments syntax theme", characters="=")
#     stream_console.print(tb)
