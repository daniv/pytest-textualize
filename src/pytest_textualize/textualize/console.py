from __future__ import annotations

from typing import Annotated
from typing import Optional
from typing import TYPE_CHECKING

from pydantic import StringConstraints
from pydantic import TypeAdapter
from rich import box
from rich.padding import Padding
from rich.table import Column
from rich.table import Table
from rich.text import Text

from pytest_textualize.factories.theme_factory import ThemeFactory

if TYPE_CHECKING:
    from collections.abc import Iterable
    from rich.text import TextType
    from rich.style import StyleType
    from rich.console import ConsoleRenderable
    from rich.console import RenderableType
    from pytest_textualize.typist import TextAlias


def is_markup(string: str) -> bool:
    if string:
        text = Text.from_markup(string)
        return len(text.spans) > 0
    return False


class KeyValueMessage:
    def __init__(
        self,
        key_name: str,
        key_value: TextType | ConsoleRenderable,
        *,
        level: Optional[str] = None,
        kv_separator: Optional[str] = None,
        value_style: Optional[StyleType] = "",
        highlight: bool = False,
    ) -> None:
        level = level or "\u2237"
        kv_separator = kv_separator or chr(0x2502)
        self.key_name = key_name
        self.key_value = key_value
        self.value_style = value_style
        self.value = key_value
        self.highlight = highlight

        validator = Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1)
        ]
        self.level = TypeAdapter(validator).validate_python(level)
        self.kv_separator = TypeAdapter(validator).validate_python(kv_separator)

    def __call__(self) -> tuple[TextAlias, TextAlias, TextAlias]:
        value = Text()

        level = Text(self.level.rjust(9), style="#B0D9B1")
        key = Text(self.key_name.ljust(20), style="#CBFFA9").append(self.kv_separator, style="none")

        if isinstance(self.value, str):
            if is_markup(self.value):
                v = Text.from_markup(self.value)
            else:
                v = Text(self.value, style=self.value_style)
            if self.highlight:
                repr_h = ThemeFactory.repr_highlighter()
                value.append_text(repr_h(v))
            else:
                value.append(self.value, style=self.value_style)
        else:
            value.append(self.value)

        return key, value, level


def key_value_scope(items: Iterable[tuple[str, RenderableType]]) -> RenderableType:
    table = Table.grid(
        Column("name", style="#8DECB4 i", width=15),
        Column("value", style="#F6F0F0", width=61),
        padding=(0, 1),
        expand=True,
    )
    # a2e2f8
    table.box = box.HEAVY_HEAD
    table.style = "#BDB395 dim"
    for item in items:
        k, v = item

        table.add_row(f" - {k}", v)
    return Padding(table, (0, 0, 0, 6))
