from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Sequence

import pytest
from rich import box
from rich.columns import Columns
from rich.console import ConsoleRenderable
from rich.console import Group
from rich.console import render_scope
from rich.markup import escape
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
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


item_stash = pytest.StashKey[Panel]()

class TextualizeReporter(BaseTextualizePlugin):
    name = TextualizePlugins.REPORTER

    def __init__(self):
        self._path_highlighter = PathHighlighter()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"

    @property
    def collect_only(self) -> bool:
        return self.config.option.collectonly

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
        return None

    @pytest.hookimpl
    def pytest_itemcollected(self, item: pytest.Item) -> None:
        if self.verbosity < Verbosity.VERBOSE:
            return None

        node_text = highlighted_nodeid(item)
        hook_msg("pytest_itemcollected", info=node_text, console=self.console, highlight=True)

        markers = list(item.iter_markers())
        skip_markers = ", ".join([mark.name for mark in markers if mark.name.startswith("skip")])
        xfail_markers = ", ".join([mark.name for mark in markers if mark.name.startswith("xfail")])

        from _pytest.skipping import evaluate_skip_marks, evaluate_xfail_marks

        if skip_markers or xfail_markers:
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
    def pytest_report_collectionfinish(self, items: Sequence[pytest.Item]) -> ConsoleRenderable | list[Any] | str | None:
        from pytest_textualize.plugin import collected_groups
        if not self.collect_only and self.verbosity > Verbosity.NORMAL:
            return collected_groups(items=items)
        return None


# if self.verbosity > Verbosity.VERBOSE and hasattr(item, "callspec"):
#
#             table = Table.grid(expand=False)
#             table.add_column(justify="right", style="cyan")
#             table.add_column(justify="right", style="cyan")
#             table.add_row("nodeid", item.nodeid)
#             table.add_row("name", item.name)
#             if hasattr(item, "originalname"):
#                 table.add_row("originalname", item.originalname)
#             import copy
#             deep_copied_dict = copy.deepcopy(item.callspec.__dict__)
#             scope = render_scope(
#                 dict(
#                     params=deep_copied_dict.get("params", {}),
#                     indices=deep_copied_dict.get("indices", {}),
#                     idlist=deep_copied_dict.get("_idlist", {}),
#                     marks=deep_copied_dict.get("marks", {}),
#                 ),
#                 title="callspec",
#                 sort_keys=True,
#             )
#             p = Panel(Group(table, scope))
#             item.stash[item_stash] = p
#
#             r = keyval_msg(
#                 "pytest.Item.callspec",
#                 render_scope(
#                     dict(
#                         params=deep_copied_dict.get("params", {}),
#                         indices=deep_copied_dict.get("indices", {}),
#                         idlist=deep_copied_dict.get("_idlist", {}),
#                         marks=deep_copied_dict.get("marks", {}),
#                     ),
#                     title="callspec",
#                     sort_keys=True,
#                 ),
#                 value_style="scope.fill",
#                 # console=self.console,
#             )
