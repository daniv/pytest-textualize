# Project : pytest-textualize
# File Name : plugin.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pytest_textualize import ConsoleFactory
from pytest_textualize import get_bool_opt
from pytest_textualize.settings import TextualizeSettings
from pytest_textualize.settings import settings_key

if TYPE_CHECKING:
    from collections.abc import Generator
    from pytest_textualize.helpers import SetEnv
    from _pytest._code import code as pytest_code
    from rich.console import Console

PLUGIN_NAME = "pytest-textualize"


@pytest.hookimpl
def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    from pytest_textualize.plugins.pytest_richtrace import hookspecs

    pluginmanager.add_hookspecs(hookspecs)



@pytest.hookimpl(tryfirst=True)
def pytest_addoption(parser: pytest.Parser, pluginmanager: pytest.PytestPluginManager) -> None:
    group = parser.getgroup(
        "pytest-textualize", description="pytest-textualize", after="terminal reporting"
    )
    group.addoption(
        "--textualize",
        action="store_true",
        dest="textualize",
        default=False,
        help="Enable rich terminal reporting using pytest-textualize. Default to %(default)s",
    )

    parser.addini("dotenv_path", type="string", default=".env", help="path to .env file")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    # -- validates that the plugin option was set to true
    if not config.getoption("--textualize", False, skip=True):
        return

    # -- Loading settings and store it into the stash
    from pytest_textualize.settings import settings_key

    from _pytest.logging import get_option_ini
    _settings = TextualizeSettings(
        pytestconfig=config,
        verbosity = config.getoption("--verbose"),
        log_format = get_option_ini(config, "log_format")
    )
    config.stash.setdefault(settings_key, _settings)

    # --load output console and error console, store them into the stash
    from pytest_textualize.plugins.pytest_richtrace import console_key
    from pytest_textualize.plugins.pytest_richtrace import error_console_key

    ConsoleFactory.stash = config.stash
    _stream_console = ConsoleFactory.console_output(config)
    config.stash.setdefault(console_key, _stream_console)

    _error_stream_console = ConsoleFactory.console_error_output(config)
    config.stash.setdefault(error_console_key, _error_stream_console)
    from pytest_textualize.textualize.theme.styles import print_styles

    # todo: example remove ...
    print_styles(_stream_console, "truecolor")

    # -- Adding the pycharm dark theme to RICH_SYNTAX_THEMES
    from pytest_textualize.textualize.theme.syntax import PYCHARM_DARK
    from rich.syntax import RICH_SYNTAX_THEMES

    RICH_SYNTAX_THEMES["pycharm_dark"] = PYCHARM_DARK

    # -- after having all configuration we start the logging handler
    from pytest_textualize import configure_logging

    configure_logging(_stream_console, _settings)

    # -- registering the main tracer plugin class
    from ..pytest_richtrace.richtrace.tracer import TextualizeTracer

    tracer = TextualizeTracer(config)
    config.pluginmanager.register(tracer, TextualizeTracer.name)

    # -- send historic hook to all the plugins that not registered yet
    config.pluginmanager.hook.pytest_console_and_settings.call_historic(
        kwargs=dict(
            console=_stream_console, error_console=_error_stream_console, settings=_settings
        )
    )


@pytest.hookimpl
def pytest_internalerror(excrepr: pytest_code.ExceptionRepr) -> bool | None:
    from rich import print

    print(excrepr.reprcrash.message)
    print(f"{excrepr.reprcrash.path}:{excrepr.reprcrash.lineno}")
    return False


# @pytest.hookimpl(tryfirst=True, wrapper=True)
# def pytest_unconfigure(config: pytest.Config) -> Generator[None, Any, None]:
#     from ..pytest_richtrace.richtrace.tracer import TextualizeTracer
#
#     if config.pluginmanager.hasplugin(TextualizeTracer.name):
#         plugin = config.pluginmanager.getplugin(TextualizeTracer.name)
#         config.pluginmanager.hook.pytest_plugin_unregistered(plugin=plugin)
#         yield
#         config.pluginmanager.unregister(plugin)


# ------------------------------------ pytest-textualize Fixtures ------------------------------------------------------


@pytest.fixture(scope="session")
def textualize_option(pytestconfig: pytest.Config) -> bool:
    return pytestconfig.getoption("textualize", False, skip=True)


@pytest.fixture(scope="session", autouse=False, name="settings")
def settings(pytestconfig: pytest.Config, textualize_option: bool) -> TextualizeSettings | None:
    if textualize_option:
        return pytestconfig.stash.get(settings_key, None)
    return None


@pytest.fixture(name="console", autouse=False, scope="session")
def create_output_console(pytestconfig: pytest.Config, settings: TextualizeSettings | None) -> Console | None:
    if settings and settings.console_outputs:
        return ConsoleFactory.console_output(pytestconfig)
    return None


@pytest.fixture(name="error_console", autouse=False, scope="session")
def create_error_console(pytestconfig: pytest.Config, settings: TextualizeSettings | None) -> Console | None:
    if settings and settings.console_outputs:
        return ConsoleFactory.console_error_output(pytestconfig)
    return None


@pytest.fixture
def force_color() -> Generator[None, None, None]:
    with patch("rich.console.Console.is_terminal", return_value=True):
        yield


@pytest.fixture(scope="session", autouse=True)
def turnoff_legacy_windows() -> Generator[None, None, None]:
    with patch("rich.console.detect_legacy_windows", return_value=False):
        yield


@pytest.fixture
def env() -> Generator[SetEnv, None, None]:
    """The fixture simulates adding environment variables to the test
    Taken from https://github.com/pydantic/pydantic-settings

    :return: yields An instance of SetEnv
    """
    from pytest_textualize.helpers import SetEnv

    setenv = SetEnv()
    yield setenv
    setenv.clear()

def _load_dotenv():
    from dotenv import load_dotenv, find_dotenv

    file = find_dotenv(".env", raise_error_if_not_found=True)
    load_dotenv(file, verbose=True)
    return not get_bool_opt("CONSOLE_OUTPUTS", os.getenv("CONSOLE_OUTPUTS"))

skipif_no_console = pytest.mark.skipif( _load_dotenv(), reason="no console")
