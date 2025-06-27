from __future__ import annotations


__all__ = (
    "PrefixEnum", "hook_msg", "keyval_msg",
           "stage_rule", "report_pytest_textualize_header", "highlighted_nodeid",
    "key_value_scope"
)

from typing import TYPE_CHECKING


from pytest_textualize.textualize.console import PrefixEnum
from pytest_textualize.textualize.console import highlighted_nodeid
from pytest_textualize.textualize.console import key_value_scope
from pytest_textualize.textualize.console import pytest_textualize_header as report_pytest_textualize_header
from pytest_textualize.textualize.console import stage_rule

if TYPE_CHECKING:
    from rich.style import StyleType
    from rich.text import TextType
    from pytest_textualize.textualize.verbose_log import Verbosity
    from rich.console import ConsoleRenderable


def hook_msg(
    hookname: str,
    *,
    prefix: PrefixEnum = PrefixEnum.PREFIX_SQUARE,
    info: TextType | None = None,
    escape: bool = False
) -> list[str] | None:
    from pytest_textualize.textualize.console import TracerMessage
    trm = TracerMessage(hookname, prefix=prefix, info=info, escape=escape)
    return trm(None)


def keyval_msg(
        key: str,
        value: TextType | ConsoleRenderable,
        *,
        prefix: PrefixEnum = PrefixEnum.PREFIX_BULLET,
        value_style: StyleType | None = "",
        escape: bool = False,
        highlight: bool = False,
) -> list[str]:
    from pytest_textualize.textualize.console import KeyValueMessage
    kvm = KeyValueMessage(key, value, prefix=prefix, value_style=value_style, highlight=highlight, escape=escape)
    return kvm(None)
