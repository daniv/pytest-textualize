# Project : pytest-textualize
# File Name : hook_message_tests.py
# Dir Path : tests/rich_tests

from __future__ import annotations

from enum import StrEnum
from typing import Any
from typing import Self
from typing import Sized
from typing import TYPE_CHECKING
from typing import Type
from typing import TypeVar

import pytest
from attr import dataclass
from hamcrest import assert_that
from hamcrest import equal_to
from hamcrest import none
from rich.color import Color
from rich.console import HighlighterType
from rich.console import RenderResult
from rich.style import Style
from rich.text import Text
from rich.text import TextType
from rich.theme import Theme
from rich.traceback import PathHighlighter

from rich_tests import LOREM_SHORT

if TYPE_CHECKING:
    from rich.console import Console, ConsoleOptions

parameterize = pytest.mark.parametrize
SizedT = TypeVar("SizedT", bound=Sized)

THEME = Theme(
    {
        "pytest.prefix": Style(color=Color.parse("#B33791")),
        "pytest.hook": Style(color=Color.parse("#C562AF")),
        "pytest.hookname": Style(color=Color.parse("#DB8DD0"), italic=True),
        "pytest.colon": Style(conceal=True),
        "pytest.najshov": Style(color=Color.parse("#FEC5F6")),
        "pytest.msg": Style(color=Color.from_ansi(231), dim=True),
    },
    inherit=False,
)


class PrefixEnum(StrEnum):
    PREFIX_SQUARE = " ▪ "
    PREFIX_BULLET = " • "
    PREFIX_DASH = " - "
    PREFIX_BIG_SQUARE = " ■ "
    PREFIX_BIG_CIRCLE = " ⬤ "
    BLACK_CIRCLE = " ● "
    LARGE_CIRCLE = " ○ "
    MEDIUM_SMALL_WHITE_CIRCLE = " ⚬ "
    CIRCLED_BULLET = " ⦿ "
    CIRCLED_WHITE_BULLET = " ⦾ "
    NARY_BULLET = " ⨀ "


@dataclass(repr=False, frozen=True)
class ReportItem:
    name: str
    type: Type[Any]
    value: Any

    def __repr__(self) -> str:
        return f"ReportItem({self.name!r}, type={self.type!r})"


@dataclass
class ReportItemGroup:
    name: str
    group_tems: list[ReportItem] = []

    def add_report_item(self, item: ReportItem) -> Self:
        self.group_tems.append(item)
        return self


class HookMessage:
    def __init__(
            self,
            hookname: str,
            *,
            info: TextType | None = None,
            prefix: PrefixEnum = PrefixEnum.PREFIX_SQUARE,
            highlighter: HighlighterType | None = None,
            escape: bool = False,
    ) -> None:
        self.hookname = hookname
        self.prefix = prefix
        self.info = info
        self.highlighter = highlighter
        self.escape = escape

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:

        yield Text.assemble(
            (f"{self.prefix}", "pytest.prefix"),
            ("hook", "pytest.hook"),
            (": ", "pytest.colon"),
            (self.hookname.ljust(30), "pytest.hookname"),
            end=" ",
        )
        if self.info and isinstance(self.info, str):
            info = self.info
            if self.escape:
                from rich.markup import escape

                yield escape(info)

            elif self.highlighter:
                yield Text.assemble(self.highlighter(info))
            else:
                yield Text.assemble(info, style="pytest.msg")

        yield "\n"


@pytest.fixture(scope="function", autouse=True)
def push_theme(console: Console) -> None:
    console.push_theme(THEME, inherit=False)
    yield
    console.pop_theme()


def test_hook_msg_default_builder(console: Console) -> None:
    hm = HookMessage("pytest_configure")

    assert_that(hm.hookname, equal_to("pytest_configure"), reason="hookname")
    assert_that(hm.info, none(), reason="info")
    assert_that(hm.prefix, equal_to(PrefixEnum.PREFIX_SQUARE), reason="info")
    assert_that(hm.highlighter, none(), reason="info")
    assert_that(hm.escape, equal_to(False), reason="info")
    assert_that(hm.info, none(), reason="info str")
    if console:
        console.line(2)
        console.print(hm)


def test_hook_msg_default_add_plain_info_str(console: Console) -> None:
    info = "the sum of 3 + 5 is=8 'yeah!'"
    hm = HookMessage("pytest_configure", info=info)
    assert_that(hm.info, equal_to(info), reason="info")
    if console:
        console.line(2)
        console.print(hm)


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
        PrefixEnum.MEDIUM_SMALL_WHITE_CIRCLE,
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
        "medium_small_white_circle",
        "circled_bullet",
        "circled_white_bullet",
        "nary_bullet",
    ],
)
def test_different_prefixes(
        request: pytest.FixtureRequest, console: Console, prefix: PrefixEnum
) -> None:
    info = f"i am PrefixEnum.'{request.node.callspec.id.upper()}' prefix"
    hm = HookMessage("pytest_configure", info=info, prefix=prefix)
    assert_that(hm.prefix, equal_to(prefix), reason="prefix")
    if console:
        console.line(2)
        console.print(hm, markup=True)


def test_with_text_objects_un_styled(console: Console) -> None:
    info = Text("the sum of 3 + 5 is=8 'yeah!'")
    hm = HookMessage("pytest_configure", info=info)
    if console:
        console.line(2)
        console.print(hm)


def test_with_text_styled_objects(console: Console) -> None:
    info = Text("the sum of 3 + 5 is=8 'yeah!'", style="bright_yellow")
    hm = HookMessage("pytest_configure", info=info)
    if console:
        console.line(2)
        console.print(hm)


def test_with_highlighter(console: Console) -> None:
    info = "test-textualize/.venv/Lib/site-packages/rich/_log_render.py"
    console.print(info)
    hm = HookMessage("pytest_configure", info=info, highlighter=PathHighlighter())
    if console:
        console.line(2)
        console.print(hm)


def test_with_escape(console: Console) -> None:
    info = "this [type] of message not markup[/]"
    console.print(info)
    hm = HookMessage("pytest_configure", info=info, escape=True)
    if console:
        console.line(2)
        console.print(hm)


def test_hook_msg_default_add_plain_info_str_with_markup(console: Console) -> None:
    info = "the [bright_yellow]sum[/] of [b]3[/] + 5 is=8 'yeah!'"

    hm = HookMessage("pytest_configure", info=info)
    if console:
        console.line(2)
        console.print(hm)


def test_styles_for_hook_message(console: Console) -> None:
    theme_eight = Theme(
        {
            "args": Style(color=Color.from_ansi(230), bold=True, dim=True),
            "text": Style(color=Color.from_ansi(231), dim=True),
            "groups": Style(color=Color.from_ansi(231)),
            "help": Style(color=Color.from_ansi(230), italic=True),
            "metavar": Style(color=Color.from_ansi(184)),
            "prog": Style(color=Color.from_ansi(208), bold=True),
            "syntax": Style(color=Color.from_ansi(190), bold=True),
            "add_enum": Style(color=Color.from_ansi(153), bold=False),
            "help2": Style(color=Color.from_ansi(144)),
            "groups2": Style(color=Color.from_ansi(138), dim=True),
            "args2": Style(color=Color.from_ansi(153), bold=True),
            "text2": Style(color=Color.from_ansi(144)),
        }
    )
    theme_true = Theme(
        {
            "BLUE5": Style(color=Color.parse("#B3C8CF")),
            "BLUE6": Style(color=Color.parse("#51829B")),
            "BLUE7": Style(color=Color.parse("#F2F2F2")),
            "BLUE8": Style(color=Color.parse("#C2D0E9")),
            "BLUE9": Style(color=Color.parse("#91ACDF")),
            "BLUE10": Style(color=Color.parse("#EEE9DA")),
            "BLUE11": Style(color=Color.parse("#BDCDD6")),
            "BLUE12": Style(color=Color.parse("#93BFCF")),
            "BLUE13": Style(color=Color.parse("#6096B4")),
            "BLUE13B": Style(color=Color.parse("#6096B4"), bold=True),
            "BLUE13I": Style(color=Color.parse("#6096B4"), italic=True),
            "BLUE13IB": Style(color=Color.parse("#6096B4"), italic=True, bold=True),
        }
    )
    # with open("C:/Users/solma/PycharmProjects/pytest-textualize/static/styles/truecolor_styles.ini",
    #           "wt") as write_theme:
    #     write_theme.write(theme_true.config)
    # pass

    BLUE5 = Style(color=Color.parse("#B3C8CF"))
    BLUE6 = Style(color=Color.parse("#51829B"))
    BLUE7 = Style(color=Color.parse("#f2f2f2"))
    BLUE8 = Style(color=Color.parse("#c2d0e9"))
    BLUE9 = Style(color=Color.parse("#91ACDF"))
    BLUE10 = Style(color=Color.parse("#EEE9DA"))
    BLUE11 = Style(color=Color.parse("#BDCDD6"))
    BLUE12 = Style(color=Color.parse("#93BFCF"))
    BLUE13 = Style(color=Color.parse("#6096B4"))

    LGREEN1 = Style(color=Color.parse("#B0DB9C"))
    LGREEN2 = Style(color=Color.parse("#CAE8BD"))
    LGREEN3 = Style(color=Color.parse("#DDF6D2"))
    LGREEN4 = Style(color=Color.parse("#ECFAE5"))

    PASTEL1 = Style(color=Color.parse("#727D73"))
    PASTEL2 = Style(color=Color.parse("#AAB99A"))
    PASTEL3 = Style(color=Color.parse("#D0DDD0"))
    PASTEL4 = Style(color=Color.parse("#F0F0D7"))
    PASTEL5 = Style(color=Color.parse("#99BC85"))
    PASTEL6 = Style(color=Color.parse("#BFD8AF"))
    PASTEL7 = Style(color=Color.parse("#D4E7C5"))
    PASTEL8 = Style(color=Color.parse("#E1F0DA"))
    PASTEL9 = Style(color=Color.parse("#A4BC92"))
    PASTEL10 = Style(color=Color.parse("#B3C99C"))
    PASTEL11 = Style(color=Color.parse("#C7E9B0"))
    PASTEL12 = Style(color=Color.parse("#C7E9B0"))
    PASTEL13 = Style(color=Color.parse("#DDFFBB"))

    if console:
        console.line(2)
        console.rule("Green combinations")
        console.print(LOREM_SHORT, style=BLUE5)
        console.print(LOREM_SHORT, style=BLUE6)
        console.print(LOREM_SHORT, style=BLUE6)
        console.print(LOREM_SHORT, style=BLUE7)
        console.print(LOREM_SHORT, style=BLUE8)
        console.print(LOREM_SHORT, style=BLUE9)
        console.print(LOREM_SHORT, style=BLUE10)
        console.print(LOREM_SHORT, style=BLUE11)
        console.print(LOREM_SHORT, style=BLUE12)
        console.print(LOREM_SHORT, style=BLUE13)
        console.rule("Green combinations")
        console.print(LOREM_SHORT, style=LGREEN1)
        console.print(LOREM_SHORT, style=LGREEN2)
        console.print(LOREM_SHORT, style=LGREEN3)
        console.print(LOREM_SHORT, style=LGREEN4)

        console.rule("Pastel combinations")
        console.print(LOREM_SHORT, style=PASTEL1)
        console.print(LOREM_SHORT, style=PASTEL2)
        console.print(LOREM_SHORT, style=PASTEL3)
        console.print(LOREM_SHORT, style=PASTEL4)
        console.print(LOREM_SHORT, style=PASTEL5)
        console.print(LOREM_SHORT, style=PASTEL6)
        console.print(LOREM_SHORT, style=PASTEL7)
        console.print(LOREM_SHORT, style=PASTEL8)
        console.print(LOREM_SHORT, style=PASTEL9)
        console.print(LOREM_SHORT, style=PASTEL10)
        console.print(LOREM_SHORT, style=PASTEL11)
        console.print(LOREM_SHORT, style=PASTEL12)
        console.print(LOREM_SHORT, style=PASTEL13)


def test_load_from_file(console: Console):
    load_theme = Theme.read(
        "C:/Users/solma/PycharmProjects/pytest-textualize/static/styles/truecolor_styles.ini"
    )

    y = 0
