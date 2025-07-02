from __future__ import annotations

from collections import OrderedDict
from collections.abc import Generator
from io import StringIO
from typing import Any
from typing import Sized
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import cast

import pytest
from boltons.strutils import strip_ansi
from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import ends_with
from hamcrest import equal_to
from hamcrest import has_length
from hamcrest import starts_with
from pydantic import ValidationError
from pytest import param
from rich.console import Console
from rich.text import Text

from pytest_textualize import Verbosity

if TYPE_CHECKING:
    from pytest_textualize.typist import VerboseLoggerType
    from pytest_textualize.typist import TextualizeSettingsType
    from hamcrest.core.matcher import Matcher

parameterize = pytest.mark.parametrize
SizedT = TypeVar("SizedT", bound=Sized)

from pytest_textualize import textualize

MODULE_VARS: dict[str, Any] = OrderedDict({})

# noinspection PyTypeChecker
def get_consoles_from_module_storage() -> tuple[Console, Console]:
    stdout_console = MODULE_VARS.get("<stdout>", None)
    if stdout_console is None:
        pytest.fail("No <stdout> console")

    stderr_console = MODULE_VARS.get("<stderr>", None)
    if stderr_console is None:
        pytest.fail("No <stderr> console")

    if stdout_console is None or stderr_console is None:
        raise AssertionError("No consoles")
    return stdout_console, stderr_console


# noinspection PyTypeChecker
def get_console_from_module_storage(name: str) -> Console:
    named_console = MODULE_VARS.get(name, None)
    if named_console is None:
        pytest.fail(f"No '{name}' console")
    return named_console


# -- https://pytest-with-eric.com/introduction/pytest-generate-tests/
@pytest.hookimpl
def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:

    if 'log_message' in metafunc.fixturenames:
        verbose = metafunc.config.option.verbose
        ids = ["debug", "info", "warning", "error", "critical"]
        test_data = [
            ((Verbosity.DEBUG, "debug"), contains_string("debug") if verbose == 3 else equal_to("")),
            ((Verbosity.VERY_VERBOSE, "info"), contains_string("info") if verbose > 1  else equal_to("")),
            ((Verbosity.VERBOSE, "warning"), contains_string("warning") if verbose > 0 else equal_to("")),
            ((Verbosity.NORMAL, "error"), contains_string("error") if verbose >= 0 else equal_to("")),
            ((Verbosity.QUIET, "critical"), contains_string("critical")),
        ]
        metafunc.parametrize("log_message, expected", test_data, ids=ids)

@pytest.fixture(scope="module", autouse=True)
def module_storage(request: pytest.FixtureRequest, settings: TextualizeSettingsType) -> None:
    if not "settings" in MODULE_VARS:
        MODULE_VARS["settings"] = settings
    if not "pytestconfig" in MODULE_VARS:
        MODULE_VARS["pytestconfig"] = request.config

    MODULE_VARS["<stdout>"] = textualize().console_factory(request.config, "<stdout>")
    MODULE_VARS["<stderr>"] = textualize().console_factory(request.config, "<stderr>")
    MODULE_VARS["<null>"] = textualize().console_factory(request.config, "null")
    MODULE_VARS["<buffer>"] = textualize().console_factory(request.config, "buffer")

    def cleanup() -> None:
        MODULE_VARS.clear()
    request.addfinalizer(cleanup)

@pytest.fixture
def verbose_logger(request: pytest.FixtureRequest) -> Generator[VerboseLoggerType, None, None]:
    vlogger = textualize().verbose_logger(request.config)
    def cleanup() -> None:
        if vlogger.console_count > 0:
            vlogger.remove_all_consoles()

    request.addfinalizer(cleanup)
    yield vlogger


def test__init__class(pytestconfig: pytest.Config, verbose_logger: VerboseLoggerType) -> None:
    vl = verbose_logger

    assert_that(vl.console_count, equal_to(0), reason="console_count")
    assert_that(cast(SizedT, vl.consoles), has_length(0), reason="no consoles")
    assert_that(vl.prefix, equal_to("\u2b25"), reason="prefix")
    assert_that(vl.is_disabled, equal_to(False), reason="is_disabled")
    assert_that(vl.is_enabled, equal_to(not vl.is_disabled), reason="is_enabled")
    assert_that(
        vl.effective_verbose,
        equal_to(Verbosity(pytestconfig.option.verbose)),
        reason="effective_verbose",
    )
    assert_that(
        vl.effective_verbose.value,
        equal_to(pytestconfig.option.verbose),
        reason="effective_verbose",
    )
    assert_that(vl.show_locals, equal_to(pytestconfig.option.showlocals), reason="showlocals")
    assert_that(vl.console_count, equal_to(0), reason="console_count")
    assert_that(vl.raise_exceptions, equal_to(True), reason="raise_exceptions")


@parameterize(
    "verbosity, as_int, as_str",
    [
        param(Verbosity.QUIET, -1, "QUIET"),
        param(Verbosity.NORMAL, 0, "NORMAL"),
        param(Verbosity.VERBOSE, 1, "VERBOSE"),
        param(Verbosity.VERY_VERBOSE, 2, "VERY_VERBOSE"),
        param(Verbosity.DEBUG, 3, "DEBUG"),
    ],
)
def test__verbosity(verbosity: Verbosity, as_int: int, as_str: str) -> None:
    assert_that(verbosity.value, equal_to(as_int), reason="int value")
    assert_that(verbosity.name, equal_to(as_str), reason="str value")


# noinspection PyTypeChecker
def test_set_verbose(pytestconfig: pytest.Config, verbose_logger: VerboseLoggerType) -> None:
    vl = verbose_logger

    pytest_verbose = pytestconfig.option.verbose
    assert_that(vl._verbosity.value, equal_to(pytest_verbose), reason="_verbosity.value")
    assert_that(
        vl.effective_verbose, equal_to(Verbosity(pytest_verbose)), reason="effective_verbose"
    )
    assert_that(vl._is_enabled_for(pytest_verbose), equal_to(True), reason="_is_enabled_for")
    assert_that(vl._is_enabled_for(pytest_verbose + 1), equal_to(False), reason="_is_enabled_for")


def test_disable_logger(verbose_logger: VerboseLoggerType) -> None:
    vl = verbose_logger

    vl.set_disabled(True)
    assert_that(vl.is_disabled, equal_to(True), reason="is_disabled")
    assert_that(vl.is_enabled, equal_to(False), reason="is_enabled")
    assert_that(vl._is_enabled_for(Verbosity.DEBUG), equal_to(False), reason="verbosity")
    assert_that(vl._is_enabled_for(Verbosity.NORMAL), equal_to(False), reason="verbosity")
    assert_that(vl._is_enabled_for(Verbosity.QUIET), equal_to(False), reason="verbosity")


def test_change_prefix(verbose_logger: VerboseLoggerType) -> None:
    vl = verbose_logger

    vl.prefix = "*"
    assert_that(vl.prefix, equal_to("*"), reason="prefix")
    with pytest.raises(ValidationError) as exc_info:
        vl.prefix = "----"

    with pytest.raises(ValidationError) as exc_info:
        vl.prefix = 1


def test_show_locals(verbose_logger: VerboseLoggerType, monkeypatch: pytest.MonkeyPatch) -> None:
    vl = verbose_logger

    monkeypatch.setattr(vl, "show_locals", True)
    assert_that(vl.show_locals, equal_to(True), reason="show_locals")


def test_adding_standard_consoles(verbose_logger: VerboseLoggerType) -> None:
    std_out = Console()
    std_err = Console(stderr=True)

    added, msg = verbose_logger.add_console("stdout", std_out)
    assert_that(added, equal_to(True), reason="added")
    assert_that(msg, ends_with("added successfully."), reason="message")

    assert_that(verbose_logger.console_count, equal_to(1), reason="console_count")
    assert_that(verbose_logger.has_console("stdout"), equal_to(True), reason="has_console")
    assert_that(verbose_logger.has_console("pytest"), equal_to(False), reason="has_console")

    added, _ = verbose_logger.add_console("stderr", std_err)

    assert_that(added, equal_to(True), reason="added")
    assert_that(verbose_logger.console_count, equal_to(2), reason="console_count")
    assert_that(verbose_logger.has_console("stdout"), equal_to(True), reason="has_console")
    assert_that(verbose_logger.has_console("stderr"), equal_to(True), reason="has_console")


def test_adding_existing_name(verbose_logger: VerboseLoggerType) -> None:
    std_out = Console()
    std_err = Console(stderr=True)

    verbose_logger.add_console("stdout", std_out)
    with pytest.raises(NameError):
        verbose_logger.add_console("stdout", std_err)


def test_adding_same_console_different_names(verbose_logger: VerboseLoggerType) -> None:
    std_out = Console()

    added, _ = verbose_logger.add_console("stdout", std_out)
    assert_that(added, equal_to(True), reason="added")
    added, msg = verbose_logger.add_console("stderr", std_out)
    assert_that(added, equal_to(False), reason="added")
    assert_that(msg, starts_with("Console exists with different name"), reason="msg exists")


def test_adding_same_console_streams(verbose_logger: VerboseLoggerType) -> None:
    std_out1 = Console()
    std_out2 = Console()

    added, _ = verbose_logger.add_console("stdout1", std_out1)
    assert_that(added, equal_to(True), reason="added")
    added, msg = verbose_logger.add_console("stdout2", std_out2)
    assert_that(cast(SizedT, verbose_logger.consoles), has_length(1), reason="duplicate consoles")
    assert_that(added, equal_to(False), reason="added")
    assert_that(msg, starts_with("Console exists with different name"), reason="msg exists")


def test_adding_multiple_buffered_consoles(verbose_logger: VerboseLoggerType) -> None:
    string_1 = StringIO()
    stream1 = Console(file=string_1)
    stream2 = Console(file=StringIO())
    stream3 = Console(file=string_1)

    added, _ = verbose_logger.add_console("stream1", stream1)
    assert_that(added, equal_to(True), reason="added")

    added, _ = verbose_logger.add_console("stream2", stream2)
    assert_that(added, equal_to(True), reason="added")

    added, msg = verbose_logger.add_console("stream3", stream3)
    assert_that(added, equal_to(False), reason="added")
    assert_that(
        msg, starts_with("Console exists with different name -> 'stream1'"), reason="msg exists"
    )


def test_removing_a_console(verbose_logger: VerboseLoggerType) -> None:
    stream1 = Console(file=StringIO())
    stream2 = Console(file=StringIO())

    verbose_logger.add_console("stream1", stream1)
    verbose_logger.add_console("stream2", stream2)
    assert_that(verbose_logger.has_console("stream1"), equal_to(True), reason="stream1")

    response = verbose_logger.remove_console("stream1")
    assert_that(response, equal_to(True), reason="response")
    assert_that(verbose_logger.has_console("stream1"), equal_to(False), reason="has stream1")
    assert_that(verbose_logger.has_console("stream2"), equal_to(True), reason="has stream2")

    # -- removing again
    response = verbose_logger.remove_console("stream1")
    assert_that(response, equal_to(False), reason="response")

    verbose_logger.remove_console("stream2")
    assert_that(verbose_logger.console_count, equal_to(0), reason="console_count = 0")


def test_log_no_console(
    verbose_logger: VerboseLoggerType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(verbose_logger, "_verbosity", Verbosity.DEBUG)

    assert_that(
        verbose_logger.effective_verbose,
        equal_to(Verbosity.DEBUG),
        reason="effective_verbose after mock",
    )

    verbose_logger.debug("hello")
    captured = capsys.readouterr()
    assert_that(captured.out, equal_to(""), reason="captured.out")
    assert_that(
        captured.err,
        equal_to("No consoles could be found, log message is omitted\n"),
        reason="captured.err",
    )


def test_log_message_renderable(
    verbose_logger: VerboseLoggerType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from inspect import currentframe, getframeinfo

    console, _ = get_consoles_from_module_storage()

    monkeypatch.setattr(verbose_logger, "_verbosity", Verbosity.DEBUG)
    verbose_logger.add_console("<stdout>", console)

    assert_that(
        verbose_logger.effective_verbose,
        equal_to(Verbosity.DEBUG),
        reason="effective_verbose after mock",
    )
    if not verbose_logger.has_console("<stdout>"):
        verbose_logger.add_console("<stdout>", console)

    current_frame = getframeinfo(currentframe())
    verbose_logger.debug("i am debug")
    captured = capsys.readouterr()
    err = strip_ansi(captured.err)
    out = strip_ansi(captured.out)

    assert_that(err, equal_to(""), reason="captured.err")
    assert_that(out, contains_string("i am debug"), reason="captured.out message")
    expected_link = (
        f"{textualize().to_pathlib(current_frame.filename).name}"
        f":{current_frame.lineno + 1}\n"
    )
    assert_that(out, ends_with(expected_link), reason="captured.out link text")

def test_log_levels(
    log_message: tuple[Verbosity, str],
    expected: Matcher[str],
    verbose_logger: VerboseLoggerType,
    capsys: pytest.CaptureFixture[str],
) -> None:
    c_out, c_err = get_consoles_from_module_storage()
    verbose_logger.add_console("<stdout>", c_out)
    verbose_logger.add_console("<stderr>", c_err)
    assert_that(verbose_logger.console_count, equal_to(2), reason="console_count")

    level, msg = log_message

    if level == Verbosity.DEBUG:
        verbose_logger.debug(msg)
        capsys_out = strip_ansi(capsys.readouterr().out)
        assert_that(capsys_out, expected, reason="debug message")

    elif level == Verbosity.VERY_VERBOSE:
        verbose_logger.info(msg)
        capsys_out = strip_ansi(capsys.readouterr().out)
        assert_that(capsys_out, expected, reason="info message")

    elif level == Verbosity.VERBOSE:
        verbose_logger.warning(msg)
        capsys_out = strip_ansi(capsys.readouterr().out)
        assert_that(capsys_out, expected, reason="warning message")

    elif level == Verbosity.NORMAL:
        verbose_logger.error(msg)
        capsys_err = strip_ansi(capsys.readouterr().err)
        capsys_out = strip_ansi(capsys.readouterr().out)
        assert_that(capsys_err, expected, reason="error message")
        assert_that(capsys_out, equal_to(""), reason="error message prints to stderr")
    else:
        verbose_logger.critical(msg)
        capsys_err = strip_ansi(capsys.readouterr().err)
        capsys_out = strip_ansi(capsys.readouterr().out)
        assert_that(capsys_err, expected, reason="critical message")
        assert_that(capsys_out, equal_to(""), reason="critical message prints to stderr")

def test_log_neutral(
    # log_message: tuple[Verbosity, str],
    # expected: Matcher[str],
    verbose_logger: VerboseLoggerType,
    # capsys: pytest.CaptureFixture[str],
) -> None:
    c_out, c_err = get_consoles_from_module_storage()
    verbose_logger.add_console("<stdout>", c_out)
    verbose_logger.add_console("<stderr>", c_err)
    assert_that(verbose_logger.console_count, equal_to(2), reason="console_count")

    msg = "For each test case, pytest will pass the inputs and expected outputs as arguments to the test function using the names test_input and expected_output."
    # level, msg = log_message

    hook1 = Text("\u2bc0", style="#0098F9")
    hook2 = Text("\u2bc0", style="#0082d6")
    verbose_logger._verbosity = Verbosity.DEBUG
    for i in range(5):
        print()

        # if i == 1:
        #     verbose_logger.prefix = "\u2bc1"
        # if i == 2:
        #     verbose_logger.prefix = "\u2bc0"
        # if i == 3:
        #     verbose_logger.prefix = "\u2bc8"
        verbose_logger.log(msg, verbosity=Verbosity.QUIET, level_text=hook1)
        verbose_logger.debug(msg)
        verbose_logger.log(msg, verbosity=Verbosity.NORMAL, level_text=hook2)
        verbose_logger.info(msg)
        verbose_logger.log(msg, verbosity=Verbosity.VERBOSE, level_text=hook1)
        verbose_logger.warning(msg)
        verbose_logger.log(msg, verbosity=Verbosity.VERY_VERBOSE, level_text=hook2)
        verbose_logger.error(msg)
        verbose_logger.log(msg, verbosity=Verbosity.DEBUG, level_text=hook1)
        verbose_logger.critical(msg)

    pass

def stg_glogging():
    import logging

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # logger.warning("warning message")
    try:
        8 / 0
    except ZeroDivisionError:
        logger.warning("warning message", exc_info=True)
    pass



@pytest.fixture
def data_fixture(request):
    # The request.param contains the value from the parametrize decorator
    if request.param == "scenario_A":
        return {"key": "value_A"}
    elif request.param == "scenario_B":
        return {"key": "value_B"}

# @pytest.mark.parametrize("data_fixture", ["scenario_A", "scenario_B"], indirect=True)
def with_indirect_fixture(data_fixture):
    assert "key" in data_fixture
    assert data_fixture["key"].startswith("value_")
