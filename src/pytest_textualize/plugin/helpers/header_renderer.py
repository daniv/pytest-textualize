from __future__ import annotations

import textwrap
from pathlib import Path
from pprint import saferepr
from typing import Any
from typing import ChainMap
from typing import TYPE_CHECKING
from typing import assert_never
from typing import cast

import pytest
from rich import box
from rich.columns import Columns
from rich.panel import Panel
from rich.pretty import Pretty
from rich.scope import render_scope
from rich.table import Table
from rich.text import Text

from pytest_textualize.factories.theme_factory import ThemeFactory

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from pytest_textualize.typist import TableType
    from rich.console import ConsoleRenderable


def header_console_renderable(config: pytest.Config, data: MutableMapping[str, Any]) -> TableType:
    argparse_h = ThemeFactory.argparse_highlighter()
    path_h = ThemeFactory.path_highlighter()
    traceconfig = config.option.traceconfig

    words = lambda x: str(x).replace("_", " ")
    title = lambda x: words(x).title()
    getval = lambda x, y: x.get(y, None)

    chain_map = cast(ChainMap, data)
    table = Table(
        box=box.HORIZONTALS,
        show_header=False,
        border_style="scope.border",
        expand=True,
    )
    table.add_column(width=25, justify="left", style="#B0DB9C", max_width=25)

    for key_name in chain_map.fromkeys(
        ["platform", "textualize_version", "pytest_version", "plugins", "packages"]
    ):
        if data.get(key_name) is None:
            continue
        match key_name:

            case "platform":
                table.add_row(title(key_name), f"[pytest.description]{data.get(key_name)}[/]")
                table.add_row(
                    title("python_version"),
                    Text(getval(data, "python_version"), style="pytest.version"),
                )
                table.add_row(
                    title("python_ver_info"),
                    Text(getval(data, "python_ver_info"), style="pytest.version"),
                )
                table.add_row(
                    title("python_executable"),
                    path_h(Text(getval(data, "python_executable"))),
                    end_section=True,
                )
                if getval(data, "pypy_version") is not None:
                    table.add_row(
                        title("pypy_version"),
                        Text(getval(data, "pypy_version"), style="pytest.version"),
                        end_section=True,
                    )

            case "textualize_version":
                table.add_row(title(key_name), Text(getval(data, key_name), style="pytest.version"))
                table.add_row(
                    title("poetry_version"),
                    Text(getval(data, "poetry_version"), style="pytest.version"),
                    end_section=True,
                )

            case "packages":
                renderable = render_packages(data.get("packages"))
                table.add_row("", renderable)

            case "pytest_version":
                table.add_row(title(key_name), Text(data.get(key_name), style="pytest.version"))
                table.add_row("rootdir", path_h(getval(data, "rootdir")))
                table.add_row("configfile", path_h(getval(data, "configfile")))
                if getval(data, "cachedir") is not None:
                    table.add_row("cachedir", path_h(getval(data, "cachedir")))
                table.add_row(
                    title("invocation_params"),
                    argparse_h(Text(data.get("invocation_params"))),
                )

            case "plugins":
                plugins = data.get("plugins")
                table.add_row(
                    title("pluggy_version"),
                    Text(plugins["pluggy_version"], style="pytest.version"),
                )
                if plugins["dist_info"]:
                    renderable = render_registered_plugins(
                        plugins["dist_title"], plugins["dist_info"], traceconfig
                    )
                    col_name = ""
                    if not traceconfig:
                        col_name = title(plugins["dist_title"])
                        col_name = textwrap.fill(col_name, 24)
                    table.add_row(col_name, renderable)
                if traceconfig:
                    renderable = render_active_plugins(
                        plugins["name_title"], plugins.get("names_info")
                    )
                    table.add_row("", renderable)
            case _:
                assert_never(key_name)

    table.add_row(
        "",
        render_scope(config.inicfg, title="[#4ED7F1]tool.pytest.ini_options[/]"),
        end_section=False,
    )
    table.add_row("", render_options_table(config), end_section=False)
    return table


def render_registered_plugins(title, dists: list[dict[str, str]], trace: bool) -> ConsoleRenderable:
    path_highlighter = ThemeFactory.path_highlighter()

    if trace:
        table = _get_plugins_table(title)
        for d in dists:
            p = Path(d.get("plugin"))
            pack = f"{p.parts[0]}~{p.parent.name}/{p.name}"
            table.add_row(
                f"[pytest.name]{d.get("name")}[/]",
                f"[pytest.version]{d.get("version")}[/]",
                path_highlighter(pack),
                d.get("summary"),
            )
        return table

    def get_content(dist_info: dict[str, str]):
        return Text.from_markup(
            f"[pytest.name]{dist_info['name']}[/]\n[pytest.version]{dist_info['version']}[/]",
            justify="center",
        )

    plugin_renderables = [
        Panel(get_content(dist), expand=True, border_style="scope.border") for dist in dists
    ]
    return Columns(plugin_renderables)


def render_active_plugins(title, plugins: list[dict[str, str]]) -> ConsoleRenderable:
    from boltons.strutils import multi_replace

    path_highlighter = ThemeFactory.path_highlighter()

    table = _get_plugins_table(title)
    for plugin in plugins:
        p = Path(plugin.get("plugin"))
        if p.is_file():
            path = f"{p.parts[0]}~{p.parent.name}/{p.name}"
            table.add_row(f"[scope.key_ni]{plugin.get("name")}[/]", path_highlighter(path))
        else:
            repr_ = textwrap.shorten(saferepr(plugin.get("plugin")), width=110)
            repr_ = multi_replace(repr_, {"'": "", '"': ""})
            table.add_row(
                f"[scope.key_ni]{plugin.get("name")}[/]", f"[poetry.description]{repr_}[/]"
            )
    return table


def render_packages(packages: list[dict[str, str]]) -> ConsoleRenderable:
    table = _get_plugins_table("")
    table.title = (
        "available packages [dim i][poetry.actual]actual[/]/[poetry.outdated]outdated[/][/]"
    )
    for package in packages:
        table.add_row(
            f"[poetry.packname]{package["name"]}[/]",
            f"[poetry.actual]{package["current_ver"]}[/]",
            f"{package["latest_ver"]}",
            f"[poetry.description]{package["summary"]}[/]",
        )
    return table


def render_options_table(config: pytest.Config) -> ConsoleRenderable:
    from itertools import batched

    path_highlighter = ThemeFactory.path_highlighter()

    table = Table(
        box=box.DOUBLE_EDGE,
        title_style="#4ED7F1",
        title="pytest options",
        show_header=True,
        highlight=True,
        expand=True,
        title_justify="left",
        border_style="scope.border",
    )
    table.add_column("option", header_style="#A7C1A8")
    table.add_column("value", header_style="#D0DDD0 b")
    table.add_column("option", header_style="#A7C1A8")
    table.add_column("value", header_style="#D0DDD0 b")

    options = vars(config.option)
    keys = sorted(options.keys())

    def render_value(key: str, v: Any) -> str | ConsoleRenderable:
        if isinstance(v, str):
            return f'"{v}"'
        if isinstance(v, list):
            if key == "file_or_dir":
                v = list(
                    map(lambda x: Path(x).resolve().relative_to(config.rootpath).as_posix(), v)
                )
                return Pretty(v, overflow="fold", insert_line=True, highlighter=path_highlighter)
            else:
                return Pretty(v, overflow="fold", insert_line=True)
        else:
            return str(v)

    for pair in batched(keys, 2):
        if len(pair) == 1:
            st = pair[0]
            st_value = render_value(st, options[st])
            table.add_row(st, st_value)
        else:
            st, nd = pair
            st_value = render_value(st, options[st])
            nd_value = render_value(nd, options[nd])
            pass
            table.add_row(
                Text(st, style="scope.key"), st_value, Text(nd, style="scope.key"), nd_value
            )

    return table


def _get_plugins_table(title: str | None):
    return Table(
        show_header=False,
        box=box.SQUARE_DOUBLE_HEAD,
        title_justify="left",
        border_style="scope.border",
        title=title,
        title_style="#4ED7F1",
    )
