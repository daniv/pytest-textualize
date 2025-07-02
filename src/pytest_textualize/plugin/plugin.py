# Project : pytest-textualize
# File Name : plugin.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

# from _pytest.logging import get_option_ini
# from rich.control import Control
#
from pytest_textualize import TS_BASE_PATH
from pytest_textualize import Textualize

# from pytest_textualize import TextualizeFactory
from pytest_textualize import TextualizePlugins

#
# from pytest_textualize import get_bool_opt
# from pytest_textualize.plugin import console_key
# from pytest_textualize.plugin import error_console_key
#


if TYPE_CHECKING:
    from pytest_textualize.typist import TextualizeSettingsType

PLUGIN_NAME = TextualizePlugins.PLUGIN


@pytest.hookimpl
def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    from pytest_textualize.plugin import hookspecs

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
    group.addoption(
        "--no-rich-logging",
        "--no-richlog",
        action="store_false",
        dest="rich_logging",
        default=True,
        help="Disable using RichHandler for python logging. Default to %(default)s",
    )
    parser.addini("project_paths", type="paths", default=[], help="project paths")
    parser.addini(
        "env_file", type="string", default=str(TS_BASE_PATH / ".env"), help="the env file used"
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:

    # -- validates that the plugin option was set to true
    if not config.getoption("--textualize", False, skip=True):
        return

    # noinspection PyTypeChecker
    config.addinivalue_line("project_paths", config.rootpath / "static/styles")

    def init_logging() -> None:
        rich_logging_config = Textualize.logging_config(config)
        rich_logging_config.configure_logging()

    def init_console() -> None:
        # -- Adding the pycharm dark theme to RICH_SYNTAX_THEMES
        from pytest_textualize.textualize.theme.syntax import PYCHARM_DARK
        from rich.syntax import RICH_SYNTAX_THEMES

        RICH_SYNTAX_THEMES["pycharm_dark"] = PYCHARM_DARK
        Textualize.console_factory(config=config, instance="<stdout>")
        Textualize.console_factory(config=config, instance="<stderr>")

    try:
        Textualize.init_settings(config)
    except ValidationError as exc:
        pytest.exit(f"ValidationError during pytest_configure() -> {str(exc)}")

    if config.option.rich_logging:
        init_logging()

    from pytest_textualize.plugin import console_key
    from pytest_textualize.plugin import error_console_key
    from pytest_textualize.plugin import settings_key

    init_console()
    assert config.stash.get(console_key, None) is not None
    assert config.stash.get(error_console_key, None) is not None

    # verbose_logger = textualize().verbose_logger(config)
    # verbose_logger.add_console("<stdout>", config.stash.get(console_key, None))
    # verbose_logger.add_console("<stderr>", config.stash.get(error_console_key, None))

    # -- registering the main tracer plugin class
    from pytest_textualize.plugin.tracer import TextualizeTracer

    tracer = TextualizeTracer()
    config.pluginmanager.register(tracer, TextualizeTracer.name)

    # -- send historic hook to all the plugins that not registered yet
    config.pluginmanager.hook.pytest_console_and_settings.call_historic(
        kwargs=dict(
            console=config.stash.get(console_key, None),
            error_console=config.stash.get(error_console_key, None),
            settings=config.stash.get(settings_key, None),
        )
    )


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config: pytest.Config) -> None:
    from pytest_textualize.plugin import settings_key

    if not config.getoption("--textualize", False, skip=True):
        return None

    if settings_key in config.stash:
        del config.stash[settings_key]

    # -- unregistering the main tracer plugin
    if config.pluginmanager.hasplugin(TextualizePlugins.TRACER):
        plugin = config.pluginmanager.getplugin(TextualizePlugins.TRACER)
        config.pluginmanager.unregister(plugin, TextualizePlugins.TRACER)

    # -- unregistering this plugin
    if config.pluginmanager.hasplugin(PLUGIN_NAME):
        plugin = config.pluginmanager.getplugin(PLUGIN_NAME)
        config.pluginmanager.unregister(plugin, PLUGIN_NAME)

    return None


# ------------------------------------ pytest-textualize Fixtures ------------------------------------------------------


@pytest.fixture(scope="session", name="opt_textualize")
def _textualize_option(pytestconfig: pytest.Config) -> bool:
    """Return if the rich_logging option was set, to use RichHandler to basicConfig

    :param pytestconfig: The pytest.Config instance
    :return: True if --textualize was set
    """
    return pytestconfig.getoption("textualize", False, skip=True)


@pytest.fixture(scope="session", name="opt_rich_logging")
def _rich_logging_option(pytestconfig: pytest.Config) -> bool:
    """Return if the --textualize option was set, mainly for internal use.

    :param pytestconfig: The pytest.Config instance
    :return: True if --textualize was set
    """
    return pytestconfig.getoption("textualize", False, skip=True)


@pytest.fixture(scope="session", name="settings")
def init_settings(pytestconfig: pytest.Config, opt_textualize: bool) -> TextualizeSettingsType:
    from dotenv import load_dotenv
    from pathlib import Path
    from pytest_textualize.settings import TextualizeSettings

    if opt_textualize:
        # loading environment variable fro file, based on ini value env_file, skipped if not exists
        ini_env_file = pytestconfig.getini("env_file")
        if Path(ini_env_file).is_file():
            load_dotenv(ini_env_file, verbose=True)
        ts = TextualizeSettings(pytestconfig=pytestconfig)
        pytestconfig.stash[settings_key] = ts

        def cleanup() -> None:
            del ts.logging_settings
            del ts.pytestconfig
            del ts.console_settings
            del ts.tracebacks_settings

        pytestconfig.add_cleanup(cleanup)

        yield ts

        del pytestconfig.stash[settings_key]


@pytest.fixture(scope="session", autouse=True, name="rich_logging")
def init_logging(pytestconfig: pytest.Config, opt_rich_logging: bool) -> None:
    if opt_rich_logging:
        pass


# @pytest.fixture(scope="session", autouse=False, name="textualize")
# def get_textualize_service() -> TextualizeType:
#     return pytset_textualize()
#

#
#
# @pytest.fixture(scope="session", autouse=False, name="settings")
# def settings(pytestconfig: pytest.Config, textualize_option: bool) -> TextualizeSettingsType | None:
#     if textualize_option:
#         from pytest_textualize.plugin import settings_key
#         return pytestconfig.stash.get(settings_key, None)
#     return None
#
#
# @pytest.fixture(name="console", autouse=False, scope="session")
# def create_output_console(
#     pytestconfig: pytest.Config, settings: TextualizeSettingsType | None
# ) -> Console | None:
#     if settings and settings.console_outputs:
#         # - the console factory won't create a new console if already exists in stash
#         return TextualizeFactory.console_factory(pytestconfig, "stdout")
#     return None
#
#
# @pytest.fixture(name="error_console", autouse=False, scope="session")
# def create_error_console(
#     pytestconfig: pytest.Config, settings: TextualizeSettingsType | None
# ) -> Console | None:
#     if settings and settings.console_outputs:
#         # - the console factory won't create a new console if already exists in stash
#         return TextualizeFactory.console_factory(pytestconfig, "stderr")
#     return None
#
#
# @pytest.fixture
# def force_color() -> Generator[None, None, None]:
#     with patch("rich.console.Console.is_terminal", return_value=True):
#         yield
#
#
# @pytest.fixture(scope="session", autouse=True)
# def turnoff_legacy_windows() -> Generator[None, None, None]:
#     with patch("rich.console.detect_legacy_windows", return_value=False):
#         yield
#
#
# @pytest.fixture
# def env() -> Generator[SetEnv, None, None]:
#     """The fixture simulates adding environment variables to the test
#     Taken from https://github.com/pydantic/pydantic-settings
#
#     :return: yields An instance of SetEnv
#     """
#
#     from pytest_textualize import SetEnv
#
#     setenv = SetEnv()
#     yield setenv
#     setenv.clear()
#
#
# def _load_dotenv():
#     from dotenv import load_dotenv, find_dotenv
#
#     file = find_dotenv(".env", raise_error_if_not_found=True)
#     load_dotenv(file, verbose=True)
#     return not get_bool_opt("CONSOLE_OUTPUTS", os.getenv("CONSOLE_OUTPUTS"))


# skipif_no_console = pytest.mark.skipif(_load_dotenv(), reason="no console")
