# Project : pytest-textualize
# File Name : hook_message_tests.py
# Dir Path : tests/rich_tests

from __future__ import annotations

import random
from typing import TYPE_CHECKING
from typing import cast

import pytest
from boltons import strutils
from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import ends_with
from hamcrest import equal_to
from hamcrest import instance_of
from hamcrest import none
from lorem import get_sentence
from lorem import get_word
from rich.color import ANSI_COLOR_NAMES
from rich.table import Table
from rich.text import Text

from helpers import cleaned_dict
from pytest_textualize import PrefixEnum
from pytest_textualize import hook_msg
from pytest_textualize.plugins import skipif_no_console

if TYPE_CHECKING:
    from rich.console import Console

parameterize = pytest.mark.parametrize
param = pytest.param
random.seed()

ANSI_COLOR_KEYS: list[str] = list(ANSI_COLOR_NAMES.keys())

@pytest.fixture(scope="module")
def color_names() -> list[str]:
    return list(ANSI_COLOR_NAMES.keys())

@parameterize("prefix", [None, PrefixEnum.PREFIX_BIG_SQUARE], ids=["x-none", "x-set"])
@parameterize("info", [None, "hello"], ids=["inf-none", "inf-set"])
@parameterize("escape", [None, True], ids=["esc-none", "esc-true"])
@parameterize("highlight", [None, True], ids=["h-none", "h-true"])
def test__init__str(prefix: PrefixEnum | None, info: str | None, escape: bool | None, highlight: bool | None) -> None:

    params = {
        "prefix": prefix,
        "info": info,
        "escape": escape,
        "highlight": highlight,
    }
    tr_msg = hook_msg("pytest_configure", **cleaned_dict(params))
    if prefix is None:
        assert_that(tr_msg.prefix, equal_to(PrefixEnum.PREFIX_SQUARE), reason="prefix default")
    else:
        assert_that(tr_msg.prefix, equal_to(prefix), reason="prefix default")

    if info is None:
        assert_that(tr_msg.info, none(), reason="info none")
    else:
        assert_that(tr_msg.info, equal_to(info), reason="info set")

    if escape is None:
        assert_that(tr_msg.escape, equal_to(False), reason="escape default = True")
    else:
        assert_that(tr_msg.escape, equal_to(True), reason="highlight")

    if highlight is None:
        assert_that(tr_msg.highlight, equal_to(False), reason="highlight default = True")
    else:
        assert_that(tr_msg.highlight, equal_to(True), reason="highlight")



@skipif_no_console
@parameterize(
    "prefix",
    [
        PrefixEnum.PREFIX_SQUARE,
        PrefixEnum.PREFIX_BULLET,
        PrefixEnum.PREFIX_DASH,
        PrefixEnum.PREFIX_BIG_SQUARE,
        PrefixEnum.PREFIX_BIG_CIRCLE,
        PrefixEnum.BLACK_CIRCLE,
        PrefixEnum.LARGE_CIRCLE,
        PrefixEnum.CIRCLED_BULLET,
        PrefixEnum.CIRCLED_WHITE_BULLET,
        PrefixEnum.NARY_BULLET,
    ],
    ids=[
        "prefix_square",
        "prefix_bullet",
        "prefix_dash",
        "prefix_big_square",
        "prefix_big_circle",
        "black_circle",
        "large_circle",
        "circled_bullet",
        "circled_white_bullet",
        "nary_bullet",
    ],
)
def test_different_prefixes(
    request: pytest.FixtureRequest, console: Console | None, prefix: PrefixEnum
) -> None:
    info = f"i am PrefixEnum.'{request.node.callspec.id.upper()}' prefix"
    tr_msg = hook_msg("pytest_configure", info=info, prefix=prefix)
    assert_that(tr_msg.prefix, equal_to(prefix), reason="prefix")
    console.line(1)
    tr_msg(console)


def test__init__str_info(console: Console | None, capsys: pytest.CaptureFixture[str]) -> None:
    str_msg = get_word(2)
    tr_msg = hook_msg("pytest_configure", info=str_msg)
    assert_that(tr_msg.info, equal_to(str_msg), reason="info")
    tr_msg(console)

    if console is not None:
        captured = capsys.readouterr().out
        actual = Text.from_ansi(captured).plain.rstrip()
        assert_that(
            actual,
            ends_with(str_msg),
            reason="clean output with info",
        )

@pytest.mark.skip(reason="not implemented")
def test__init__no_call(capsys: pytest.CaptureFixture[str]) -> None:
    """

    :param capsys: The
    """
    hook_msg("pytest_configure")
    captured = capsys.readouterr().out
    assert_that(captured, equal_to(""), reason="no call")


def test__call__console_none(capsys: pytest.CaptureFixture[str]) -> None:
    """Test __call__ with no console.

    """
    table = hook_msg("pytest_configure", console=None)
    captured = capsys.readouterr().out
    assert_that(captured, equal_to(""), reason="no call")
    assert_that(cast(object, table), instance_of(Table), reason="type(Table)")


@skipif_no_console
def test__call__str_info_markup(
    console: Console | None, capsys: pytest.CaptureFixture[str], color_names: list[str]
) -> None:
    def func(s: str) -> str:
        int_num = random.randint(0, len(color_names) - 1)
        style = color_names[int_num]
        return f"[{style}]{s}[/{style}]"


    str_msg = get_word(2, func=func)
    tr_msg = hook_msg("pytest_configure", info=f"info -> {str_msg}")

    console.line(1)
    tr_msg(console)
    captured = capsys.readouterr().out
    actual = strutils.strip_ansi(captured).strip()
    from_markup = Text.from_markup(str_msg).plain
    assert_that(
        actual,
        ends_with(from_markup),
        reason="captured from_ansi to plain"
    )


@skipif_no_console
def test__call__str_info_markup_printed(console: Console | None) -> None:
    str_msg = get_word(3)
    tr_msg = hook_msg("pytest_configure", info=f"info -> {str_msg}")
    console.line(1)
    tr_msg(console)


@skipif_no_console
def test__call__str_no_escape_no_markup(console: Console | None, capsys: pytest.CaptureFixture[str]) -> None:
    sentence = get_sentence()
    sentence = f"[placeholder]{sentence}"
    tr_msg = hook_msg("pytest_configure", info=sentence)
    console.line(1)
    tr_msg(console)
    captured = capsys.readouterr().out
    actual = strutils.strip_ansi(captured).strip()
    with pytest.raises(AssertionError) as exc_info:
        assert_that(actual, contains_string("[placeholder]"), reason="[placeholder] not escaped")

    assert_that(exc_info.value.args[0].out, contains_string("but: was"), reason="[placeholder] not printed")


@skipif_no_console
def test__call__str_no_escape_w_markups(console: Console | None, capsys: pytest.CaptureFixture[str]) -> None:
    sentence = get_sentence(1)
    sentence = f"[bright_blue][placeholder][/]{sentence}"
    tr_msg = hook_msg("pytest_configure", info=sentence)
    console.line(1)
    tr_msg(console)
    captured = capsys.readouterr().out
    actual = strutils.strip_ansi(captured).strip()
    with pytest.raises(AssertionError) as exc_info:
        assert_that(actual, contains_string("[placeholder]"), reason="[placeholder] not escaped")

    assert_that(exc_info.value.args[0].out, contains_string("but: was"), reason="[placeholder] not printed")


@skipif_no_console
def test__call__str_escape_no_markup(console: Console | None, capsys: pytest.CaptureFixture[str]) -> None:
    sentence = get_word(2)
    sentence = f"[placeholder]{sentence}"
    tr_msg = hook_msg("pytest_configure", info=sentence, escape=True)
    console.line(1)
    tr_msg(console)
    captured = capsys.readouterr().out
    actual = strutils.strip_ansi(captured)
    assert_that(actual, contains_string("[placeholder]"), reason="[placeholder] not escaped")


@skipif_no_console
def test__call__str_highlight(console: Console | None) -> None:
    sentence = "calc: 2 + 2 = 4"
    tr_msg = hook_msg("pytest_configure", info=sentence, highlight=True)
    console.line(1)
    tr_msg(console)


@skipif_no_console
def test_with_text_objects_un_styled(console: Console | None) -> None:
    info = Text(get_sentence(1))
    tr_msg = hook_msg("pytest_configure", info=info)
    if console:
        console.line(1)
        tr_msg(console)


@skipif_no_console
def test_with_text_objects_styled(console: Console | None) -> None:
    info = Text(get_sentence(1), style="#C599B6")
    tr_msg = hook_msg("pytest_configure", info=info)
    if console:
        console.line(1)
        tr_msg(console)


@skipif_no_console
def test_with_text_objects_un_styled_highlight(console: Console | None) -> None:
    info = Text("calc: 2 + 2 = 4")
    tr_msg = hook_msg("pytest_configure", info=info, highlight=True)
    if console:
        console.line(1)
        tr_msg(console)




#

#
# def test_styles_for_hook_message(console: Console) -> None:
#     theme_eight = Theme(
#         {
#             "args": Style(color=Color.from_ansi(230), bold=True, dim=True),
#             "text": Style(color=Color.from_ansi(231), dim=True),
#             "groups": Style(color=Color.from_ansi(231)),
#             "help": Style(color=Color.from_ansi(230), italic=True),
#             "metavar": Style(color=Color.from_ansi(184)),
#             "prog": Style(color=Color.from_ansi(208), bold=True),
#             "syntax": Style(color=Color.from_ansi(190), bold=True),
#             "add_enum": Style(color=Color.from_ansi(153), bold=False),
#             "help2": Style(color=Color.from_ansi(144)),
#             "groups2": Style(color=Color.from_ansi(138), dim=True),
#             "args2": Style(color=Color.from_ansi(153), bold=True),
#             "text2": Style(color=Color.from_ansi(144)),
#         }
#     )
#     theme_true = Theme(
#         {
#             "BLUE5": Style(color=Color.parse("#B3C8CF")),
#             "BLUE6": Style(color=Color.parse("#51829B")),
#             "BLUE7": Style(color=Color.parse("#F2F2F2")),
#             "BLUE8": Style(color=Color.parse("#C2D0E9")),
#             "BLUE9": Style(color=Color.parse("#91ACDF")),
#             "BLUE10": Style(color=Color.parse("#EEE9DA")),
#             "BLUE11": Style(color=Color.parse("#BDCDD6")),
#             "BLUE12": Style(color=Color.parse("#93BFCF")),
#             "BLUE13": Style(color=Color.parse("#6096B4")),
#             "BLUE13B": Style(color=Color.parse("#6096B4"), bold=True),
#             "BLUE13I": Style(color=Color.parse("#6096B4"), italic=True),
#             "BLUE13IB": Style(color=Color.parse("#6096B4"), italic=True, bold=True),
#         }
#     )
#     # with open("C:/Users/solma/PycharmProjects/pytest-textualize/static/styles/truecolor_styles.ini",
#     #           "wt") as write_theme:
#     #     write_theme.write(theme_true.config)
#     # pass
#
#     BLUE5 = Style(color=Color.parse("#B3C8CF"))
#     BLUE6 = Style(color=Color.parse("#51829B"))
#     BLUE7 = Style(color=Color.parse("#f2f2f2"))
#     BLUE8 = Style(color=Color.parse("#c2d0e9"))
#     BLUE9 = Style(color=Color.parse("#91ACDF"))
#     BLUE10 = Style(color=Color.parse("#EEE9DA"))
#     BLUE11 = Style(color=Color.parse("#BDCDD6"))
#     BLUE12 = Style(color=Color.parse("#93BFCF"))
#     BLUE13 = Style(color=Color.parse("#6096B4"))
#
#     LGREEN1 = Style(color=Color.parse("#B0DB9C"))
#     LGREEN2 = Style(color=Color.parse("#CAE8BD"))
#     LGREEN3 = Style(color=Color.parse("#DDF6D2"))
#     LGREEN4 = Style(color=Color.parse("#ECFAE5"))
#
#     PASTEL1 = Style(color=Color.parse("#727D73"))
#     PASTEL2 = Style(color=Color.parse("#AAB99A"))
#     PASTEL3 = Style(color=Color.parse("#D0DDD0"))
#     PASTEL4 = Style(color=Color.parse("#F0F0D7"))
#     PASTEL5 = Style(color=Color.parse("#99BC85"))
#     PASTEL6 = Style(color=Color.parse("#BFD8AF"))
#     PASTEL7 = Style(color=Color.parse("#D4E7C5"))
#     PASTEL8 = Style(color=Color.parse("#E1F0DA"))
#     PASTEL9 = Style(color=Color.parse("#A4BC92"))
#     PASTEL10 = Style(color=Color.parse("#B3C99C"))
#     PASTEL11 = Style(color=Color.parse("#C7E9B0"))
#     PASTEL12 = Style(color=Color.parse("#C7E9B0"))
#     PASTEL13 = Style(color=Color.parse("#DDFFBB"))
#
#     if console:
#         console.line(2)
#         console.rule("Green combinations")
#         console.print(LOREM_SHORT, style=BLUE5)
#         console.print(LOREM_SHORT, style=BLUE6)
#         console.print(LOREM_SHORT, style=BLUE6)
#         console.print(LOREM_SHORT, style=BLUE7)
#         console.print(LOREM_SHORT, style=BLUE8)
#         console.print(LOREM_SHORT, style=BLUE9)
#         console.print(LOREM_SHORT, style=BLUE10)
#         console.print(LOREM_SHORT, style=BLUE11)
#         console.print(LOREM_SHORT, style=BLUE12)
#         console.print(LOREM_SHORT, style=BLUE13)
#         console.rule("Green combinations")
#         console.print(LOREM_SHORT, style=LGREEN1)
#         console.print(LOREM_SHORT, style=LGREEN2)
#         console.print(LOREM_SHORT, style=LGREEN3)
#         console.print(LOREM_SHORT, style=LGREEN4)
#
#         console.rule("Pastel combinations")
#         console.print(LOREM_SHORT, style=PASTEL1)
#         console.print(LOREM_SHORT, style=PASTEL2)
#         console.print(LOREM_SHORT, style=PASTEL3)
#         console.print(LOREM_SHORT, style=PASTEL4)
#         console.print(LOREM_SHORT, style=PASTEL5)
#         console.print(LOREM_SHORT, style=PASTEL6)
#         console.print(LOREM_SHORT, style=PASTEL7)
#         console.print(LOREM_SHORT, style=PASTEL8)
#         console.print(LOREM_SHORT, style=PASTEL9)
#         console.print(LOREM_SHORT, style=PASTEL10)
#         console.print(LOREM_SHORT, style=PASTEL11)
#         console.print(LOREM_SHORT, style=PASTEL12)
#         console.print(LOREM_SHORT, style=PASTEL13)
#
#
# def test_load_from_file(console: Console):
#     load_theme = Theme.read(
#         "C:/Users/solma/PycharmProjects/pytest-textualize/static/styles/truecolor_styles.ini"
#     )
#
#     y = 0
