# Project : pytest-textualize
# File Name : textualize_reporte py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/richtrace
from __future__ import annotations

import sys
import textwrap
import threading

from functools import cached_property
from pathlib import Path
from pprint import saferepr
from typing import Any
from typing import ClassVar
from typing import cast


from rich.traceback import PathHighlighter
from rich.text import Text
from rich.table import Table
from rich import box
from rich.pretty import Pretty
from rich.padding import Padding
from rich.panel import Panel
from rich.columns import Columns

import pytest
from typing_extensions import TYPE_CHECKING
from typing_extensions import assert_never

from pytest_textualize.plugins.pytest_richtrace import console_key
from pytest_textualize.settings import Verbosity
from pytest_textualize.settings import settings_key
from pytest_textualize.textualize.hook_message import KeyValueMessage
from pytest_textualize.textualize.hook_message import tracer_message

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import MutableMapping
    from rich.console import Console
    from pytest_textualize.plugins import PytestPlugin
    from pytest_textualize import TextualizeSettings
    from rich.console import ConsoleRenderable

path_highlighter = PathHighlighter()


class TextualizeReporter:
    name = "pytest-textualize-reporter"

    monitored_classes: ClassVar[list[str]] = []

    def __init__(self, config: pytest.Config):
        self.config = config
        self.console: Console = config.stash.get(console_key, None)
        self.settings: TextualizeSettings = config.stash.get(settings_key, None)
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"

    @property
    def traceconfig(self) -> bool:
        return self.config.option.traceconfig

    @property
    def verbosity(self) -> Verbosity:
        verbose = self.config.option.verbose
        return Verbosity(verbose)

    @cached_property
    def isatty(self) -> bool:
        return sys.stdin.isatty()

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        from pytest_textualize.settings import settings_key
        from pytest_textualize.plugins.pytest_richtrace import console_key

        self.monitored_classes.append(self.name)
        self.settings = config.stash.get(settings_key, None)
        self.console = config.stash.get(console_key, None)
        from pytest_textualize import __version__

        panel = Panel(
            Text(
                "A pytest plugin using Rich for beautiful test result formatting.",  # noqa: E501
                justify="center",
            ),
            box=box.ROUNDED,
            style="pytest.panel.border",
            padding=2,
            title="[#4da8da]pytest-textualize plugin[/]",
            subtitle=f"[#A9C46C]v{__version__}[/]",
        )
        self.console.print(panel)

    @pytest.hookimpl
    def pytest_addhooks(self, pluginmanager: pytest.PytestPluginManager) -> None:
        from pytest_textualize.plugins.pytest_richtrace.hookspecs import ReportingHookSpecs

        pluginmanager.add_hookspecs(ReportingHookSpecs)

    @pytest.hookimpl(trylast=True)
    def pytest_plugin_registered(self, plugin: PytestPlugin, plugin_name: str) -> None:
        if plugin_name is None:
            return None

        if self.config.option.traceconfig:
            tm = tracer_message("pytest_plugin_registered", info=plugin_name)
            with self._lock:
                tm(self.console)
        elif plugin_name in self.monitored_classes:
            tm = tracer_message("pytest_plugin_registered", info=plugin_name)
            with self._lock:
                tm(self.console)
        return None

    @pytest.hookimpl
    def pytest_plugin_unregistered(self, plugin: PytestPlugin) -> None:
        if self.verbosity > Verbosity.NORMAL:
            if hasattr(plugin, "name"):
                trm = tracer_message("pytest_plugin_unregistered", info=getattr(plugin, "name"))
            else:
                trm = tracer_message("pytest_plugin_unregistered", info=saferepr(plugin))
            trm(self.console)

    @pytest.hookimpl
    def pytest_make_collect_report(self, collector: pytest.Collector) -> None:
        if self.verbosity < Verbosity.VERBOSE or collector.nodeid == "":
            return
        if isinstance(collector, pytest.Session):
            info = f"pytest.Session -> \"{collector.nodeid}\""
        elif isinstance(collector, pytest.Directory):
            info = f"pytest.Directory -> \"{collector.nodeid}\""
        elif isinstance(collector, pytest.File):
            info = f"pytest.File -> \"{collector.nodeid}\""
        else:
            assert_never("unsupported collector")
        hm = tracer_message("pytest_make_collect_report", info=info)
        hm(self.console)




    @pytest.hookimpl
    def pytest_collection_modifyitems(
        self, session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
    ) -> None:
        if self.verbosity > Verbosity.NORMAL:
            trm = tracer_message("pytest_report_collection_modifyitems")
            trm(self.console)

            # self.console.print(f"{INDENT}[keyname]items[/]:")
            item_text = "\n".join([f.name for f in items]).replace("[", "\\[")
            if item_text:
                pass

            # self.console.print(indent(item_text, INDENT * 2))
            # self.console.print()

        return None

    @pytest.hookimpl
    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        # if report.nodeid:
        kv_msg = KeyValueMessage("nodeid", "report.nodeid")
        kv_msg(self.console)
        self.console.line()
        table = Table(show_header=False, show_edge=False, show_lines=False)
        table.add_column("name", style="pytest.keyname", width=15)
        table.add_column("value", width=61)

        table.add_row("outcome", f"[{report.outcome}]{report.outcome}[/]")

        def strip_escape(data: bytes) -> bytes:
            """Strip 7-bit and 8-bit C1 ANSI sequences
            https://stackoverflow.com/a/14693789/3253026
            """
            import re
            ansi_escape_8bit = re.compile(
                rb"(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~])"
            )
            return ansi_escape_8bit.sub(b"", data)
        def strip_escape_from_string(text: str) -> str:
            return strip_escape(text.encode("utf-8")).decode("utf-8")

        if report.caplog:
            table.add_row(
                "caplog",
                strip_escape_from_string(report.caplog),
            )

        if report.capstderr:
            table.add_row(
                "capstderr",
                strip_escape_from_string(report.capstderr),
            )

        if report.capstdout:
            width = self.console.width - len("    ") * 3
            stdout_text = "\n".join(
                textwrap.wrap(
                    Text.from_ansi(report.capstdout.strip(), style="none").plain,
                    width=width,
                    initial_indent="    " * 2,
                    subsequent_indent="    " * 2,
                )
            ).strip()
            table.add_row("capstdout", stdout_text)

        padding = Padding(table, (0, 0, 0, 4))
        self.console.print(padding)


    @pytest.hookimpl
    def pytest_itemcollected(self, item: pytest.Item) -> None:
        if self.verbosity < Verbosity.VERBOSE:
            return
        trm = tracer_message("pytest_itemcollected", info=item.nodeid)
        trm(self.console)
        kv_msg = KeyValueMessage( "nodeid", item.nodeid)
        kv_msg(self.console)
        markers = list(item.iter_markers())

        skip_markers = ", ".join(
            [mark.name for mark in markers if mark.name.startswith("skip")]
        )

        xfail_markers = ", ".join(
            [mark.name for mark in markers if mark.name.startswith("xfail")]
        )

        from _pytest.skipping import evaluate_skip_marks, evaluate_xfail_marks
        if skip_markers or xfail_markers:
            self.console.print("markers", style="bright_magenta")
            skipped = evaluate_skip_marks(item)
            if skipped is not None:
                table = Table(
                    show_header=False, show_edge=False, show_lines=False
                )
                table.add_column("name", style="pytest.keyname", width=15)
                table.add_column("value", width=61)

                table.add_row("type", "skip")
                table.add_row("reason", skipped.reason)
                table.add_row("marker", skip_markers)

                padding = Padding(table, (0, 0, 0, 8))
                self.console.print(padding)

            xfailed = evaluate_xfail_marks(item)
            if xfailed is not None:
                table = Table()
                table = Table(
                    show_header=False, show_edge=False, show_lines=False
                )
                table.add_column("name", style="pytest.keyname", width=15)
                table.add_column("value", width=61)

                table.add_row("type", "xfail")
                table.add_row("reason", xfailed.reason)
                if xfailed.raises:
                    table.add_row("raises", str(xfailed.raises))
                table.add_row("run", str(xfailed.run))
                table.add_row("strict", str(xfailed.strict))
                table.add_row("marker", xfail_markers)

                padding = Padding(table, (0, 0, 0, 8))
                self.console.print(padding)


    @pytest.hookimpl(trylast=True)
    def pytest_unconfigure(self) -> None:
        if self.verbosity > Verbosity.NORMAL:
            trm = tracer_message("pytest_unconfigure")
            trm(self.console)
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

        from rich.scope import render_scope

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
    import textwrap
    from rich.highlighter import ReprHighlighter
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
                v = list(map(lambda x: Path(x).resolve().relative_to(config.rootpath).as_posix(), v))
                return Pretty(
                    v,
                    overflow="fold",
                    insert_line=True,
                    highlighter=path_highlighter
                )
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
