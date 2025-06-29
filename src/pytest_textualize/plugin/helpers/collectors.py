# Project : pytest-textualize
# File Name : collect_only.py
# Dir Path : src/pytest_textualize/plugins/pytest_richtrace/services
from __future__ import annotations

import inspect
from collections import Counter
from typing import TYPE_CHECKING
from typing import assert_never

import pytest
from rich import box
from rich.columns import Columns
from rich.console import Group
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

if TYPE_CHECKING:
    from rich.console import RenderableType
    from collections.abc import Sequence
    from rich.console import ConsoleRenderable
    from _pytest.nodes import Node


def _format_node(node: Node) -> RenderableType:
    type_name = node.__class__.__name__.lower()
    name_style = "i #BBE9FF"

    match type_name:
        case "dir":
            renderable = Text(f"<Dir: ", style="#FFEEA9").append(node.name, style=name_style).append(">", style="#FFEEA9")
        case "package":
            renderable = Text(f"<Package: ", style="#4CC9FE").append(node.name, style=name_style).append(">", style="#4CC9FE")
        case "module":
            renderable = Text(f"<Module: ", style="#6FE6FC").append(node.name, style=name_style).append(">", style="#6FE6FC")
        case "function":
            renderable = Text(f"<Function: ", style="#4ED7F1").append(node.name, style=name_style).append(">", style="#4ED7F1")
        case _:
            assert_never(type_name)

    obj = getattr(node, "obj", None)
    doc = inspect.getdoc(obj) if obj else None
    if doc:
        table = Table(show_header=False, safe_box=True, show_edge=True, style="#4CC9FE")
        table.add_column("Doc", style="#BBE9FF", no_wrap=True)
        for line in doc.splitlines():
            table.add_row(line)

        return Group(renderable, table)

    return renderable


def collect_only_report(session: pytest.Session) -> ConsoleRenderable:
    test_cases_verbosity = session.config.get_verbosity(pytest.Config.VERBOSITY_TEST_CASES)
    if test_cases_verbosity < 0:
        if test_cases_verbosity < -1:
            return collected_groups(session)
        else:
            return collected_list(session)
    return collected_tree(session)


def collected_tree(session: pytest.Session) -> ConsoleRenderable:
    root = Tree("pytest session", highlight=False, hide_root=True)
    stack: list[Node] = []
    tree_stack: list[Tree] = []
    for item in session.items:
        needed_collectors = item.listchain()[1:]  # strip root node
        while stack:
            if stack == needed_collectors[: len(stack)]:
                break
            stack.pop()
            tree_stack.pop()
        for col in needed_collectors[len(stack):]:
            formatted_node = _format_node(col)
            if len(stack) == 0:
                leaf = root.add(formatted_node, guide_style="#BBE9FF", highlight=False)
                tree_stack.append(leaf)
            else:
                tree_stack.append(tree_stack[-1].add(formatted_node, guide_style="#BBE9FF", highlight=False))
            stack.append(col)
    panel = Panel(
        root, expand=False, box=box.DOUBLE, padding=(1, 2, 1, 4), title="Execution Plan", style="#578FCA", subtitle="collect-only", subtitle_align="left",
    )
    return panel


def collected_list(session: pytest.Session) -> ConsoleRenderable:
    renderables: list[str] = []
    for i, item in enumerate(session.items, start=1):
        renderables.append(f"[#9FB3DF]{i}.[/]{escape(item.name)}")
    return Panel(
        Columns(renderables, column_first=True, expand=True),
        title="[#C5D3E8]Selected items",
        style="#BBE9FF",
        border_style="#4CC9FE",
        box=box.DOUBLE,
        padding=(1, 0, 0, 1),
    )


def collected_groups(session: pytest.Session | None = None, items: Sequence[pytest.Item] | None = None) -> ConsoleRenderable:
    from rich.traceback import PathHighlighter
    path_highlighter = PathHighlighter()
    def get_content(n: str, c: int):
        return path_highlighter(
            Text.from_markup(
            f"[pytest.name]{n}[/]\n[pytest.version]{c}[/]",
            justify="center",
        ))

    if session is not None:
        items = session.items

    counts = Counter(item.nodeid.split("::", 1)[0] for item in items)
    renderables = [Panel(get_content(name, count), expand=False) for name, count in sorted(counts.items())]
    return Panel(
        Columns(renderables, column_first=True, expand=False),
        title="[#EAE4D5]Selected Items by module",
        style="#D29F80",
        border_style="#735557",
        box=box.DOUBLE,
        padding=(1, 0, 0, 1),
    )
