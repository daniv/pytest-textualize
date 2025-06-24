from __future__ import annotations

import pytest
from rich import box
from rich.columns import Columns
from rich.console import render_scope
from rich.markup import escape
from rich.padding import Padding
from rich.panel import Panel
from rich.text import Text
from rich.traceback import PathHighlighter
from typing_extensions import assert_never

from pytest_textualize import TextualizePlugins
from pytest_textualize import highlighted_nodeid
from pytest_textualize import hook_msg
from pytest_textualize import key_value_scope
from pytest_textualize import keyval_msg
from pytest_textualize.plugin.base import BaseTextualizePlugin
from pytest_textualize.settings import Verbosity


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
