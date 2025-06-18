# Project : pytest-textualize
# File Name : plugin.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from dotenv import load_dotenv

from pytest_textualize import ConsoleFactory
from pytest_textualize.settings import settings_key
from pytest_textualize.textualize import locate
from pytest_textualize.settings import TextualizeSettings
from rich.console import Console

if TYPE_CHECKING:
    pass

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
    import dotenv
    import os

    textualize = config.getoption("textualize", False, skip=True)

    if int(os.getenv("LOAD_PLUGIN", 0)) == 0 or textualize is False:
        return

    path = dotenv.find_dotenv(".env")
    assert path is not None, ".env file not found"
    dotenv.load_dotenv(dotenv_path=path, override=True, verbose=True)

    from pytest_textualize.plugins.pytest_richtrace import console_key
    from pytest_textualize.settings import settings_key
    from pytest_textualize.plugins.pytest_richtrace import error_console_key

    _settings = TextualizeSettings()
    config.stash.setdefault(settings_key, _settings)

    ConsoleFactory.stash = config.stash
    _stream_console = ConsoleFactory.console_output()
    config.stash.setdefault(console_key, _stream_console)

    _error_stream_console = ConsoleFactory.console_error_output()
    config.stash.setdefault(error_console_key, _error_stream_console)

    # -- Adding the pycharm dark theme to RICH_SYNTAX_THEMES
    from rich.syntax import RICH_SYNTAX_THEMES
    from pytest_textualize.textualize.syntax import PYCHARM_DARK

    RICH_SYNTAX_THEMES["pycharm_dark"] = PYCHARM_DARK

    from pytest_textualize.plugins.pytest_richtrace.richtrace.tracer import PytestRichTracer

    tracer = PytestRichTracer(config)
    config.pluginmanager.register(tracer, PytestRichTracer.name)

    config.pluginmanager.hook.pytest_console_and_settings.call_historic(
        kwargs=dict(
            console=_stream_console, error_console=_error_stream_console, settings=_settings
        )
    )


@pytest.fixture(scope="session")
def textualize_option(pytestconfig: pytest.Config) -> bool:
    return pytestconfig.getoption("textualize", False, skip=True)


@pytest.fixture(scope="session", autouse=False, name="settings")
def settings(pytestconfig: pytest.Config, textualize_option: bool) -> TextualizeSettings:
    if textualize_option:
        return pytestconfig.stash.get(settings_key, None)
