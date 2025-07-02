from __future__ import annotations

__all__ = (
    # -- from helpers
    "is_list_of_strings",
    "get_bool_opt",
    "get_int_opt",
    "get_list_opt",
    "literal_to_list",
    "SetEnv",
    "safe_getattr",
    "assert_never",
    # -- from settings
    # from models
    # "TestRunResultsType", "WarningReportType", "PerfTime", "NodeId",
    # -- from this module
    "TextualizePlugins",
    "__version__",
    "TS_BASE_PATH",
    "Verbosity",
    "cleanup_factory",
    "Textualize",
    "ConsoleMessage",
)

from enum import IntEnum
from enum import StrEnum
from importlib import metadata
from pathlib import Path
from typing import Callable
from typing import Final
from typing import TYPE_CHECKING
from typing import assert_never

import pytest

from pytest_textualize._textualize import ConsoleMessage
from pytest_textualize._textualize import Textualize

# ------------------------------------------- From helpers.py ----------------------------------------------------------
from pytest_textualize.helpers import SetEnv
from pytest_textualize.helpers import assert_never
from pytest_textualize.helpers import get_bool_opt
from pytest_textualize.helpers import get_int_opt
from pytest_textualize.helpers import get_list_opt
from pytest_textualize.helpers import is_list_of_strings
from pytest_textualize.helpers import literal_to_list
from pytest_textualize.helpers import safe_getattr

if TYPE_CHECKING:
    from collections.abc import Callable
    from pytest_textualize.typist import PytestPluginType


__version__ = metadata.version("pytest_textualize")
TS_BASE_PATH: Final = Path(__file__).parents[2]

# --- source https://www.compart.com/en/unicode/html


# "inspect.attr": Style(color="yellow", italic=True),
# "inspect.attr.dunder": Style(color="yellow", italic=True, dim=True),
# "inspect.callable": Style(bold=True, color="red"),
# "inspect.async_def": Style(italic=True, color="bright_cyan"),
# "inspect.def": Style(italic=True, color="bright_cyan"),
# "inspect.class": Style(italic=True, color="bright_cyan"),
# "inspect.error": Style(bold=True, color="red"),
# "inspect.equals": Style(),
# "inspect.help": Style(color="cyan"),
# "inspect.doc": Style(dim=True),
# "inspect.value.border": Style(color="green"),

# -- https://www.compart.com/en/unicode
# ----------------------------------------------------------------

# -- Asterisk                                   " * "       \u002a
# -- Middle Dot                                 " · "       \u00b7
# -- Latin Small Letter F with Hook             " ƒ "       \u0192
# -- Dash                                       " ‐ "       \u2010
# -- En Dash                                    " – "       \u2013
# -- Em Dash                                    " — "       \u2014
# -- Horizontal Bar                             " ― "      \u2015
# -- Double Vertical Line                       " ‖ "       \u2016
# -- Bullet                                     " • "       \u2022
# -- Triangle Bullet                            " ‣ "       \u2023
# -- Hyphen Bullet                              " ⁃ "       \u2043
# -- Leftwards Arrow                            " ← "       \u2190
# -- Rightwards Arrow                           " → "       \u2192
# -- Left Right Arrow                           " ↔ "       \u2194
# -- Rightwards-Two Headed Arrow                " ↠ "       \u21a0
# -- Rightwards Arrow with Tail                 " ↣ "       \u21a3
# -- Rightwards Arrow from Bar                  " ↦ "       \u21a6
# -- Leftwards Bar Over Rightwards Arrow 2 Bar  " ↹ "       \u21b9
# -- Rightwards Arrow Over Leftwards Arrow      " ⇄ "       \u21c4
# -- Leftwards Arrow Over Rightwards Arrow      " ⇆ "       \u21c6
# -- Leftwards Paired Arrows                    " ⇇ "       \u21c7
# -- Rightwards Paired Arrows                   " ⇉ "       \u21c9
# -- Rightwards Arrow to Bar                    " ⇥ "       \u21e5
# -- Three Rightwards Arrows                    " ⇶ "       \u21f6
# -- Left Right Arrow w/Vertical Stroke         " ⇹ "       \u21f9
# -- Divides                                    " ∣ "       \u2223
# -- Parallel To                                " ∥ "       \u2225
# -- Proportion                                 " ∷ "       \u2237
# -- Square Root                                " √ "       \u221a
# -- Much Greater-Than                          " ≫ "       \u226b
# -- Box Drawings Light Vertical                " │ "       \u2502
# -- Box Drawings Double Horizontal             " ═ "       \u2550
# -- Box Drawings Double Vertical               " ║ "       \u2551
# -- B Diamond                                  " ◆ "       \u25c6
# -- B Small Square                             " ▪ "       \u25aa
# -- B Right-Pointing Small Triangle            " ▸ "       \u25b8
# -- B Left-Pointing Small Triangle             " ◂ "       \u25c2
# -- B Circle                                   " ● "       \u25cf
# -- B Star                                     " ★ "       \u2605
# -- B Diamond Suit                             " ♦ "       \u2666
# -- Digram For Greater Yang                    " ⚌ "       \u268c
# -- Check Mark                                 " ✓ "       \u2713  ◼◼◼◼ ggg ◼◼◼◼ 25FC
# -- Ballot X                                   " ✗ "       \u2717  ▮▮▮▮ ggg ▮▮▮▮ 25AE
# -- Maltese Cross                              " ✠ "       \u2720
# -- Six Pointed B Star                         " ✶ "       \u2736
# -- B Diamond Minus White X                    " ❖ "       \u2756
# -- Heavy Wide-Headed Rightwards Arrow         " ➔ "       \u2794
# -- Left and Right Double Turnstile            " ⟚ "      \u27da
# -- Long Rightwards Arrow                      " ⟶ "       \u27f6
# -- Rightwards Two-Headed Arrow w/Tail         " ⤖ "       \u2916
# -- N-Ary Circled Times Operator               " ⨂ "       \u2a02
# -- B Medium Diamond                           " ⬥ "       \u2b25
# -- Leftwards Triangle-Headed Paired Arrows    " ⮄ "       \u2b84
# -- Rightwards Triangle-Headed Paired Arrows   " ⮆ "       \u2b86
# -- B Square Centred                           " ⯀ "       \u2bc0
# -- B Diamond Centred                          " ⯁ "       \u2bc1
# -- Rightwards TH Arrow w/Double Vert. Stroke  " ⭼ "       \u2b7c
# -- Medium Right-Pointing Triangle Centred     " ⯈ "       \u2bc8

_HOOK_PREFIX = "\u25aa"


# -- "⟥⟥⟥⟥⟥⟥—*—⟤⟤⟤⟤⟤"


class TextualizePlugins(StrEnum):
    PLUGIN = "pytest-textualize-plugin"
    TRACER = "textualize-tracer"
    ERROR_TRACER = "textualize-error-tracer"
    COLLECTOR_TRACER = "textualize-collector-tracer"
    RUNTEST_TRACER = "textualize-runtest-tracer"
    REGISTRATION_SERVICE = "textualize-registration-service"
    PLUGGY_COLLECTOR_SERVICE = "pluggy-collector-service"
    PYTEST_COLLECTOR_SERVICE = "pytest-collector-service"
    POETRY_COLLECTOR_SERVICE = "poetry-collector-service"
    PYTHON_COLLECTOR_SERVICE = "python-collector-service"
    HOOKS_COLLECTOR_SERVICE = "hooks-collector-service"
    COLLECTOR_WRAPPER = "collector-wrapper"
    SUMMARY_SERVICE = "summary-service"


class Verbosity(IntEnum):
    QUIET = -1  # --quiet
    NORMAL = 0
    VERBOSE = 1  # -v
    VERY_VERBOSE = 2  # -vv
    DEBUG = 3  # -vvv


def cleanup_factory(
    pluginmanager: pytest.PytestPluginManager, plugin_: PytestPluginType
) -> Callable[[], None]:
    def clean_up() -> None:
        name = pluginmanager.get_name(plugin_)
        # todo: log message
        pluginmanager.unregister(name=name)
        pluginmanager.hook.pytest_plugin_unregistered(plugin=plugin_)

    return clean_up


# def custom_exception_handler(exc_type, exc_value, exc_traceback):
#     print(f"An unhandled error occurred: {exc_type.__name__}: {exc_value}")
#     # You could also log this to a file, send an email, etc.
#     # For example, to print the full traceback:
#     # import traceback
#     # traceback.print_exception(exc_type, exc_value, exc_traceback)
#
# # Assign your custom handler to sys.excepthook
# sys.excepthook = custom_exception_handler
