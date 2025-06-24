from __future__ import annotations

import textwrap
from pathlib import Path
from pprint import saferepr
from typing import Any
from typing import cast

import pytest
from rich import box
from rich.columns import Columns
from rich.console import render_scope
from rich.markup import escape
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text
from rich.traceback import PathHighlighter
from typing_extensions import TYPE_CHECKING
from typing_extensions import assert_never

from pytest_textualize import TextualizePlugins
from pytest_textualize import highlighted_nodeid
from pytest_textualize import hook_msg
from pytest_textualize import key_value_scope
from pytest_textualize import keyval_msg
from pytest_textualize.plugins.pytest_richtrace.base import BaseTextualizePlugin
from pytest_textualize.settings import Verbosity

if TYPE_CHECKING:
    from typing import MutableMapping
    from rich.console import ConsoleRenderable


class TextualizeReporter(BaseTextualizePlugin):
    name = TextualizePlugins.REPORTER

    def __init__(self):
        self._path_highlighter = PathHighlighter()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"


    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        from pytest_textualize import report_pytest_textualize_header

        super().configure(config)

        report_pytest_textualize_header(self.console)

    @pytest.hookimpl
    def pytest_make_collect_report(self, collector: pytest.Collector) -> None:
        if self.verbosity <= Verbosity.VERBOSE or collector.nodeid == "":
            return
        if isinstance(collector, pytest.Session):
            info = f'pytest.Session -> "{collector.nodeid}"'
        elif isinstance(collector, pytest.Directory):
            info = f'pytest.Directory -> "{collector.nodeid}"'
        elif isinstance(collector, pytest.File):
            info = f'pytest.File -> "{collector.nodeid}"'
        else:
            assert_never("unsupported collector")
        hook_msg("pytest_make_collect_report", info=info, console=self.console)

    @pytest.hookimpl
    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        if self.verbosity > Verbosity.NORMAL:
            hook_msg("pytest_collection_modifyitems", console=self.console)

            # -- only on VER_VERBOSE
            if self.verbosity > Verbosity.VERBOSE:
                renderables: list[str] = []
                for i, item in enumerate(items, start=1):
                    renderables.append(f"[#97866A]{i}.[/]{escape(item.name)}")
                self.console.print(
                    Padding(
                        Panel(
                            Columns(renderables, column_first=True, expand=True),
                            title="[#EAE4D5]collection_modifyitems",
                            style="#D29F80",
                            border_style="#735557",
                            box=box.DOUBLE,
                            padding=(1, 0, 0, 1),
                        ),
                        (0, 0, 0, 3),
                    )
                )
        return None

    @pytest.hookimpl
    def pytest_itemcollected(self, item: pytest.Item) -> None:
        if self.verbosity < Verbosity.VERBOSE:
            return None

        node_text = highlighted_nodeid(item)
        hook_msg("pytest_itemcollected", info=node_text, console=self.console, highlight=True)

        if self.verbosity > Verbosity.VERBOSE and hasattr(item, "callspec"):
            import copy

            deep_copied_dict = copy.deepcopy(item.callspec.__dict__)
            r = keyval_msg(
                "pytest.Item.callspec",
                render_scope(
                    dict(
                        params=deep_copied_dict.get("params", {}),
                        indices=deep_copied_dict.get("indices", {}),
                        idlist=deep_copied_dict.get("_idlist", {}),
                        marks=deep_copied_dict.get("marks", {}),
                    ),
                    title="callspec",
                    sort_keys=True,
                ),
                value_style="scope.fill",
                console=self.console,
            )

        markers = list(item.iter_markers())
        skip_markers = ", ".join([mark.name for mark in markers if mark.name.startswith("skip")])
        xfail_markers = ", ".join([mark.name for mark in markers if mark.name.startswith("xfail")])

        from _pytest.skipping import evaluate_skip_marks, evaluate_xfail_marks

        if skip_markers or xfail_markers:
            # self.console.print("markers", style="bright_magenta")
            skipped = evaluate_skip_marks(item)
            if skipped is not None:
                renderables = key_value_scope(
                    [
                        ("type", "[skip]skip[/]"),
                        ("reason", Text(skipped.reason)),
                        ("marker", Text(f"@{skip_markers}", style="#B3AE60")),
                    ]
                )
                self.console.print(renderables)

            xfailed = evaluate_xfail_marks(item)
            if xfailed is not None:
                xfail_list = [
                    ("type", f"[xfail]xfail[/]"),
                    ("reason", Text(xfailed.reason)),
                    ("run", str(xfailed.run)),
                    ("strict", str(xfailed.strict)),
                ]
                if xfailed.raises:
                    xfail_list.append( ("raises", str(xfailed.raises)))
                    xfail_list.append( ("marker", Text(f"@{skip_markers}", style="#B3AE60")))

                renderables = key_value_scope(xfail_list)
                self.console.print(renderables)

        return None

    @pytest.hookimpl(trylast=True)
    def pytest_unconfigure(self) -> None:
        if self.verbosity > Verbosity.NORMAL:
            hook_msg("pytest_unconfigure", console=self.console)
        self.config.pluginmanager.unregister(self, self.name)

    @pytest.hookimpl
    def pytest_render_header(self, config: pytest.Config, data: MutableMapping[str, Any]) -> bool:
        from collections import ChainMap
        from pytest_textualize.textualize.theme.highlighters import ArgparseArgsHighlighter
        from rich.text import Text

        arg_h = ArgparseArgsHighlighter()

        table = Table(
            box=box.HORIZONTALS,
            show_header=False,
            border_style="pytest.table.border",
            expand=True,
        )

        table.add_column(width=25, justify="left", style="pytest.keyname", max_width=25)

        words = lambda x: str(x).replace("_", " ")
        title = lambda x: words(x).title()
        getval = lambda x, y: x.get(y, None)

        chain_map = cast(ChainMap, data)
        for key_name in chain_map.fromkeys(
            ["platform", "poetry_version", "pytest_version", "plugins", "packages"]
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
                        path_highlighter(Text(getval(data, "python_executable"))),
                        end_section=True,
                    )
                    if getval(data, "pypy_version") is not None:
                        table.add_row(
                            title("pypy_version"),
                            Text(getval(data, "pypy_version"), style="pytest.version"),
                            end_section=True,
                        )

                case "poetry_version":
                    table.add_row(
                        title(key_name), Text(getval(data, key_name), style="pytest.version")
                    )
                    table.add_row(
                        title("project_version"),
                        Text(getval(data, "project_version"), style="pytest.version"),
                        end_section=True,
                    )

                case "packages":
                    if self.traceconfig:
                        renderable = render_packages(data.get("packages"))
                        table.add_row("", renderable)

                case "pytest_version":
                    table.add_row(title(key_name), Text(data.get(key_name), style="pytest.version"))
                    table.add_row("rootdir", path_highlighter(getval(data, "rootdir")))
                    table.add_row("configfile", path_highlighter(getval(data, "configfile")))
                    if getval(data, "cachedir") is not None:
                        table.add_row("cachedir", path_highlighter(getval(data, "cachedir")))
                    table.add_row(
                        title("invocation_params"),
                        arg_h(Text(data.get("invocation_params"))),
                    )

                case "plugins":
                    plugins = data.get("plugins")
                    table.add_row(
                        title("pluggy_version"),
                        Text(plugins["pluggy_version"], style="pytest.version"),
                    )
                    if plugins["dist_info"]:
                        renderable = render_registered_plugins(
                            plugins["dist_title"], plugins["dist_info"], self.traceconfig
                        )
                        col_name = ""
                        if not self.traceconfig:
                            col_name = title(plugins["dist_title"])
                            col_name = textwrap.fill(col_name, 24)
                        table.add_row(col_name, renderable)
                    if self.traceconfig:
                        renderable = render_active_plugins(
                            plugins["name_title"], plugins.get("names_info")
                        )
                        table.add_row("", renderable)

                case _:
                    assert_never(key_name)

        table.add_row(
            "",
            render_scope(self.config.inicfg, title="[#4ED7F1]tool.pytest.ini_options[/]"),
            end_section=False,
        )
        table.add_row("", render_options_table(config), end_section=False)
        self.console.print(Padding(table, (0, 0, 0, 2)))
        self.console.line(2)
        return True


def render_registered_plugins(title, dists: list[dict[str, str]], trace: bool) -> ConsoleRenderable:
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

    plugin_renderables = [Panel(get_content(dist), expand=True) for dist in dists]
    return Columns(plugin_renderables)


def render_active_plugins(title, plugins: list[dict[str, str]]) -> ConsoleRenderable:
    from boltons.strutils import multi_replace

    table = _get_plugins_table(title)
    for plugin in plugins:
        p = Path(plugin.get("plugin"))
        if p.is_file():
            path = f"{p.parts[0]}~{p.parent.name}/{p.name}"
            table.add_row(f"[bright_white]{plugin.get("name")}[/]", path_highlighter(path))
        else:
            repr_ = textwrap.shorten(saferepr(plugin.get("plugin")), width=110)
            repr_ = multi_replace(repr_, {"'": "", '"': ""})
            table.add_row(f"[bright_white]{plugin.get("name")}[/]", f"[pytest.text]{repr_}[/]")
    return table


def render_packages(packages: list[dict[str, str]]) -> ConsoleRenderable:
    table = _get_plugins_table("")
    table.title = (
        "available packages [dim i][poetry.actual]actual[/]/[poetry.outdated]outdated[/][/]"
    )
    for package in packages:
        table.add_row(
            f"[poetry.packname ]{package["name"]}[/]",
            f"[poetry.actual]{package["current_ver"]}[/]",
            f"{package["latest_ver"]}",
            f"[poetry.description]{package["summary"]}[/]",
        )
    return table


def render_options_table(config: pytest.Config) -> ConsoleRenderable:
    from itertools import batched

    table = Table(
        box=box.DOUBLE_EDGE,
        title_style="#4ED7F1",
        title="pytest options",
        show_header=True,
        highlight=True,
        expand=True,
        title_justify="left",
        border_style="pytest.table.border",
    )
    table.add_column("option", header_style="pytest.keyname")
    table.add_column("value", header_style="#D0DDD0 b")
    table.add_column("option", header_style="pytest.keyname")
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
            table.add_row(st, st_value, nd, nd_value)

    return table


def _get_plugins_table(title: str | None):
    return Table(
        show_header=False,
        box=box.SQUARE_DOUBLE_HEAD,
        title_justify="left",
        border_style="pytest.table.border",
        title=title,
        title_style="#4ED7F1",
    )
