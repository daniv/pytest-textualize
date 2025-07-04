from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

import pytest
from pluggy._manager import DistFacade

from pytest_textualize import TextualizePlugins

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Iterator
    from collections.abc import MutableMapping

to_kebab_case = lambda s: s.lower().replace(" ", "_")


class PytestCollectorService:
    name = TextualizePlugins.PYTEST_COLLECTOR_SERVICE

    @pytest.hookimpl(tryfirst=True)
    def pytest_collect_env_info(self, config: pytest.Config) -> dict[str, str]:
        return {
            to_kebab_case("pytest version"): pytest.__version__,
            "rootdir": config.rootpath.as_posix(),
            "configfile": config.inipath.name,
            "invocation_params": shlex.join(config.invocation_params.args),
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"


class PluggyCollectorService:
    name = TextualizePlugins.PLUGGY_COLLECTOR_SERVICE

    def __init__(self) -> None:
        self.config: pytest.Config | None = None
        self.pluginmanager: pytest.PytestPluginManager | None = None

    @pytest.hookimpl
    def pytest_collect_env_info(self, config: pytest.Config) -> dict[str, Any]:
        """
        Following pytest rules on displaying plugins on headers:
            - --debug not set and --trace-config not set -> registered
            - --debug not set and --trace-config was set -> registered + active
            - --debug was set and --trace-config was not set -> registered
            - --debug was set and also --trace-config was set -> registered + active

        :param config: the pytest.Config instance
        :return: a dictionary with pluggy info
        """
        import pluggy

        pluginmanager = config.pluginmanager
        self.pluginmanager = pluginmanager
        self.config = config

        dist_info = self._plugin_distinfo()
        names_info = self._name_plugin()
        return dict(
            plugins=dict(
                pluggy_version=pluggy.__version__,
                dist_title="registered third-party plugins",
                name_title="active plugins",
                dist_info=dist_info if dist_info else None,
                names_info=names_info if names_info else None,
            )
        )

    def _iter_distinfo(self) -> Iterator[tuple[object, DistFacade]]:
        for dist_info in iter(self.pluginmanager.list_plugin_distinfo()):
            yield dist_info

    def _iter_name_plugin(self) -> Generator[tuple[str, object], None, None]:
        for plugin in iter(self.pluginmanager.list_name_plugin()):
            if str(repr(plugin[1])).find("collector-service") > 0:
                continue
            yield plugin

    def _plugin_distinfo(self) -> list[dict[str, str]]:
        from glom import glom
        from pprint import saferepr

        assert self.config is not None
        assert self.pluginmanager is not None

        dists: list[dict[str, str]] = []

        for plugin, facade in self._iter_distinfo():
            location = getattr(plugin, "__file__", saferepr(plugin))
            if Path(location).is_file():
                location = Path(location).relative_to(self.config.rootpath).as_posix()
            dists.append(
                dict(
                    name=facade.name,
                    version=facade.version,
                    project_name=facade.project_name,
                    summary=glom(facade, "metadata.json.summary", default=""),
                    plugin=location,
                )
            )
        return dists

    def _name_plugin(self) -> list[dict[str, str]]:
        assert self.config is not None
        assert self.pluginmanager is not None
        from pprint import saferepr

        # ------------------------------------ if self.value and not (isclass(obj) or callable(obj) or ismodule(obj)):
        names: list[dict[str, str]] = []
        for name, plugin in self._iter_name_plugin():
            if plugin is None:
                continue
            if len(name) > 25:
                if Path(name).is_file():
                    p = Path(name)
                    name = f"{p.parent.name}/{p.name}"

            location = getattr(plugin, "__file__", saferepr(plugin))
            if Path(location).is_file():
                try:
                    location = Path(location).relative_to(self.config.rootpath).as_posix()
                except ValueError as e:
                    location = Path(location).relative_to(Path.home()).as_posix()
                    names.append(dict(name=name, plugin=location))
            else:
                names.append(dict(name=name, plugin=location))

        return names

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"


def sysexec(self, *argv: os.PathLike[str], **popen_opts: Any) -> str:
    """Return stdout text from executing a system child process,
    where the 'self' path points to executable.
    The process is directly invoked and not through a system shell.
    """
    from subprocess import PIPE
    from subprocess import Popen

    popen_opts.pop("stdout", None)
    popen_opts.pop("stderr", None)
    proc = Popen(
        [str(self)] + [str(arg) for arg in argv],
        **popen_opts,
        stdout=PIPE,
        stderr=PIPE,
    )
    stdout: str | bytes
    stdout, stderr = proc.communicate()
    ret = proc.wait()
    if isinstance(stdout, bytes):
        stdout = stdout.decode(sys.getdefaultencoding())
    if ret != 0:
        if isinstance(stderr, bytes):
            stderr = stderr.decode(sys.getdefaultencoding())
        raise RuntimeError(
            ret,
            ret,
            str(self),
            stdout,
            stderr,
        )
    return stdout


class PoetryCollectorService:
    name = TextualizePlugins.POETRY_COLLECTOR_SERVICE

    @pytest.hookimpl(trylast=True)
    def pytest_collect_env_info(self, config: pytest.Config) -> dict[str, Any] | None:
        from pytest_textualize import __version__ as textualize_version

        packages = None
        poetry_version = None
        try:
            cmd = "poetry --version"
            p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, shell=False)
            stdout, _ = p.communicate()
            poetry_version = re.findall(r"\d*\.\d+\.\d+", stdout.decode("utf-8"))[0]
            from pytest_textualize.plugin import settings_key

            settings = config.stash.get(settings_key, None)
            from pytest_textualize import Verbosity

            if config.getoption("--trace-config") or settings.verbosity >= Verbosity.VERY_VERBOSE:
                cmd = "poetry show -T -l"
                p = subprocess.Popen(
                    shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
                )
                stdout, stderr = p.communicate()
                if stdout:
                    packages = self.generate_output(stdout.decode("utf-8").splitlines())
        except subprocess.CalledProcessError as e:
            pass

        data = dict(textualize_version=textualize_version, poetry_version=poetry_version)
        if packages:
            data["packages"] = packages
        return data

    @staticmethod
    def generate_output(lines: list[str]):
        from importlib.metadata import metadata

        packages = []
        packs = tuple(map(lambda x: tuple(filter(len, x.split(" ")))[:3], lines))
        from pydantic_extra_types.semantic_version import SemanticVersion

        for name, current_ver, latest_ver in packs:
            try:
                comp = SemanticVersion.validate_from_str(str(current_ver)).compare(str(latest_ver))
                latest_ver = (
                    f"[poetry.outdated]{latest_ver}[/]"
                    if comp < 0
                    else f"[poetry.actual]{latest_ver}[/]"
                )
                pack = dict(
                    name=name,
                    current_ver=current_ver,
                    latest_ver=latest_ver,
                    summary=metadata(str(name)).json["summary"],
                )
                packages.append(pack)
            except ValueError as error:
                pass

        return packages

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"


class PythonCollectorService:
    name = TextualizePlugins.PYTHON_COLLECTOR_SERVICE

    @pytest.hookimpl(tryfirst=True)
    def pytest_collect_env_info(self, config: pytest.Config) -> dict[str, Any]:
        """Collect version information about the python and visrtual ebvironment used

        :param config: The pytest config
        :return: a dictionary with collected information
        """
        import sys
        import platform

        # -- adding pypy_version_info idf available
        pypy_version_info = getattr(sys, "pypy_version_info", None)
        if pypy_version_info:
            verinfo = ".".join(map(str, pypy_version_info[:3]))
            pypy_kv = f"{verinfo} - {pypy_version_info[3]}"

        # -- adding python executable path
        executable_kv = Path(sys.executable).relative_to(config.rootpath).as_posix()

        return dict(
            platform=f"{sys.platform} - {platform.platform()}",
            python_version=platform.python_version(),
            python_ver_info=".".join(map(str, sys.version_info)),
            pypy_version=locals().get("pypy_kv", None),
            python_executable=Path(sys.executable).relative_to(config.rootpath).as_posix(),
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"


class HookHeaderCollectorService:
    name = TextualizePlugins.HOOKS_COLLECTOR_SERVICE

    @pytest.hookimpl(trylast=True)
    def pytest_collect_env_info(self, config) -> dict[str, Any]:
        data = {}
        lines = config.hook.pytest_report_header(
            config=config, start_path=config.invocation_params.dir
        )
        for line_or_lines in lines:
            if not line_or_lines:
                continue
            if isinstance(line_or_lines, str):
                line_or_lines = [line_or_lines]
            if bool(line_or_lines[0].find("using") >= 0):
                continue
            for line in line_or_lines:
                partition = list(map(str.strip, line.partition(": ")))
                if len(partition) > 3:
                    continue
                match partition[0]:
                    case "plugins" | "rootdir":
                        pass
                    case _:
                        data[partition[0]] = partition[2]
        return data

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"


class CollectorWrapper:
    name = TextualizePlugins.COLLECTOR_WRAPPER

    @pytest.hookimpl(wrapper=True)
    def pytest_collect_env_info(self) -> Generator[None, dict, MutableMapping[str, Any]]:
        from collections import ChainMap

        outcomes = yield

        maps = []
        for outcome in outcomes:
            child = dict(filter(lambda x: x[1] is not None and x[1] != "", outcome.items()))
            maps.append(child)

        return ChainMap(*maps)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"


class HeaderServiceManager:
    names = [
        PytestCollectorService.name,
        PluggyCollectorService.name,
        PoetryCollectorService.name,
        PythonCollectorService.name,
        HookHeaderCollectorService.name,
        CollectorWrapper.name,
    ]

    def setup(self, config: pytest.Config) -> None:
        plugin = config.pluginmanager.getplugin(TextualizePlugins.REGISTRATION_SERVICE)
        plugin.monitored_classes.extend(self.names)

    def call(self, config: pytest.Config):
        collector_wrapper = CollectorWrapper()
        config.pluginmanager.register(collector_wrapper, CollectorWrapper.name)

        python_collector = PythonCollectorService()
        config.pluginmanager.register(python_collector, PythonCollectorService.name)

        pytest_collector = PytestCollectorService()
        config.pluginmanager.register(pytest_collector, PytestCollectorService.name)

        poetry_collector = PoetryCollectorService()
        config.pluginmanager.register(poetry_collector, PoetryCollectorService.name)

        pluggy_collector = PluggyCollectorService()
        config.pluginmanager.register(pluggy_collector, PluggyCollectorService.name)

        hook_collector = HookHeaderCollectorService()
        config.pluginmanager.register(hook_collector, HookHeaderCollectorService.name)

    def teardown(self, config: pytest.Config) -> None:
        for name in self.names:
            plugin = config.pluginmanager.getplugin(name)
            config.pluginmanager.hook.pytest_plugin_unregistered(plugin=plugin)
            config.pluginmanager.unregister(plugin, name)
