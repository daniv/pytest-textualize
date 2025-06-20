# Project : pytest-textualize
# File Name : plugin.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

from typing import Any
from typing import Generator
from typing import TYPE_CHECKING

import pytest

from pytest_textualize import ConsoleFactory
from pytest_textualize.settings import TextualizeSettings
from pytest_textualize.settings import settings_key

if TYPE_CHECKING:
    from _pytest._code import code as pytest_code

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

    _settings = TextualizeSettings()
    config.stash.setdefault(settings_key, _settings)
    _settings.verbosity = config.getoption("--verbose")

    # --load output console and error console, store them into the stash
    from pytest_textualize.plugins.pytest_richtrace import console_key
    from pytest_textualize.plugins.pytest_richtrace import error_console_key
    from pytest_textualize.console_factory import push_theme

    ConsoleFactory.stash = config.stash
    _stream_console = ConsoleFactory.console_output(config)
    config.stash.setdefault(console_key, _stream_console)
    push_theme(config.rootpath, _stream_console, _settings)

    _error_stream_console = ConsoleFactory.console_error_output(config)
    config.stash.setdefault(error_console_key, _error_stream_console)
    push_theme(config.rootpath, _error_stream_console, _settings)
    from pytest_textualize.textualize.theme.styles import print_styles

    print_styles(_stream_console, "truecolor")

    # -- Adding the pycharm dark theme to RICH_SYNTAX_THEMES

    # from pytest_textualize.textualize.theme.syntax import PYCHARM_DARK
    # RICH_SYNTAX_THEMES["pycharm_dark"] = PYCHARM_DARK

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


@pytest.hookimpl(tryfirst=True, wrapper=True)
def pytest_unconfigure(config: pytest.Config) -> Generator[None, Any, None]:
    from ..pytest_richtrace.richtrace.tracer import TextualizeTracer

    if config.pluginmanager.hasplugin(TextualizeTracer.name):
        plugin = config.pluginmanager.getplugin(TextualizeTracer.name)
        config.pluginmanager.hook.pytest_plugin_unregistered(plugin=plugin)
        yield
        config.pluginmanager.unregister(plugin)


@pytest.fixture(scope="session")
def textualize_option(pytestconfig: pytest.Config) -> bool:
    return pytestconfig.getoption("textualize", False, skip=True)


@pytest.fixture(scope="session", autouse=False, name="settings")
def settings(pytestconfig: pytest.Config, textualize_option: bool) -> TextualizeSettings | None:
    if textualize_option:
        return pytestconfig.stash.get(settings_key, None)
    return None
