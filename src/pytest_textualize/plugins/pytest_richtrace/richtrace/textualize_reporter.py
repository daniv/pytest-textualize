# Project : pytest-textualize
# File Name : textualize_reporter.py
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

import pytest
import rich
import rich.box
import rich.columns
import rich.highlighter
import rich.padding
import rich.panel
import rich.pretty
import rich.style
import rich.table
import rich.text
import rich.theme
import rich.traceback
from typing_extensions import TYPE_CHECKING

from pytest_textualize.settings import Verbosity
from pytest_textualize.textualize.hook_message import HookMessage

if TYPE_CHECKING:
    from typing import MutableMapping
    from rich.console import Console
    from pytest_textualize.plugins import PytestPlugin
    from pytest_textualize import TextualizeSettings
    from rich.console import ConsoleRenderable


class TextualizeReporter:
    name = "pytest-textualize-reporter"

    monitored_classes: ClassVar[list[str]] = []

    def __init__(self, config: pytest.Config):
        self.config = config
        self.console: Console | None = None
        self.settings: TextualizeSettings | None = None
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"

    @property
    def traceconfig(self) -> bool:
        return self.config.option.traceconfig

    @property
    def verbosity(self) -> Verbosity:
        if self.settings is None:
            return Verbosity.QUIET
        return self.settings.verbosity

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

        panel = rich.panel.Panel(
            rich.text.Text(
                "A pytest plugin using Rich for beautiful test result formatting.",  # noqa: E501
                justify="center",
            ),
            box=rich.box.ROUNDED,
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
        if plugin_name is None or self.verbosity < Verbosity.VERBOSE:
            return None

        if self.config.option.traceconfig:
            hm = HookMessage("pytest_plugin_registered", info=plugin_name)
            with self._lock:
                self.console.print(hm)
        else:
            if plugin_name in self.monitored_classes:
                hm = HookMessage("pytest_plugin_registered", info=plugin_name)
                with self._lock:
                    self.console.print(hm)
        return None

    @pytest.hookimpl
    def pytest_report_make_collect_report(self, collector: pytest.Collector) -> None:
        if self.verbosity < Verbosity.VERBOSE:
            return

        if isinstance(collector, pytest.Session):
            info = f"pytest.Session {collector.nodeid}"
        elif isinstance(collector, pytest.Directory):
            info = f"pytest.Directory {collector.nodeid}"
        elif isinstance(collector, pytest.File):
            info = f"pytest.File {collector.nodeid}"
        else:
            raise NotImplementedError
        hm = HookMessage("pytest_make_collect_report", info=info)
        self.console.print(hm)

    @pytest.hookimpl
    def pytest_plugin_unregistered(self, plugin: PytestPlugin) -> None:
        if self.verbosity > Verbosity.NORMAL:
            if hasattr(plugin, "name"):
                hm = HookMessage("pytest_plugin_unregistered", info=getattr(plugin, "name"))
            else:
                hm = HookMessage("pytest_plugin_unregistered", info=saferepr(plugin))
            self.console.print(hm)

    @pytest.hookimpl(trylast=True)
    def pytest_unconfigure(self) -> None:
        if self.verbosity > Verbosity.NORMAL:
            hm = HookMessage("pytest_unconfigure")
            self.console.print(hm)
        self.config.pluginmanager.unregister(self, self.name)

    @pytest.hookimpl
    def pytest_render_header(self, config: pytest.Config, data: MutableMapping[str, Any]) -> bool:
        from collections import ChainMap
        from pytest_textualize.textualize.theme.highlighters import ArgparseArgsHighlighter
        from rich.text import Text

        path_h = rich.traceback.PathHighlighter()
        arg_h = ArgparseArgsHighlighter()

        table = rich.table.Table(
            box=rich.box.HORIZONTALS,
            show_header=False,
            border_style="pytest.table.border",
            expand=True,
        )

        # table = rich.table.Table.grid(padding=1, pad_edge=True)
        table.add_column(width=25, justify="left", style="pytest.keyname", max_width=25)

        words = lambda x: str(x).replace("_", " ")
        title = lambda x: words(x).title()
        getval = lambda x, y: x.get(y, None)

        for key_name in cast(ChainMap, data).fromkeys(
                ["platform", "poetry_version", "pytest_version", "plugins", "packages"]
        ):
            if data.get(key_name) is None:
                continue

            match key_name:

                case "platform":
                    table.add_row(title(key_name), data.get(key_name))
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
                    table.add_row("rootdir", path_h(getval(data, "rootdir")))
                    table.add_row("configfile", path_h(getval(data, "configfile")))
                    if getval(data, "cachedir") is not None:
                        table.add_row("cachedir", path_h(getval(data, "cachedir")))

                    pushed = False
                    try:
                        # from rich_argparse_plus.themes import ARGPARSE_COLOR_THEMES
                        #
                        # theme = rich.theme.Theme(
                        #     ARGPARSE_COLOR_THEMES.get("mother_earth")
                        # )
                        # self.console.push_theme(theme)
                        pushed = True
                        self.console.print(arg_h(rich.text.Text(data.get("invocation_params"))))
                        table.add_row(
                            title("invocation_params"),
                            arg_h(rich.text.Text(data.get("invocation_params"))),
                        )
                    finally:
                        if pushed:
                            pass
                            # self.console.pop_theme()

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

            # match key_name:
            #     case key_name.find("version"):
            #         table.add_row(key_name, repr_h(Path(value).as_posix()))
            #     case "rootdir" | "configfile" | "cachedir":
            #         if key_name == "rootdir":
            #             table.add_section()
            #             table.add_row(key_name, path_h(value.as_posix()))
            #         else:
            #             table.add_row(key_name, repr_h(Path(value).as_posix()))
            #     case "invocation_params":
            #         table.add_row("invocation parameters", f"[pytest.string]{value}[/]")
            #     case "python":
            #         table.add_row("python version", repr_h(value))
            #     case "pytest_ver":
            #         table.add_row("pytest version", repr_h(value))
            #     case "python_ver_info":
            #         table.add_row("python version info", repr_h(value))
            #     case "plugins":
            #         table.add_row("pluggy version", value.get("pluggy_version"))
            #         if value.get("dist_info"):
            #             renderable = render_registered_plugins(
            #                 value.get("dist_title", "registered plugins"),
            #                 value.get("dist_info"),
            #                 self.traceconfig,
            #             )
            #             end_section = False if self.traceconfig else True
            #
            #             col_name = ""
            #             if not self.traceconfig:
            #                 col_name = textwrap.fill(glom(value, "dist_title"), 20)
            #             table.add_row(col_name, renderable, end_section=end_section)
            #         if self.traceconfig:
            #             renderable = render_active_plugins(
            #                 value.get("name_title", "active plugins"), value.get("names_info")
            #             )
            #             table.add_row("", renderable, end_section=True)
            #     case "executable":
            #         if (
            #                 self.verbosity > Verbosity.NORMAL
            #                 or self.config.option.debug
            #                 or getattr(self.config.option, "pastebin", None)
            #         ):
            #             table.add_row(key_name, path_h(value))
            #     case "poetry_version" | "project_version":  # packages
            #         table.add_row(key_name.replace("_", " "), value)
            #     case "packages":
            #         if self.traceconfig:
            #             renderable = render_packages(value)
            #             table.add_row("", renderable)
            #     case _:
            #         table.add_row(key_name, value)

        from rich.scope import render_scope

        table.add_row(
            "",
            render_scope(self.config.inicfg, title="[#4ED7F1]tool.pytest.ini_options[/]"),
            end_section=False,
        )
        table.add_row("", render_options_table(config), end_section=False)
        self.console.print(rich.padding.Padding(table, (0, 0, 0, 2)))
        self.console.line(2)
        return True


def render_registered_plugins(title, dists: list[dict[str, str]], trace: bool) -> ConsoleRenderable:
    ph = rich.traceback.PathHighlighter()

    if trace:
        table = _get_plugins_table(title)
        for d in dists:
            p = Path(d.get("plugin"))
            pack = f"{p.parts[0]}~{p.parent.name}/{p.name}"
            table.add_row(
                f"[pytest.name]{d.get("name")}[/]",
                f"[pytest.version]{d.get("version")}[/]",
                ph(pack),
                d.get("summary"),
            )
        return table

    def get_content(dist_info: dict[str, str]):
        return rich.text.Text.from_markup(
            f"[pytest.name]{dist_info['name']}[/]\n[pytest.version]{dist_info['version']}[/]",
            justify="center",
        )

    plugin_renderables = [rich.panel.Panel(get_content(dist), expand=True) for dist in dists]
    return rich.columns.Columns(plugin_renderables)


def render_active_plugins(title, plugins: list[dict[str, str]]) -> ConsoleRenderable:
    import textwrap

    ph = rich.traceback.PathHighlighter()

    table = _get_plugins_table(title)
    for plugin in plugins:
        p = Path(plugin.get("plugin"))
        if p.is_file():
            path = f"{p.parts[0]}~{p.parent.name}/{p.name}"
            table.add_row(f"[bright_white]{plugin.get("name")}[/]", ph(path))
        else:
            repr_ = textwrap.shorten(saferepr(plugin.get("plugin")), width=110)
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

    table = rich.table.Table(
        box=rich.box.DOUBLE_EDGE,
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
                return rich.pretty.Pretty(
                    v,
                    overflow="fold",
                    insert_line=True,
                    highlighter=rich.traceback.PathHighlighter(),
                )
            else:
                return rich.pretty.Pretty(v, overflow="fold", insert_line=True)
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
    return rich.table.Table(
        show_header=False,
        box=rich.box.SQUARE_DOUBLE_HEAD,
        title_justify="left",
        border_style="pytest.table.border",
        title=title,
        title_style="#4ED7F1",
    )
