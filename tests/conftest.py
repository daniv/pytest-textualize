from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from tests.helpers.env import SetEnv


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
def pytest_configure(config: pytest.Config) -> None:
    pass
    # # TODO: move to settings setup
    # from _pytest._io.terminalwriter import should_do_markup
    #
    # # -- forcing color on terminal
    # if not should_do_markup(sys.stdout):
    #     os.environ["PY_COLORS"] = "1"


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
