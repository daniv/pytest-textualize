from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pytest_textualize.plugins.pytest_richtrace import console_key
from pytest_textualize.plugins.pytest_richtrace import error_console_key
from pytest_textualize.settings import settings_key

if TYPE_CHECKING:
    from collections.abc import Generator
    from tests.helpers.env import SetEnv
    from rich.console import Console
    from pathlib import Path

pytest_plugins = "pytester"


@pytest.hookimpl
def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    from pytest_textualize.plugins.pytest_richtrace import plugin

    pluginmanager.register(plugin, plugin.PLUGIN_NAME)


@pytest.hookimpl(tryfirst=True)
def pytest_cmdline_main(config: pytest.Config) -> pytest.ExitCode | int | None:
    if not "--strict-markers" in config.invocation_params.args:
        config.known_args_namespace.strict_markers = True
        config.option.strict_markers = True
    if not "--strict-config" in config.invocation_params.args:
        config.known_args_namespace.strict_config = True
        config.option.strict_config = True
    config.known_args_namespace.keepduplicates = False
    return None


@pytest.hookimpl
def pytest_addoption(parser: pytest.Parser, pluginmanager: pytest.PytestPluginManager) -> None:
    group = parser.getgroup("textualize", description="testing pytest-textualize options")
    group.addoption(
        "--no-print",
        action="store_false",
        dest="console_print",
        default=True,
        help="Do not print console outputs during tests.",
    )


class TextualizePytester:
    def __init__(self, pytester: pytest.Pytester):
        self.pytester = pytester

    def run_pytest(self, *args, **kwargs) -> pytest.RunResult:
        result = self.pytester.runpytest("--textualize", str(self.pytester.path), *args, **kwargs)
        return result

    def make_pyfile(self, *args, **kwargs) -> Path:
        return self.pytester.makepyfile(*args, **kwargs)

    def make_conftest(self, source: str) -> Path:
        return self.pytester.makeconftest(source)


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    textualize = config.getoption("textualize", False, skip=True)
    if textualize is True:
        assert config.stash.get(console_key, None) is not None
        assert config.stash.get(error_console_key, None) is not None
        assert config.stash.get(settings_key, None) is not None


@pytest.fixture
def env() -> Generator[SetEnv, None, None]:
    """The fixture simulates adding environment variables to the test
    Taken from https://github.com/pydantic/pydantic-settings

    :return: yields An instance of SetEnv
    """
    from tests.helpers.env import SetEnv

    setenv = SetEnv()

    yield setenv

    setenv.clear()


@pytest.fixture
def textualize_pytester(pytester: pytest.Pytester):
    return TextualizePytester(pytester)


@pytest.fixture(scope="function")
def textualize(pytestconfig: pytest.Config) -> bool:
    return pytestconfig.getoption("textualize", False, skip=True)


@pytest.fixture(name="console", autouse=False, scope="session")
def create_output_console(pytestconfig: pytest.Config) -> Console | None:
    from rich.console import Console

    if pytestconfig.option.console_print:
        args = dict(
            color_system="truecolor",
            force_terminal=True,
            force_interactive=True,
            legacy_windows=False,
        )
        if not sys.stdout.isatty():
            args["_environ"] = {"COLUMNS": "190", "TERM": "xterm-256color"}
        console = Console(**args)
        yield console
        del console
    else:
        return None


@pytest.fixture(scope="session", autouse=True)
def turnoff_legacy_windows():
    with patch("rich.console.detect_legacy_windows", return_value=False):
        yield


@pytest.fixture()
def force_color():
    with patch("rich.console.Console.is_terminal", return_value=True):
        yield


@pytest.fixture(scope="session", name="stream_console", autouse=False)
def get_output_console(pytestconfig: pytest.Config, console_print: bool) -> Console | None:
    if console_print:
        return pytestconfig.stash.get(console_key, None)

# @pytest.fixture(scope="session", name="consoles", autouse=False)
# def get_consoles(
#         pytestconfig: pytest.Config, console_print: bool
# ) -> tuple[Console, Console] | None:
#     if console_print:
#         return pytestconfig.stash.get(console_key, None), pytestconfig.stash.get(
#             error_console_key, None
#         )
