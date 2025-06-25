from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from helpers.manifest import ManifestDirectory

if TYPE_CHECKING:
    from pathlib import Path

pytest_plugins = "pytester"


@pytest.hookimpl(tryfirst=True)
def pytest_cmdline_main(config: pytest.Config) -> pytest.ExitCode | int | None:
    import re
    if not "--strict-markers" in config.invocation_params.args:
        config.known_args_namespace.strict_markers = True
        config.option.strict_markers = True
    if not "--strict-config" in config.invocation_params.args:
        config.known_args_namespace.strict_config = True
        config.option.strict_config = True
    config.known_args_namespace.keepduplicates = False
    return None


@pytest.hookimpl
def pytest_addoption(parser: pytest.Parser, pluginmanager: pytest.PytestPluginManager) -> None:
    group = parser.getgroup("textualize", description="testing pytest-textualize options")
    group.addoption(
        "--no-print",
        action="store_false",
        dest="console_print",
        default=True,
        help="Do not print console outputs during tests.",
    )
    from pytest_textualize.plugin import plugin as textualize_plugin
    pluginmanager.register(textualize_plugin, textualize_plugin.PLUGIN_NAME)



is_hidden_or_pack = lambda s: s.name.startswith(".") or s.name.startswith("_")
is_not_py = lambda s: s.suffix != ".py"

@pytest.hookimpl(trylast=True)
def pytest_ignore_collect(
    collection_path: Path, path, config: pytest.Config
) -> bool | None:

    if collection_path.is_dir() and is_hidden_or_pack(collection_path):
            return True
    if collection_path.is_file():
        if any([is_hidden_or_pack(collection_path), is_not_py(collection_path)]):
            return True
    return None


@pytest.hookimpl
def pytest_collect_directory(path, parent):
    # Use our custom collector for directories containing a `manifest.json` file.
    if path.joinpath("manifest.json").is_file():
        return ManifestDirectory.from_parent(parent=parent, path=path)
    # Otherwise fallback to the standard behavior.
    return None


class TextualizePytester:
    def __init__(self, pytester: pytest.Pytester):
        self.pytester = pytester

    def run_pytest(self, *args, **kwargs) -> pytest.RunResult:
        result = self.pytester.runpytest("--textualize", str(self.pytester.path), *args, **kwargs)
        return result

    def make_pyfile(self, *args, **kwargs) -> Path:
        return self.pytester.makepyfile(*args, **kwargs)

    def make_conftest(self, source: str) -> Path:
        return self.pytester.makeconftest(source)
